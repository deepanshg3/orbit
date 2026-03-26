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
    REDDIT_API_URL = "https://www.reddit.com/r/technology/top.json"
    USER_AGENT = "orbit-app"

    # Posting configuration
    POSTS_PER_DAY = 2

    # Logging configuration
    LOG_LEVEL = "INFO"
    
    #Trends Display in Logs
    TOP_TRENDS_LIMIT = 25
 
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

    #SupaBase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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