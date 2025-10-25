"""
Initialization file for the app package
"""

import logging

# Configure application-wide logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Package version
__version__ = "1.0.0"

# Package metadata
__title__ = "AI Telecaller System"
__description__ = "AI-based IVR Telecaller System for Learn with Leaders"
__author__ = "Learn with Leaders Tech Team"
