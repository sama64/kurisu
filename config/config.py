from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-sonnet")
    ALLOWED_CHAT_ID: int = int(os.getenv("ALLOWED_CHAT_ID", "0"))
    MAX_HISTORY_LENGTH: int = 30
    PROACTIVE_MESSAGE_MIN_INTERVAL: int = 3600  # 1 hour in seconds
    PROACTIVE_MESSAGE_MAX_INTERVAL: int = 14400  # 4 hours in seconds

config = Config() 