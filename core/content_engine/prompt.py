from core.utils.logger import get_logger

# Initialize a specific logger for this prompt builder
logger = get_logger("orbit.content_prompts")

def build_content_prompt(trend_title: str, trend_reason: str, content_type: str, playbook: dict = None) -> str:
    """
    Builds the prompt for the Content Generator. 
    Dynamically injects the Weekly Strategy Playbook if one is provided.
    """
    # 1. Format the dynamic playbook lists into clean bullet points
    if playbook:
        do_rules = "\n- " + "\n- ".join(playbook.get("do_rules", ["Write with clarity."]))
        dont_rules = "\n- " + "\n- ".join(playbook.get("dont_rules", ["Avoid fluff and clickbait."]))
        winning_hooks = "\n- " + "\n- ".join(playbook.get("winning_hook_mechanics", ["Start with a strong, definitive statement."]))
        optimal_length = playbook.get("optimal_length_range", "Adhere strictly to the content type limits below.")
    else:
        # Fallback if no playbook is passed
        logger.warning("[PROMPT BUILDER] No strategy playbook provided. Falling back to default baseline rules.")
        
        do_rules = "\n- Provide technical or strategic insight.\n- Be useful for developers."
        dont_rules = "\n- Do not rewrite the news.\n- Avoid generic statements."
        winning_hooks = "\n- Start with a scroll-stopping opening line."
        optimal_length = "Keep it concise but dense."

    # 2. Return the master prompt string
    return f"""
You are an expert AI content strategist and engineer.
Your job is to convert a trending topic into a HIGH-VALUE technical content piece.

--------------------------------------------------
INPUT:

Title:
{trend_title}

Context:
{trend_reason}

Content Type:
{content_type}

--------------------------------------------------
🎯 CURRENT AUDIENCE PLAYBOOK (MANDATORY RULES)

Our analytics engine mathematically analyzed last week's best-performing posts. 
You MUST adhere to these psychological and structural constraints:

✅ HARD RULES (YOU MUST DO THESE):
{do_rules}

❌ FATAL ERRORS (NEVER DO THESE):
{dont_rules}

🪝 PROVEN HOOK MECHANICS (Use one of these structures for your first line):
{winning_hooks}

📏 OPTIMAL PACING TREND:
{optimal_length}
(Note: You must still strictly respect the hard character limits in the FORMAT RULES below).

--------------------------------------------------
FORMAT RULES (VERY IMPORTANT):

IF content_type = "short":
- Write ONLY 2–3 lines
- Max 250 characters strictly
- No explanation, only punchy insight

IF content_type = "medium":
- Write a SINGLE post under 450 characters strictly
- Include insight but keep concise

IF content_type = "thread":
- Write structured multi-part content
- Include breakdown, insights, and depth
- Each part (chunk) must be strictly under 450 char

IMPORTANT:
- DO NOT include numbering like "1/", "2/" for thread content
- Return clean content only in chunks
- Numbering will be handled by the system

--------------------------------------------------
CONTENT REQUIREMENTS:
- Sound like an expert, not a journalist
- Extract a UNIQUE angle
- Have a human, authoritative tone

--------------------------------------------------
STRUCTURE:

Return JSON with:

{{
  "angle": "unique perspective in one line",
  "hook": "scroll-stopping opening line",
  "content": "main content (clear, structured, insightful)",
  "takeaway": "practical lesson or conclusion"
}}

--------------------------------------------------
OUTPUT:
STRICT JSON ONLY
"""