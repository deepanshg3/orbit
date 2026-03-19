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

    # AI model configuration
    MODEL_NAME = "gpt-4"

    # Logging configuration
    LOG_LEVEL = "INFO"
    
    #Trends Display in Logs
    TOP_TRENDS_LIMIT = 5

    #Select your niche
    NICHE_KEYWORDS = [
    "ai", "machine", "learning", "data", "robot",
    "technology", "software", "nvidia", "openai"
    ]


# Create a global settings object
settings = Settings()