import json
import time
from google import genai
from google.genai import types
from core.utils.logger import get_logger
from core.utils.schema import StrategyPlaybookSchema
from core.strategy_engine.prompts import STRATEGY_SYSTEM_PROMPT
from configs.settings import settings 

logger = get_logger("orbit.strategy_analyzer")

class StrategyAnalyzer:
    def __init__(self):
        try:
            # 1. Initialize Gemini with the NEW SDK syntax
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("[ANALYZER] Gemini 2.5 Flash initialized successfully (Modern SDK).")
        except Exception as e:
            logger.error(f"[ANALYZER] Failed to initialize Gemini API: {str(e)}")
            raise

    def generate_playbook(self, top_posts_text: str, bottom_posts_text: str) -> dict:
        """
        Sends the post data to Gemini, enforces the Pydantic schema, 
        and handles API rate limits using Exponential Backoff.
        """
        logger.info("[ANALYZER] Constructing payload for Gemini...")

        user_message = (
            f"=== TOP 5 POSTS (WINNERS) ===\n{top_posts_text}\n\n"
            f"=== BOTTOM 5 POSTS (LOSERS) ===\n{bottom_posts_text}\n\n"
            "Analyze these posts and return the strict JSON playbook."
        )

        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"[ANALYZER] Calling API (Attempt {attempt + 1}/{max_retries})...")
                
                # The New SDK call structure
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=STRATEGY_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                    )
                )
                
                raw_json_string = response.text

                # Parse the raw string into a Python dictionary
                playbook_dict = json.loads(raw_json_string)

                # Validate against the Pydantic Schema
                validated_playbook = StrategyPlaybookSchema(**playbook_dict)
                
                logger.info("[ANALYZER] Playbook generated and validated successfully!")
                return validated_playbook.model_dump()

            except json.JSONDecodeError as e:
                logger.error(f"[ANALYZER] Decode Error: Gemini returned invalid JSON -> {str(e)}")
            except Exception as e:
                logger.error(f"[ANALYZER] Network/API Error -> {str(e)}")
            
            # Exponential Backoff logic (Wait 2s, 4s, then abort)
            if attempt < max_retries - 1:
                sleep_time = base_delay * (2 ** attempt)
                logger.warning(f"[ANALYZER] Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        logger.error("[ANALYZER] FATAL: Max retries reached. Returning empty playbook.")
        raise Exception("Gemini API failed to generate a valid playbook.")