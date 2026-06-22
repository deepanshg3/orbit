import json
import re
import time
import random
from google import genai
from google.genai import types 
from configs.settings import settings
from core.utils.schema import RankedTrend

# --- NEW IMPORT ---
from core.monitoring.tracing import trace_gemini_call
from core.trend_engine.prompt import build_ranker_system_prompt, build_ranker_user_message 

class LLMRanker:
    """
    Uses Gemini (new SDK) to rank trends and traces decisions via LangSmith.
    """

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract_json(self, text):
        # We keep this as a safety net, even though JSON mode usually strips the markdown
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

        # 1. Build the two separate pieces dynamically
        system_instruction = build_ranker_system_prompt(settings.USER_PROFILE, playbook)
        user_message = build_ranker_user_message(trends)

        valid_ids = [t["id"] for t in trends]
        failure_count = 0

        for attempt in range(max_retries):
            try:
                self.logger.info(f"[LLM] Attempt {attempt + 1}")
                start_time = time.time()

                # --- LANGSMITH WRAPPER START ---
                tags = ["trend_ranking", "hacker_news"]
                meta = {
                    "attempt": attempt + 1,
                    "total_raw_trends_provided": len(trends),
                    "playbook_guided": bool(playbook)
                }
                inputs_payload = {
                    "system_instruction": system_instruction,
                    "prompt_payload": user_message
                }

                with trace_gemini_call(name="Orbit Trend Ranking", inputs=inputs_payload, tags=tags, metadata=meta) as trace:
                    
                    # 2. The Modern SDK Call (Separated System vs Content)
                    response = self.client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=user_message,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json", 
                        )
                    )

                    # Extract tokens directly into our LangSmith state
                    trace.extract_usage(response)

                    latency = time.time() - start_time
                    self.logger.info(f"[LLM] Latency: {latency:.2f}s")

                    raw_output = response.text
                    
                    # Log raw string immediately prior to local script parsing
                    trace.outputs = {"raw_generated_ranking": raw_output}

                    self.logger.info(f"[LLM] Prompt Tokens: {trace.prompt_tokens}")
                    self.logger.info(f"[LLM] Completion Tokens: {trace.completion_tokens}")
                    self.logger.info(f"[LLM] Total Tokens: {trace.total_tokens}")

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

                    # Save cleanly structured dictionary outputs to LangSmith for easier reading
                    trace.outputs["validated_ranked_trends"] = [t.model_dump() for t in validated_output]

                    return validated_output
                # --- LANGSMITH WRAPPER END ---

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
                    if execution_failed := True:
                        # Let the context manager log the traceback and throw the exception forward
                        raise e
                    
        return None