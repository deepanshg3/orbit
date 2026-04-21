from google import genai
from configs.settings import settings
from core.utils.schema import RankedTrend
from core.trend_engine.prompt import build_ranker_prompt
import json
import re
import time
import random

class LLMRanker:
    """
    Uses Gemini (new SDK) to rank trends.
    """

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract_json(self, text):
        text = re.sub(r"```json|```", "", text).strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return match.group(0)
        return text

    def rank(self, trends, playbook=None, max_retries=3):
        """
        Ranks the trends. Now accepts an optional playbook to drive scoring.
        """
        self.logger.info("[LLM] Ranking trends using Gemini")

        # Dynamically build the prompt using our external file and settings
        prompt = build_ranker_prompt(trends, settings.USER_PROFILE, playbook)

        valid_ids = [t["id"] for t in trends]
        failure_count = 0

        for attempt in range(max_retries):
            try:
                self.logger.info(f"[LLM] Attempt {attempt + 1}")
                start_time = time.time()

                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )

                latency = time.time() - start_time
                self.logger.info(f"[LLM] Latency: {latency:.2f}s")

                raw_output = response.text

                # Token Sizes
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    input_tokens = getattr(usage, "prompt_token_count", 0)
                    output_tokens = getattr(usage, "candidates_token_count", 0)
                    total_tokens = getattr(usage, "total_token_count", 0)
                
                    self.logger.info(f"[LLM] Prompt Tokens: {input_tokens}")
                    self.logger.info(f"[LLM] Completion Tokens: {output_tokens}")
                    self.logger.info(f"[LLM] Total Tokens: {total_tokens}")

                self.logger.debug(f"[LLM] Raw response length: {len(raw_output)} chars")

                cleaned_output = self.extract_json(raw_output)
                self.logger.debug("[LLM] JSON extracted")

                parsed_output = json.loads(cleaned_output)

                # Structural validation
                if not isinstance(parsed_output, list):
                    raise ValueError("Output is not a list")

                if len(parsed_output) != 5:
                    raise ValueError("LLM did not return exactly top 5 trends")

                validated_output = []
                for item in parsed_output:
                    # Field validation
                    if not all(k in item for k in ["id", "title", "score", "reason", "content_type"]):
                        raise ValueError("Missing required fields")

                    # ID validation
                    if item["id"] not in valid_ids:
                        raise ValueError(f"Invalid ID returned: {item['id']}")

                    # Pydantic validation
                    validated = RankedTrend(**item)
                    validated_output.append(validated)

                self.logger.info(f"[LLM] Success on attempt {attempt + 1} (Playbook guided: {bool(playbook)})")

                # Optional: enforce correct ordering if LLM messes up
                validated_output.sort(key=lambda x: x.score, reverse=True)

                return validated_output

            except Exception as e:
                failure_count += 1
                error_msg = str(e)
                
                # 503 Overload handling
                if "503" in error_msg or "high demand" in error_msg.lower():
                    if attempt == max_retries - 1:
                        self.logger.error(f"[LLM ERROR] All attempts failed. Server overloaded: {error_msg} | Total failures: {failure_count}")
                        return None
                    
                    base_delay = 5
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 2)
                    self.logger.warning(f"[LLM WARNING] 503 Overload. Waiting {sleep_time:.1f}s before attempt {attempt + 2}...")
                    time.sleep(sleep_time)
                
                # Standard error handling
                else:
                    self.logger.warning(f"[LLM ERROR] Attempt {attempt+1} failed: {error_msg}")
                    if attempt == max_retries - 1:
                        self.logger.error(f"[LLM ERROR] All normal attempts failed | Total failures: {failure_count}")
                        return None
                    
                    time.sleep(2)
                    
        return None