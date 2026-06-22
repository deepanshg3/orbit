import json
import re
import time
import random
from google import genai
from google.genai import types 
from configs.settings import settings
from core.utils.schema import GeneratedContent

# --- NEW IMPORT ---
from core.monitoring.tracing import trace_gemini_call
from core.content_engine.prompt import build_content_system_prompt, build_content_user_message

class ContentGenerator:

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract_json(self, text):
        # We keep this as a safety net, even though JSON mode usually strips the markdown
        text = re.sub(r"```json|```", "", text).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    def generate(self, trend, content_type, playbook=None, max_retries=3):
        """
        Generates the content using the dynamic prompt builder and logs to LangSmith.
        """
        self.logger.info("[CONTENT] Generating content")

        system_instruction = build_content_system_prompt(playbook)
        user_message = build_content_user_message(trend.title, trend.reason, content_type)

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # --- LANGSMITH WRAPPER START ---
                # We define the taxonomy tags and the critical metadata 
                # so you can filter these traces in the LangSmith UI.
                tags = ["content_generation", "daily_post", content_type]
                meta = {
                    "trend_title": trend.title,
                    "trend_reason": trend.reason,
                    "content_type": content_type,
                    "attempt": attempt + 1,
                    # We log the raw playbook dict so you know exactly which rules were active
                    "playbook_rules": playbook if playbook else "default_fallback"
                }

                # We pass the full prompt structure to LangSmith's 'inputs'
                inputs_payload = {
                    "system_instruction": system_instruction,
                    "user_message": user_message
                }

                with trace_gemini_call(name="Orbit Content Generation", inputs=inputs_payload, tags=tags, metadata=meta) as trace:
                    
                    # 1. The Modern SDK Call (Inside the trace)
                    response = self.client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=user_message,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json", 
                        )
                    )
                    
                    # 2. Extract token usage and attach to LangSmith state
                    trace.extract_usage(response)
                    
                    # Replicate your local terminal logging
                    self.logger.info(f"[CONTENT] Prompt Tokens: {trace.prompt_tokens}")
                    self.logger.info(f"[CONTENT] Completion Tokens: {trace.completion_tokens}")
                    self.logger.info(f"[CONTENT] Total Tokens: {trace.total_tokens}")
                    
                    latency = time.time() - start_time
                    self.logger.info(f"[CONTENT] Latency: {latency:.2f}s")
                    
                    raw_output = response.text
                    
                    # 3. Log the raw output string back to LangSmith BEFORE we try to parse it
                    # This ensures if the JSON parser crashes, you still see what Gemini said!
                    trace.outputs = {"raw_generated_text": raw_output}
                    
                    self.logger.debug(f"[CONTENT] Raw response length: {len(raw_output)}")

                    # JSON Parsing & Validation
                    cleaned = self.extract_json(raw_output)
                    parsed = json.loads(cleaned)
                    parsed["content_type"] = content_type

                    # Logging Local Metrics
                    content_data = parsed.get("content", "")
                    hook_data = parsed.get("hook", "")
                    takeaway_data = parsed.get("takeaway", "")

                    self.logger.info(f"[CONTENT] Type: {content_type}")
                    hook_len = len(hook_data)
                    self.logger.info(f"[CONTENT] Hook Length: {hook_len} chars")
                    takeaway_len = len(takeaway_data)
                    self.logger.info(f"[CONTENT] Takeaway Length: {takeaway_len} chars")

                    if isinstance(content_data, list):
                        chunk_count = len(content_data)
                        total_chars = sum(len(chunk) for chunk in content_data)

                        self.logger.info(f"[CONTENT] Content Chunks: {chunk_count}")
                        self.logger.info(f"[CONTENT] Total Content Length: {total_chars} chars")
                        total_full_length = hook_len + total_chars + takeaway_len
                        self.logger.info(f"[CONTENT] Full Post Length (hook+content+takeaway): {total_full_length} chars")

                        for i, chunk in enumerate(content_data):
                            chunk_len = len(chunk)
                            self.logger.debug(f"[CONTENT] Chunk {i+1}: {chunk_len} chars")
                            if chunk_len > 450:
                                self.logger.warning(f"[CONTENT WARNING] Chunk {i+1} exceeds 450 chars ({chunk_len})")
                    else:
                        content_len = len(content_data)
                        self.logger.info(f"[CONTENT] Content Length: {content_len} chars")
                        if content_type == "short" and content_len > 250:
                            self.logger.warning("[CONTENT WARNING] Short content exceeded 250 chars")
                        if content_type == "medium" and content_len > 450:
                            self.logger.warning("[CONTENT WARNING] Medium content exceeded 450 chars")

                    validated = GeneratedContent(**parsed)
                    
                    # 4. Attach the final validated object to LangSmith so you can see the cleanly parsed JSON
                    trace.outputs["validated_json"] = parsed
                    
                    self.logger.info("[CONTENT] Content generated successfully based on current playbook")

                    return validated
                # --- LANGSMITH WRAPPER END ---

            except Exception as e:
                error_msg = str(e)
                
                # 503 Overload handling
                if "503" in error_msg or "high demand" in error_msg.lower():
                    if attempt == max_retries - 1:
                        self.logger.error(f"[CONTENT ERROR] All attempts failed. Server overloaded: {error_msg}")
                        return None
                    
                    base_delay = 5
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 2)
                    self.logger.warning(f"[CONTENT WARNING] 503 Overload. Waiting {sleep_time:.1f}s before attempt {attempt + 2}...")
                    time.sleep(sleep_time)
                
                # Standard error handling
                else:
                    self.logger.warning(f"[CONTENT ERROR] Attempt {attempt+1} failed: {error_msg}")
                    if attempt == max_retries - 1:
                        self.logger.error("[CONTENT ERROR] All normal attempts failed.")
                        return None
                    
                    time.sleep(2)