import json
import time
from google import genai
from google.genai import types
from configs.settings import settings
from core.utils.logger import get_logger

logger = get_logger("orbit.inbound.community_manager")

class CommunityManager:
    def __init__(self):
        """
        Initializes the Community Manager with the modern Gemini API client.
        """
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.logger = logger  # <--- CRITICAL FIX: The missing logger!

    def _build_system_instruction(self) -> str:
        return (
            "You are Orbit, an autonomous AI Engineering agent managed by a tech-builder. "
            "Your persona is technical, direct, highly insightful, and subtly witty. "
            "Avoid typical corporate AI fluff like 'Hey there tech enthusiast!' or 'Oh, that is a great question!'. "
            "Speak like a senior engineer who values optimization, clean design, and hardware-level performance. "
            "Keep answers concise (under 250 characters) to fit social media constraints perfectly. "
            "Acknowledge the specific technical nuances brought up in the user's comment."
        )

    def generate_replies(self, unanswered_queue: list) -> list:
        if not unanswered_queue:
            self.logger.info("[COMMUNITY MANAGER] Queue is empty. No replies to generate.")
            return []

        self.logger.info(f"[COMMUNITY MANAGER] Compiling responses for {len(unanswered_queue)} comments in batch...")

        prompt = (
            "Analyze the parent post context and the corresponding user comments below. "
            "Generate an authentic, tailored response for each user comment following your core persona.\n\n"
            "CRITICAL: Your output MUST be a valid JSON array of objects, and nothing else. "
            "Do not wrap the response in markdown blocks (like ```json). "
            "Each object inside the array must contain exactly these keys:\n"
            "- 'comment_id': (string matching the input)\n"
            "- 'username': (string matching the input)\n"
            "- 'reply_text': (your custom generated reply string)\n\n"
            "--- START OF INPUT QUEUE ---\n"
        )

        for idx, item in enumerate(unanswered_queue):
            prompt += (
                f"\n[Item {idx+1}]\n"
                f"Comment ID: {item['comment_id']}\n"
                f"Username: {item['username']}\n"
                f"User Comment: {item['text']}\n"
                f"Parent Thread Hook: {item['context']['hook']}\n"
                f"Parent Thread Takeaway: {item['context']['takeaway']}\n"
                "---"
            )

        max_retries = 3
        base_delay = 2 

        for attempt in range(max_retries):
            try:
                self.logger.debug(f"[COMMUNITY MANAGER] LLM Generation Attempt {attempt + 1}/{max_retries}...")
                
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self._build_system_instruction(),
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )

                raw_text = response.text.replace("```json", "").replace("```", "").strip()
                generated_batch = json.loads(raw_text)

                validated_replies = []
                
                for reply in generated_batch:
                    comment_id = reply.get("comment_id")
                    original_item = next((i for i in unanswered_queue if i["comment_id"] == comment_id), None)
                    
                    if original_item:
                        validated_replies.append({
                            "post_id": original_item["post_id"],
                            "comment_id": comment_id,
                            "username": reply.get("username"),
                            "reply_text": reply.get("reply_text")
                        })

                self.logger.info(f"[COMMUNITY MANAGER] Successfully generated {len(validated_replies)} valid replies.")
                return validated_replies

            except json.JSONDecodeError as je:
                self.logger.error(f"[COMMUNITY MANAGER ERROR] LLM failed to output pure JSON string: {je}")
                return []
            
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "429" in error_msg:
                    if attempt < max_retries - 1:
                        sleep_time = base_delay * (2 ** attempt) 
                        self.logger.warning(f"[COMMUNITY MANAGER] API Overloaded. Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                        continue 
                    else:
                        self.logger.error(f"[COMMUNITY MANAGER] Max retries reached. API is completely down: {e}")
                        return []
                else:
                    self.logger.error(f"[COMMUNITY MANAGER ERROR] Unhandled Exception: {e}")
                    return []
                    
        return []