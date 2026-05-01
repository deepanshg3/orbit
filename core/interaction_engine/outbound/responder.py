from google import genai
from configs.settings import settings


class InteractionResponder:

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_reply(self, post_text, reason=None):
        """
        Generate high-quality reply using LLM
        """

        self.logger.info("[RESPONDER] Generating reply...")

        # Optional reasoning injection
        reasoning_context = ""
        if settings.ENABLE_REASON_IN_REPLY and reason:
            reasoning_context = f"""
Context for why this post was selected:
{reason}
"""

        prompt = f"""
You are an expert AI engineer engaging on Threads.

Your tone:
{settings.REPLY_TONE}

Your style:
{settings.REPLY_STYLE}

--------------------------------------------------

Post:
"{post_text}"

{reasoning_context}

--------------------------------------------------

TASK:

Write a reply that:

1. Adds real value (insight, perspective, or clarification)
2. Is NOT generic or obvious
3. Feels natural and human
4. Is concise (1–2 lines)
5. Encourages engagement (optional subtle curiosity)

--------------------------------------------------

RULES:

- Avoid phrases like "Great point", "Interesting", "I agree"
- Do NOT restate the post
- Focus on insight or perspective
- Prefer technical or strategic thinking
- Keep under {settings.MAX_REPLY_LENGTH} characters

--------------------------------------------------

OUTPUT:
Only the reply text. No explanation.
"""

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt
            )

            reply = response.text.strip()

            self.logger.info(f"[RESPONDER] Reply generated ({len(reply)} chars)")

            # Safety trim
            # if len(reply) > settings.MAX_REPLY_LENGTH:
            #     self.logger.warning("[RESPONDER] Reply too long, trimming")
            #     reply = reply[:settings.MAX_REPLY_LENGTH]

            return reply

        except Exception as e:
            self.logger.error(f"[RESPONDER] Failed: {str(e)}")
            return None