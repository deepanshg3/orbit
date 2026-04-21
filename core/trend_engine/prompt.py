from core.utils.logger import get_logger

# Initialize a specific logger for this prompt builder
logger = get_logger("orbit.ranker_prompts")

def build_ranker_prompt(trends: list, profile: dict, playbook: dict = None) -> str:
    """
    Builds the prompt for the LLM Ranker.
    Dynamically injects winning and losing topics from the Weekly Strategy Playbook.
    """
    
    # 1. Format the raw trends list
    trends_text = "\n".join([f"{t['id']}. {t['title']}" for t in trends])

    # 2. Format the dynamic playbook (The mathematical strategy)
    if playbook:
        winning_topics = "\n- " + "\n- ".join(playbook.get("winning_topics", ["Topics highly relevant to the User Profile"]))
        losing_topics = "\n- " + "\n- ".join(playbook.get("losing_topics", ["Off-topic or overly generic news"]))
        
        strategy_block = f"""
=== CURRENT AUDIENCE STRATEGY (DATA-DRIVEN) ===
Our analytics engine proved what our audience engaged with last week.
You MUST heavily bias your scoring based on these exact trends:

🔥 PRIORITIZE (Boost scores for these topics):
{winning_topics}

🧊 PENALIZE (Lower scores or ignore these topics):
{losing_topics}
"""
    else:
        # Fallback if no playbook is passed
        logger.warning("[PROMPT BUILDER] No strategy playbook provided. Falling back to base User Profile targeting.")
        strategy_block = """
=== CURRENT AUDIENCE STRATEGY ===
No specific historical data provided this week. Rely entirely on the USER PROFILE below to determine relevance.
"""

    # 3. Return the master prompt string
    return f"""
You are a strict ranking system. You must ONLY select from the given trends.

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

1. Score ALL trends (1–10)
Based on:
- relevance to the User Profile AND Current Audience Strategy
- engagement potential
- usefulness

2. ALSO decide content_type for each trend, decide based upon how much attention it needs:

Choose ONE:
- "short" → for quick news, announcements, simple ideas (under 200 chars)
- "medium" → for moderate insights (under 400 chars)
- "thread" → for deep insights, technical topics, case studies (multi-post)

Guidelines:
- Complex / high-value insights → thread
- Breaking news / simple updates → short
- Balanced topics → medium

3. Scoring rules:
- Use full range (1–10)
- Make sure scores are unique, score them in decimal between 1-10 like 9.8, 9.4, 7.9 
- Scores must be relative
- Lower ID = higher virality (use as signal, not rule)
- Clearly differentiate top vs average vs weak

4. Select TOP 5 after scoring

OUTPUT:
Return ONLY TOP 5 items.

[
  {{
      "id": number,
      "title": "exact title",
      "score": number,
      "content_type": "short | medium | thread",
      "reason": "short explanation"
  }}
]

TRENDS:
{trends_text}
"""