"""
FastAPI Configuration
====================

Configuration settings for the FastAPI application.
"""

import os
from typing import Optional
from pydantic import BaseSettings

class FastAPIConfig(BaseSettings):
    """FastAPI application configuration"""
    
    # Application settings
    app_name: str = "AI Telecaller System API"
    app_version: str = "3.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database settings (same as Flask)
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    database_url: Optional[str] = None
    
    # API settings
    api_prefix: str = ""
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # CORS settings
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global config instance
config = FastAPIConfig()
