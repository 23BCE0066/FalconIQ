import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "FalconIQ API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your_secret_key_here"
    CLERK_SECRET_KEY: str = "your_clerk_secret_key_here"
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: str = "pk_test_YW11c2VkLWhlcm1pdC0xLmNsZXJrLmFjY291bnRzLmRldiQ"
    
    # Database
    DATABASE_URL: str = "sqlite:///./falconiq.db"
    DB_ECHO: bool = True
    SUPABASE_URL: Optional[str] = "https://qpfeycxloytbpdoidzms.supabase.co"
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = "sb_publishable_RcTCl6gd0l0CIHYB6Pim2g_Kkpd4bNh"
    
    # External APIs & Agents
    GEMINI_API_KEY: str = "your_gemini_api_key_here"
    AGENT_API_KEY: str = "your_agent_api_key_here"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
