from google import genai
from configs.settings import settings
import json
import re


class LLMRanker:
    """
    Uses Gemini (new SDK) to rank trends.
    """

    def __init__(self, logger):
        self.logger = logger

        # Create Gemini client (NEW WAY)
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def build_prompt(self, trends):
        profile = settings.USER_PROFILE

        trends_text = "\n".join(
            [f"{t['id']}. {t['title']}" for t in trends]
        )

        prompt = f"""
    You are NOT allowed to generate new content.

    You are ONLY allowed to SELECT from the given list.

    ROLE:
    You are a strict ranking system, not a creative writer.

    USER PROFILE:
    - Niche: {profile["niche"]}
    - Audience: {profile["audience"]}
    - Goal: {profile["goal"]}
    - Style: {profile["content_style"]}
    - Tone: {profile["tone"]}
    - Avoid: {", ".join(profile["avoid"])}

    STRICT RULES (MANDATORY):
    1. You MUST ONLY choose from the given trends.
    2. You MUST NOT create new titles.
    3. You MUST NOT modify or rewrite titles.
    4. You MUST return EXACT titles from input.
    5. If you break rules, output is invalid.

    TASK:
    - Analyze each trend
    - Score based on, Score strictly MUST be between 1-10. :
        • relevance to niche
        • engagement potential
        • alignment with goal
    - Select TOP 5

    OUTPUT FORMAT (STRICT JSON ONLY, NO EXTRA TEXT):

    [
    {{
        "id": number,
        "title": "EXACT title from list",
        "score": number,
        "reason": "short explanation"
    }}
    ]

    TRENDS:
    {trends_text}
    """
        return prompt


    def extract_json(self, text):
        """
        Extract JSON from LLM response (handles ```json blocks).
        """
        # Remove markdown code block if present
        text = re.sub(r"```json|```", "", text).strip()

        # Try to find JSON array
        match = re.search(r"\[.*\]", text, re.DOTALL)

        if match:
            return match.group(0)

        return text


    def rank(self, trends):
        self.logger.info("Ranking trends using Gemini (new SDK)...")

        prompt = self.build_prompt(trends)

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt
            )

            raw_output = response.text

            # Step 1: Clean markdown
            cleaned_output = self.extract_json(raw_output)

            # Step 2: Parse JSON
            parsed_output = json.loads(cleaned_output)

            return parsed_output

        except Exception as e:
            self.logger.error(f"LLM Error: {str(e)}")
            return None