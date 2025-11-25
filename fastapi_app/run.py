#!/usr/bin/env python3
"""
FastAPI Application Runner
=========================

Run the FastAPI application with proper configuration.
"""

import uvicorn
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi_app.config import config
from fastapi_app.main import app

def main():
    """Run the FastAPI application"""
    print("🚀 Starting AI Telecaller FastAPI Application")
    print("=" * 50)
    print(f"📱 Application: {config.app_name}")
    print(f"🔢 Version: {config.app_version}")
    print(f"🌐 Server: http://{config.host}:{config.port}")
    print(f"📚 Documentation: http://{config.host}:{config.port}{config.docs_url}")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
