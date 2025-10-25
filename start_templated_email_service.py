#!/usr/bin/env python3
"""
Start Templated Email Service - Flask App for Testing Templated Emails
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
import logging
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple templated email service for testing
class SimpleTemplatedEmailService:
    """Simple templated email service for API testing"""
    
    def __init__(self):
        self.templates = {
            'signup': 'signup.html',
            'password_reset': 'password_reset.html', 
            'otp': 'otp.html',
            'order_confirmation': 'order_confirmation.html',
            'welcome_pack': 'welcome_pack.html'
        }
        logger.info("✅ Simple Templated Email Service initialized")
    
    def send_templated_email(self, template_type, data):
        """Simulate sending a templated email"""
        if template_type not in self.templates:
            return {"success": False, "error": f"Template '{template_type}' not found"}
        
        # Log the email details (simulate sending)
        logger.info(f"📧 Sending {template_type} email to {data.get('to_email', 'unknown@example.com')}")
        logger.info(f"   Data: {data}")
        
        return {
            "success": True,
            "message_id": f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}-{template_type}",
            "template": template_type,
            "recipient": data.get('to_email', 'unknown@example.com')
        }

# Initialize service
email_service = SimpleTemplatedEmailService()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Templated Email Service",
        "timestamp": datetime.now().isoformat(),
        "available_templates": list(email_service.templates.keys())
    })

@app.route('/api/templated-email/status', methods=['GET'])
def status():
    """Get service status and available templates"""
    return jsonify({
        "status": "running",
        "service": "Templated Email API",
        "available_templates": list(email_service.templates.keys()),
        "endpoints": [
            "/api/templated-email/send-signup",
            "/api/templated-email/send-password-reset",
            "/api/templated-email/send-otp",
            "/api/templated-email/send-order-confirmation",
            "/api/templated-email/send-welcome-pack"
        ]
    })

@app.route('/api/templated-email/send-signup', methods=['POST'])
def send_signup_email():
    """Send signup confirmation email"""
    try:
        data = request.get_json()
        if not data.get('to_email'):
            return jsonify({"error": "to_email is required"}), 400
            
        result = email_service.send_templated_email('signup', data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending signup email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templated-email/send-password-reset', methods=['POST'])
def send_password_reset_email():
    """Send password reset email"""
    try:
        data = request.get_json()
        if not data.get('to_email'):
            return jsonify({"error": "to_email is required"}), 400
            
        result = email_service.send_templated_email('password_reset', data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templated-email/send-otp', methods=['POST'])
def send_otp_email():
    """Send OTP verification email"""
    try:
        data = request.get_json()
        if not data.get('to_email'):
            return jsonify({"error": "to_email is required"}), 400
            
        result = email_service.send_templated_email('otp', data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending OTP email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templated-email/send-order-confirmation', methods=['POST'])
def send_order_confirmation_email():
    """Send order confirmation email"""
    try:
        data = request.get_json()
        if not data.get('to_email'):
            return jsonify({"error": "to_email is required"}), 400
            
        result = email_service.send_templated_email('order_confirmation', data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending order confirmation email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templated-email/send-welcome-pack', methods=['POST'])
def send_welcome_pack_email():
    """Send welcome pack email with PDF"""
    try:
        data = request.get_json()
        if not data.get('to_email'):
            return jsonify({"error": "to_email is required"}), 400
            
        result = email_service.send_templated_email('welcome_pack', data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sending welcome pack email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Simple index page"""
    return jsonify({
        "service": "Templated Email API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "status": "/api/templated-email/status",
            "signup": "/api/templated-email/send-signup",
            "password_reset": "/api/templated-email/send-password-reset",
            "otp": "/api/templated-email/send-otp",
            "order_confirmation": "/api/templated-email/send-order-confirmation",
            "welcome_pack": "/api/templated-email/send-welcome-pack"
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Templated Email Service...")
    print("📧 Available endpoints:")
    print("   - http://localhost:5000/health")
    print("   - http://localhost:5000/api/templated-email/status")
    print("   - http://localhost:5000/api/templated-email/send-signup")
    print("   - http://localhost:5000/api/templated-email/send-password-reset")
    print("   - http://localhost:5000/api/templated-email/send-otp")
    print("   - http://localhost:5000/api/templated-email/send-order-confirmation")
    print("   - http://localhost:5000/api/templated-email/send-welcome-pack")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)