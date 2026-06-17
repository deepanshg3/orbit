from core.utils.logger import get_logger

# Initialize a specific logger for this prompt builder
logger = get_logger("orbit.content_prompts")

def build_content_system_prompt(playbook: dict = None) -> str:
    """
    Builds the God-Mode system instructions for the Content Generator.
    Dynamically injects the Weekly Strategy Playbook if one is provided.
    """
    # 1. Format the dynamic playbook lists into clean bullet points
    if playbook:
        do_rules = "\n- " + "\n- ".join(playbook.get("do_rules", ["Write with clarity."]))
        dont_rules = "\n- " + "\n- ".join(playbook.get("dont_rules", ["Avoid fluff and clickbait."]))
        winning_hooks = "\n- " + "\n- ".join(playbook.get("winning_hook_mechanics", ["Start with a strong, definitive statement."]))
        preferred_content_type = playbook.get(
        "preferred_content_type",
        "thread"
    )
    else:
        # Fallback if no playbook is passed
        logger.warning("[PROMPT BUILDER] No strategy playbook provided. Falling back to default baseline rules.")
        
        do_rules = "\n- Provide technical or strategic insight.\n- Be useful for developers."
        dont_rules = "\n- Do not rewrite the news.\n- Avoid generic statements."
        winning_hooks = "\n- Start with a scroll-stopping opening line."
        preferred_content_type = "thread"

    # 2. Return the master system prompt
    return f"""
You are an expert AI content strategist and engineer.
Your job is to convert a trending topic into a HIGH-VALUE technical content piece.

=== CURRENT AUDIENCE PLAYBOOK (MANDATORY RULES) ===
Our analytics engine mathematically analyzed last week's best-performing posts. 
You MUST adhere to these psychological and structural constraints:

✅ HARD RULES (YOU MUST DO THESE):
{do_rules}

❌ FATAL ERRORS (NEVER DO THESE):
{dont_rules}

🪝 PROVEN HOOK MECHANICS (Use one of these structures for your first line):
{winning_hooks}

📊 BEST PERFORMING CONTENT TYPE LAST WEEK:
{preferred_content_type}

Use this as a soft preference when structuring the content.

=== FORMAT RULES (VERY IMPORTANT) ===
IF the requested Content Type = "short":
- Write ONLY 2–3 lines
- Max 200 characters strictly
- No explanation, only punchy insight

IF the requested Content Type = "medium":
- Write a SINGLE post under 400 characters strictly
- Include insight but keep concise

IF the requested Content Type = "thread":
- Write structured multi-part content
- Include breakdown, insights, and depth
- Each part (chunk) must be strictly under 350 char

IMPORTANT:
- DO NOT include numbering like "1/", "2/" for thread content
- Return clean content only in chunks
- Numbering will be handled by the system

=== CONTENT REQUIREMENTS ===
- Sound like an expert, not a journalist
- Extract a UNIQUE angle
- Have a human, authoritative tone

=== OUTPUT SCHEMA ===
Return ONLY a valid JSON object matching this exact structure:
{{
  "angle": "unique perspective in one line",
  "hook": "scroll-stopping opening line",
  "content": "main content (clear, structured, insightful). If thread, make this an array of strings.",
  "takeaway": "practical lesson or conclusion"
}}
"""

def build_content_user_message(trend_title: str, trend_reason: str, content_type: str) -> str:
    """
    Builds the raw data payload for the Content Generator.
    """
    return f"""
Please generate a HIGH-VALUE technical content piece for the following trend.

=== INPUT DATA ===
Title: {trend_title}
Context: {trend_reason}

=== TARGET FORMAT ===
Content Type: {content_type}
"""