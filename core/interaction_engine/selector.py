from google import genai
from configs.settings import settings
import json
import re


class InteractionSelector:

    def __init__(self, logger):
        self.logger = logger
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract_json(self, text):
        """
        Clean LLM response and extract JSON safely
        """
        text = re.sub(r"```json|```", "", text).strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        return match.group(0) if match else text

    def select_top_posts(self, posts):
        """
        Select top 5 posts using LLM ranking
        """

        if not posts:
            self.logger.warning("[SELECTOR] No posts available")
            return []

        # Limit (safe even if 25 already)
        posts = posts[:25]

        self.logger.info(f"[SELECTOR] Sending {len(posts)} posts to LLM")

        # Format posts
        formatted_posts = "\n".join(
            [f"{i+1}. {p['text']}" for i, p in enumerate(posts)]
        )

        prompt = f"""
You are an expert AI engineer and content strategist.

You are selecting the BEST posts to reply to on Threads.

--------------------------------------------------

POSTS:
{formatted_posts}

--------------------------------------------------

TASK:

Select TOP 5 posts worth replying to.

You MUST rank them based on RELATIVE COMPARISON.

--------------------------------------------------

SCORING CRITERIA (Total = 10):

1. Technical relevance (AI, dev, systems) → /3
2. Depth of discussion (not surface-level) → /2
3. Opportunity to add value (can you contribute insight?) → /2
4. Engagement potential (controversial, interesting, useful) → /2
5. Clarity / signal (not noise, not spam) → /1

--------------------------------------------------

IMPORTANT RULES:

- Avoid generic posts (e.g., "hello", "AI is cool")
- Prefer posts with clear technical angle
- Prefer posts where a thoughtful reply adds value
- Compare posts AGAINST each other before ranking
- Be selective and critical

--------------------------------------------------

OUTPUT FORMAT (STRICT JSON):

[
  {{
    "rank": 1,
    "post_index": 3,
    "score": 9.2,
    "reason": "High technical depth and strong opportunity to add insight"
  }},
  {{
    "rank": 2,
    "post_index": 7,
    "score": 8.8,
    "reason": "Good discussion with engagement potential"
  }}
]

ONLY return JSON. No explanation outside JSON.
"""

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt
            )

            raw_output = response.text
            self.logger.debug(f"[SELECTOR] Raw response: {raw_output}")

            cleaned = self.extract_json(raw_output)
            parsed = json.loads(cleaned)

            # Map back to actual posts
            top_posts = []

            for item in parsed:
                idx = item["post_index"] - 1

                if 0 <= idx < len(posts):
                    post = posts[idx]

                    post["score"] = item.get("score", 0)
                    post["reason"] = item.get("reason", "")

                    top_posts.append(post)

            self.logger.info(f"[SELECTOR] Selected top {len(top_posts)} posts")

            return top_posts

        except Exception as e:
            self.logger.error(f"[SELECTOR] LLM failed: {str(e)}")

            # fallback: return first 3 safely
            return posts[:3]