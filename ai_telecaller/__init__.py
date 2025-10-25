"""
AI Telecaller System - Modular Package
Refactored from monolithic structure to modular architecture
"""

from .core.telecaller import create_system
from .core.config import config
from .core.conversation import ConversationState

__version__ = "2.0.0"
__author__ = "AI Telecaller Team"

# Main system factory function
def create_telecaller_system():
    """Create and return a new telecaller system instance"""
    return create_system()
