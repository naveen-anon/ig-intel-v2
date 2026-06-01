import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Changed from PostgreSQL to local SQLite database file
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ig_intel.db")
    
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")
    
    MONITOR_INTERVAL_MINUTES: int = 15

settings = Settings()
