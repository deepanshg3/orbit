from google import genai
from configs.settings import settings
from core.utils.schema import GeneratedContent
import json
import re
import time
import random

class ContentGenerator:

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def build_prompt(self, trend, content_type):
        return f"""
You are an expert AI content strategist and engineer.

Your job is to convert a trending topic into a HIGH-VALUE technical content piece.

--------------------------------------------------

INPUT:

Title:
{trend.title}

Context:
{trend.reason}

Content Type:
{content_type}

--------------------------------------------------

GOAL:

Create content that:
- Builds authority
- Teaches something useful
- Provides insight (NOT news summary)
- Have human touch

--------------------------------------------------

FORMAT RULES (VERY IMPORTANT):

IF content_type = "short":
- Write ONLY 2–3 lines
- Max 250 characters strictly
- No explanation, only punchy insight

IF content_type = "medium":
- Write a SINGLE post under 450 characters strictly
- Include insight but keep concise

IF content_type = "thread":
- Write structured multi-part content
- Include breakdown, insights, and depth
- Each part (chunk) must be strictly under 450 char

IMPORTANT:
- DO NOT include numbering like "1/", "2/" for thread content
- Return clean content only in chunks
- Numbering will be handled by the system


--------------------------------------------------

CONTENT REQUIREMENTS:

1. MUST NOT rewrite the news
2. MUST extract a UNIQUE angle
3. MUST provide technical or strategic insight
4. MUST be useful for developers / AI builders
5. Have a human tone

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

    def generate(self, trend, content_type, max_retries=3):

        self.logger.info("[CONTENT] Generating content")

        prompt = self.build_prompt(trend, content_type)

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

                # Inject content_type (source of truth)
                parsed["content_type"] = content_type

                # -------------------------------
                # Content Metrics Logging
                # -------------------------------
                content_data = parsed.get("content", "")
                hook_data = parsed.get("hook", "")
                takeaway_data = parsed.get("takeaway", "")

                self.logger.info(f"[CONTENT] Type: {content_type}")

                # --- Hook ---
                hook_len = len(hook_data)
                self.logger.info(f"[CONTENT] Hook Length: {hook_len} chars")

                # --- Takeaway ---
                takeaway_len = len(takeaway_data)
                self.logger.info(f"[CONTENT] Takeaway Length: {takeaway_len} chars")

                # --- Content ---
                if isinstance(content_data, list):
                    chunk_count = len(content_data)
                    total_chars = sum(len(chunk) for chunk in content_data)

                    self.logger.info(f"[CONTENT] Content Chunks: {chunk_count}")
                    self.logger.info(f"[CONTENT] Total Content Length: {total_chars} chars")
                    total_full_length = hook_len + total_chars + takeaway_len
                    self.logger.info(f"[CONTENT] Full Post Length (hook+content+takeaway): {total_full_length} chars")

                    # Per-chunk validation logging
                    for i, chunk in enumerate(content_data):
                        chunk_len = len(chunk)

                        self.logger.debug(f"[CONTENT] Chunk {i+1}: {chunk_len} chars")

                        if chunk_len > 450:
                            self.logger.warning(
                                f"[CONTENT WARNING] Chunk {i+1} exceeds 450 chars ({chunk_len})"
                            )

                else:
                    content_len = len(content_data)
                    self.logger.info(f"[CONTENT] Content Length: {content_len} chars")

                    if content_type == "short" and content_len > 250:
                        self.logger.warning("[CONTENT WARNING] Short content exceeded 250 chars")

                    if content_type == "medium" and content_len > 450:
                        self.logger.warning("[CONTENT WARNING] Medium content exceeded 450 chars")

                validated = GeneratedContent(**parsed)

                self.logger.info("[CONTENT] Content generated successfully")

                return validated

            except Exception as e:
                error_msg = str(e)
                
                # 1. Check if it's the specific Gemini 503 Overload Error
                if "503" in error_msg or "high demand" in error_msg.lower():
                    if attempt == max_retries - 1:
                        self.logger.error(f"[CONTENT ERROR] All attempts failed. Server overloaded: {error_msg}")
                        return None
                    
                    # Calculate exponential backoff: 5s, 10s, 20s + jitter
                    base_delay = 5
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 2)
                    
                    self.logger.warning(f"[CONTENT WARNING] 503 Overload. Waiting {sleep_time:.1f}s before attempt {attempt + 2}...")
                    time.sleep(sleep_time)
                
                # 2. If it's a different error (like a JSON formatting glitch), do a standard retry
                else:
                    self.logger.warning(f"[CONTENT ERROR] Attempt {attempt+1} failed: {error_msg}")
                    
                    if attempt == max_retries - 1:
                        self.logger.error("[CONTENT ERROR] All normal attempts failed.")
                        return None
                    
                    time.sleep(2) # Short 2-second breather for standard errors

        