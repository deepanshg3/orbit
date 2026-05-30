import os

"""
Orbit configuration settings.

This file stores system-wide configuration values.
"""

class Settings:
    
    # Application settings
    APP_NAME = "Orbit"
    VERSION = "0.1.0"

    # Reddit API configuration
    user_agent = os.getenv("REDDIT_USER_AGENT")
    REDDIT_API_URL = "https://www.reddit.com/r/technology/top.json"
    REDDIT_USER_AGENT = user_agent

    #Hacker News API configuration
    HN_API_URL = "https://hn.algolia.com/api/v1/search?tags=front_page"
    HN_USER_AGENT = user_agent

    # Posting configuration
    POSTS_PER_DAY = 2

    # Logging configuration
    LOG_LEVEL = "INFO"
    
    #Trends Display in Logs
    TOP_TRENDS_LIMIT = 20
 
    #Max LLM retries
    MAX_LLM_RETRIES=3

    #Select your niche
    NICHE_KEYWORDS = [
    "ai", "machine", "learning", "data", "robot",
    "technology", "software", "nvidia", "openai"
    ]
    
    #API key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = "gemini-2.5-flash"

    # Threads
    THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
    THREADS_APP_SECRET = os.getenv("THREADS_APP_SECRET")
    THREADS_USERNAME= "hard.truths_"

    #SupaBase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # -------------------------------
    # INTERACTION ENGINE SETTINGS
    # -------------------------------

    INTERACTION_KEYWORDS = [
        "AI", "LLM", "AI agents", "machine learning",
        "OpenAI", "GPU", "Anthropic", "Claude", "Gemini"
    ]

    MAX_REPLIES_PER_RUN = 1
    MAX_POSTS_FETCH = 25
    MIN_POST_LENGTH = 30

    # -------------------------------
    # RESPONSE SETTINGS
    # -------------------------------

    REPLY_TONE = "expert, thoughtful, slightly contrarian"
    REPLY_STYLE = "concise, insight-driven"
    MAX_REPLY_LENGTH = 400   # ✅ renamed

    ENABLE_REASON_IN_REPLY = True

    # -------------------------------
    # SAFETY
    # -------------------------------

    ENABLE_INTERACTIONS = True


    #User Profile
    USER_PROFILE = {
    "niche": "AI engineering",
    "audience": "developers building AI systems",
    "goal": "build authority and trust",
    "content_style": "insightful, technical, non-controversial",
    "avoid": ["politics", "religion", "clickbait"],
    "tone": "professional, clear, educational"
}


# Create a global settings object
settings = Settings()