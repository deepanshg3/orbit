"""
Orbit configuration settings.

This file stores system-wide configuration values.
"""

class Settings:
    
    # Application settings
    APP_NAME = "Orbit"
    VERSION = "0.1.0"

    # Posting configuration
    POSTS_PER_DAY = 2

    # AI model configuration
    MODEL_NAME = "gpt-4"

    # Logging configuration
    LOG_LEVEL = "INFO"


# Create a global settings object
settings = Settings()