#!/usr/bin/env python3
"""
AI IVR Telecaller System - Modular Entry Point
Uses the refactored modular architecture
"""

import time
from ai_telecaller.core.telecaller import create_system

def main():
    """Main function using modular system"""
    print("🚀 AI IVR Telecaller System Starting...")
    print("="*60)
    
    # Create the modular telecaller system
    system = create_system()
    
    try:
        # Start ngrok tunnel
        if not system.start_ngrok():
            print("❌ Failed to start ngrok. Please ensure ngrok is installed.")
            return
        
        # Start Flask server
        system.start_flask_server()
        
        # Wait for everything to initialize
        time.sleep(2)
        
        print("\n✅ System Ready!")
        print(f"🌐 Webhook URL: {system.ngrok_url}")
        print(f"📱 Configure this URL in your Twilio webhook settings")
        
        # Run interactive menu
        system.run_interactive_menu()
        
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        system.shutdown()

if __name__ == "__main__":
    main()
