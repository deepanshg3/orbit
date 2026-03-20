from google import genai
from configs.settings import settings
from core.utils.schema import RankedTrend
import json
import re


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
                    You are NOT allowed to generate new content.
                    You are ONLY allowed to SELECT from the given list.

                    ROLE:
                    You are a strict ranking and evaluation system.
                    You are NOT a creative writer.

                    --------------------------------------------------

                    USER PROFILE:
                    - Niche: {profile["niche"]}
                    - Audience: {profile["audience"]}
                    - Goal: {profile["goal"]}
                    - Style: {profile["content_style"]}
                    - Tone: {profile["tone"]}
                    - Avoid: {", ".join(profile["avoid"])}

                    --------------------------------------------------

                    STRICT RULES (MANDATORY):

                    1. You MUST ONLY choose from the given trends
                    2. You MUST NOT create new titles
                    3. You MUST NOT modify, rewrite, or summarize titles
                    4. You MUST return EXACT titles from input
                    5. Every returned ID MUST exist in the input list
                    6. If any rule is broken → output is INVALID

                    --------------------------------------------------

                    TASK:

                    You MUST evaluate and score ALL provided trends.

                    For EACH trend:
                    - Analyze carefully
                    - Assign a score between 1 and 10
                    - Provide a short reasoning

                    Scoring MUST consider:
                    • relevance to niche
                    • engagement potential
                    • alignment with user goal
                    • usefulness for content creation

                    --------------------------------------------------

                    IMPORTANT SCORING RULES:

                    - You MUST use the FULL range (1–10)
                    - You MUST NOT cluster scores
                    - You MUST create CLEAR separation between items

                    Score distribution MUST follow:
                    • Top tier → 9–10
                    • Mid tier → 6–8
                    • Low tier → 1–5

                    - The BEST item MUST clearly stand above others
                    - Avoid giving same scores to multiple top items
                    - To avoid giving same score you can go for decimal scores between 1-10, like 9.8, 8.4 like such to make sure no two news have same scores

                    --------------------------------------------------

                    RELATIVE RANKING (CRITICAL):

                    - You MUST compare ALL trends against each other
                    - Scoring MUST be relative, not independent
                    - Think: “which is better than which”

                    --------------------------------------------------

                    VIRALITY SIGNAL:

                    - Lower ID = higher current momentum
                    - This is IMPORTANT but NOT the only factor
                    - Balance virality with relevance and usefulness

                    --------------------------------------------------

                    CONTENT STRATEGY RULES:

                    - Prefer trends that can become:
                    • major breakthoughs
                    • insights
                    • technical breakdowns
                    • engineering lessons
                    • real-world analysis

                    - Prefer topics where a developer can:
                    • explain how something works
                    • analyze failures or risks
                    • discuss tradeoffs
                    • provide expert opinion

                    - Avoid purely informational or shallow news

                    --------------------------------------------------

                    DIVERSITY CONSTRAINT:

                    - DO NOT select multiple trends with the same theme
                    - Ensure selected top items cover DIFFERENT angles
                    - Make sure the topic are diverse
                    --------------------------------------------------

                    QUALITY CONTROL:

                    - The selected trend should be more appealing towards audience and be relevant to audience.

                    --------------------------------------------------

                    FINAL OUTPUT INSTRUCTIONS:

                    - Return ALL trends with scores
                   
                    OUTPUT FORMAT (STRICT JSON ONLY, NO EXTRA TEXT):

                    [
                    {{
                        "id": number,
                        "title": "EXACT title from list",
                        "score": number,
                        "reason": "short explanation"
                    }}
                    ]

                    --------------------------------------------------

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

        for attempt in range(max_retries):
            try:
                self.logger.info(f"[LLM] Attempt {attempt + 1}")

                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )

                raw_output = response.text

                self.logger.debug("[LLM] Raw response received")

                cleaned_output = self.extract_json(raw_output)

                self.logger.debug("[LLM] JSON extracted")

                parsed_output = json.loads(cleaned_output)

                # Structural validation
                if not isinstance(parsed_output, list):
                    raise ValueError("Output is not a list")

                if len(parsed_output) != len(trends):
                    raise ValueError("LLM did not return all trends")

                validated_output = []

                for item in parsed_output:

                    # Field validation
                    if not all(k in item for k in ["id", "title", "score", "reason"]):
                        raise ValueError("Missing required fields")

                    # ID validation
                    if item["id"] not in valid_ids:
                        raise ValueError(f"Invalid ID returned: {item['id']}")

                    # Pydantic validation
                    validated = RankedTrend(**item)
                    validated_output.append(validated)

                self.logger.info("[LLM] Successfully ranked trends")

                validated_output.sort(key=lambda x: x.score, reverse=True)

                top_5 = validated_output[:5]

                return top_5

            except Exception as e:
                self.logger.warning(
                    f"[LLM ERROR] Attempt {attempt + 1} failed | {str(e)}"
                )

        self.logger.error("[LLM ERROR] All attempts failed")
        return None