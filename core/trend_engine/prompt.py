from core.utils.logger import get_logger

logger = get_logger("orbit.ranker_prompts")

def build_ranker_system_prompt(profile: dict, playbook: dict = None) -> str:
    """Builds the God-Mode system instructions for the Ranker."""
    
    if playbook:
        winning_topics = "\n- " + "\n- ".join(playbook.get("winning_topics", ["Topics highly relevant to the User Profile"]))
        losing_topics = "\n- " + "\n- ".join(playbook.get("losing_topics", ["Off-topic or overly generic news"]))
        strategy_block = f"""
=== CURRENT AUDIENCE STRATEGY (DATA-DRIVEN) ===
🔥 PRIORITIZE (Boost scores for these topics):
{winning_topics}

🧊 PENALIZE (Lower scores or ignore these topics):
{losing_topics}
"""
    else:
        logger.warning("[PROMPT BUILDER] No strategy playbook provided. Falling back to base User Profile.")
        strategy_block = "=== CURRENT AUDIENCE STRATEGY ===\nNo historical data. Rely entirely on the USER PROFILE."

    return f"""
You are a strict ranking system. You must ONLY select from the provided trends.

USER PROFILE:
- Niche: {profile["niche"]}
- Audience: {profile["audience"]}
- Goal: {profile["goal"]}
- Style: {profile["content_style"]}
- Tone: {profile["tone"]}

{strategy_block}

RULES (MANDATORY):
- Use ONLY given trends
- DO NOT modify titles
- Return EXACT titles
- All IDs must exist in input

TASK:
1. Score ALL trends (1–10) based on relevance to the User Profile AND Current Strategy.
2. ALSO decide content_type ("short", "medium", or "thread").
3. Make sure scores are unique decimal numbers (e.g., 9.8, 9.4).
4. Select TOP 5 after scoring.

=== OUTPUT SCHEMA (MANDATORY) ===
You must return a JSON array containing exactly 5 objects. Each object MUST have the exact following keys:
[
  {{
      "id": number,
      "title": "exact title",
      "score": number,
      "content_type": "short | medium | thread",
      "reason": "short explanation"
  }}
]
"""

def build_ranker_user_message(trends: list) -> str:
    """Builds the raw data payload."""
    trends_text = "\n".join([f"{t['id']}. {t['title']}" for t in trends])
    return f"Rank these TRENDS based on your system instructions and return the JSON array:\n{trends_text}"