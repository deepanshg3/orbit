from google import genai
from configs.settings import settings
from core.utils.schema import RankedTrend
import json
import re
import time


class LLMRanker:
    """
    Uses Gemini (new SDK) to rank trends.
    """

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def build_prompt(self, trends):
        profile = settings.USER_PROFILE

        trends_text = "\n".join(
            [f"{t['id']}. {t['title']}" for t in trends]
        )

        prompt = f"""
                    You are a strict ranking system. You must ONLY select from the given trends.

                    USER PROFILE:
                    - Niche: {profile["niche"]}
                    - Audience: {profile["audience"]}
                    - Goal: {profile["goal"]}
                    - Style: {profile["content_style"]}
                    - Tone: {profile["tone"]}

                    RULES (MANDATORY):
                    - Use ONLY given trends
                    - DO NOT modify titles
                    - Return EXACT titles
                    - All IDs must exist in input

                    TASK:

                    1. Score ALL trends (1–10)
                    Based on:
                    - relevance
                    - engagement potential
                    - usefulness

                    2. ALSO decide content_type for each trend, decide based upon how much attention it needs:

                    Choose ONE:
                    - "short" → for quick news, announcements, simple ideas (under 200 chars)
                    - "medium" → for moderate insights (under 400 chars)
                    - "thread" → for deep insights, technical topics, case studies (multi-post)

                    Guidelines:
                    - Complex / high-value insights → thread
                    - Breaking news / simple updates → short
                    - Balanced topics → medium

                    3. Scoring rules:
                    - Use full range (1–10)
                    - Make sure scores are unique,score them in decimal between 1-10 like 9.8, 9.4, 7.9 
                    - Scores must be relative
                    - Lower ID = higher virality (use as signal, not rule)
                    - Clearly differentiate top vs average vs weak

                    4. Select TOP 5 after scoring

                    OUTPUT:
                    Return ONLY TOP 5 items.

                    [
                    {{
                        "id": number,
                        "title": "exact title",
                        "score": number,
                        "content_type": "short | medium | thread",
                        "reason": "short explanation"
                    }}
                    ]

                    TRENDS:
                    {trends_text}
                    """
        return prompt

    def extract_json(self, text):
        text = re.sub(r"```json|```", "", text).strip()

        match = re.search(r"\[.*\]", text, re.DOTALL)

        if match:
            return match.group(0)

        return text

    def rank(self, trends, max_retries=3):
        self.logger.info("[LLM] Ranking trends using Gemini")

        prompt = self.build_prompt(trends)

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

                self.logger.info(f"[LLM] Success on attempt {attempt + 1}")

                # Optional: enforce correct ordering if LLM messes up
                validated_output.sort(key=lambda x: x.score, reverse=True)

                return validated_output

            except Exception as e:
                failure_count += 1
                self.logger.warning(
                    f"[LLM ERROR] Attempt {attempt + 1} failed | {str(e)}"
                )

        self.logger.error(f"[LLM ERROR] All attempts failed | Total failures: {failure_count}")
        return None