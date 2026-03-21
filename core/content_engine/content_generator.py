from google import genai
from configs.settings import settings
from core.utils.schema import GeneratedContent
import json
import re
import time


class ContentGenerator:

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def build_prompt(self, trend):
        return f"""
You are an expert AI content strategist and engineer.

Your job is to convert a trending topic into a HIGH-VALUE technical content piece.

--------------------------------------------------

INPUT:

Title:
{trend.title}

Context:
{trend.reason}

--------------------------------------------------

GOAL:

Create content that:
- Builds authority
- Teaches something useful
- Provides insight (NOT news summary)

--------------------------------------------------

CONTENT REQUIREMENTS:

1. MUST NOT rewrite the news
2. MUST extract a UNIQUE angle
3. MUST provide technical or strategic insight
4. MUST be useful for developers / AI builders

--------------------------------------------------

STRUCTURE:

Return JSON with:

{{
  "angle": "unique perspective in one line",
  "hook": "scroll-stopping opening line",
  "content": "main content (clear, structured, insightful)",
  "takeaway": "practical lesson or conclusion"
}}

--------------------------------------------------

WRITING RULES:

- Avoid fluff
- Avoid generic statements
- Prefer clarity over hype
- Sound like an expert, not a journalist
- Keep it concise but dense

--------------------------------------------------

OUTPUT:
STRICT JSON ONLY
"""

    def extract_json(self, text):
        text = re.sub(r"```json|```", "", text).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    def generate(self, trend, max_retries=3):

        self.logger.info("[CONTENT] Generating content")

        prompt = self.build_prompt(trend)

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                
                # ✅ Detailed, Safe Token usage tracking
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    input_tokens = getattr(usage, "prompt_token_count", 0)
                    output_tokens = getattr(usage, "candidates_token_count", 0)
                    total_tokens = getattr(usage, "total_token_count", 0)
                
                    self.logger.info(f"[CONTENT] Prompt Tokens: {input_tokens}")
                    self.logger.info(f"[CONTENT] Completion Tokens: {output_tokens}")
                    self.logger.info(f"[CONTENT] Total Tokens: {total_tokens}")
                
                # Latency time
                latency = time.time() - start_time
                self.logger.info(f"[CONTENT] Latency: {latency:.2f}s")
                
                # Raw response processing
                raw_output = response.text
                self.logger.debug(f"[CONTENT] Raw response length: {len(raw_output)}")

                cleaned = self.extract_json(raw_output)
                parsed = json.loads(cleaned)

                validated = GeneratedContent(**parsed)

                self.logger.info("[CONTENT] Content generated successfully")

                return validated

            except Exception as e:
                self.logger.warning(
                    f"[CONTENT ERROR] Attempt {attempt+1} failed: {str(e)}"
                )

        self.logger.error("[CONTENT ERROR] All attempts failed")
        return None

        