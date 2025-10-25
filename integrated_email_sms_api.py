#!/usr/bin/env python3
"""
Integrated Email/SMS API Server
Clean REST APIs for email and SMS services integrated into the main IVR system
Test with Postman after deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the clean services
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.templated_email_service import TemplatedEmailService
from app.services.unified_templated_email_service import UnifiedTemplatedEmailService

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize services
email_service = EmailService()
sms_service = SMSService()
templated_email_service = TemplatedEmailService()
unified_templated_email_service = UnifiedTemplatedEmailService()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'operational',
        'message': 'Email/SMS API Server is running',
        'services': {
            'email': 'Available',
            'sms': 'Available', 
            'templated_email': 'Available'
        },
        'endpoints': {
            'email': '/email',
            'sms': '/sms/send',
            'bulk_sms': '/sms/bulk',
            'templated_email': '/templated-email/{template_type}',
            'status': '/status'
        }
    })

# ===== EMAIL ENDPOINTS =====
@app.route('/email', methods=['POST', 'OPTIONS'])
def send_email():
    """
    Send email endpoint
    
    POST /email
    {
        "email_type": "smtp|customdomain|subdomain",
        "to_email": "recipient@example.com", 
        "subject": "Email Subject",
        "body": "Email body content",
        "is_html": false,
        "sender_email": "optional@sender.com",
        "smtp_email": "optional@gmail.com",
        "smtp_password": "optional_password"
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        
        # Add default SMTP credentials from environment if not provided
        if data.get('email_type') == 'smtp' and not data.get('smtp_email'):
            data['smtp_email'] = os.getenv('EMAIL_USERNAME')
            data['smtp_password'] = os.getenv('EMAIL_PASSWORD')
        
        result = email_service.send_email(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Email sending failed: {str(e)}'
        }), 500

@app.route('/email/bulk', methods=['POST', 'OPTIONS'])
def send_bulk_email():
    """
    Send bulk email endpoint
    
    POST /email/bulk
    {
        "email_type": "smtp|customdomain|subdomain",
        "recipients": ["user1@example.com", "user2@example.com"],
        "subject": "Bulk Email Subject",
        "body": "Bulk email body content",
        "is_html": false,
        "sender_email": "optional@sender.com",
        "smtp_email": "optional@gmail.com",
        "smtp_password": "optional_password"
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        
        # Validate required fields for bulk email
        if not data.get('recipients'):
            return jsonify({
                'success': False,
                'error': 'Missing required field: recipients'
            }), 400
            
        if not isinstance(data.get('recipients'), list):
            return jsonify({
                'success': False,
                'error': 'recipients must be an array of email addresses'
            }), 400
            
        if len(data.get('recipients', [])) == 0:
            return jsonify({
                'success': False,
                'error': 'recipients array cannot be empty'
            }), 400
        
        # Add default SMTP credentials from environment if not provided
        if data.get('email_type') == 'smtp' and not data.get('smtp_email'):
            data['smtp_email'] = os.getenv('EMAIL_USERNAME')
            data['smtp_password'] = os.getenv('EMAIL_PASSWORD')
        
        recipients = data.get('recipients')
        successful_sends = 0
        failed_sends = 0
        results = []
        
        # Send email to each recipient
        for recipient in recipients:
            try:
                # Create individual email data
                email_data = data.copy()
                email_data['to_email'] = recipient
                del email_data['recipients']  # Remove bulk field
                
                result = email_service.send_email(email_data)
                
                if result.get('success'):
                    successful_sends += 1
                    results.append({
                        'email': recipient,
                        'success': True,
                        'message': 'Email sent successfully'
                    })
                else:
                    failed_sends += 1
                    results.append({
                        'email': recipient,
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                failed_sends += 1
                results.append({
                    'email': recipient,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'Bulk email completed: {successful_sends} sent, {failed_sends} failed',
            'total_recipients': len(recipients),
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'email_type': data.get('email_type'),
            'subject': data.get('subject'),
            'results': results
        }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Bulk email sending failed: {str(e)}'
        }), 500

@app.route('/email/status', methods=['GET'])
def email_status():
    """Get email service status"""
    try:
        result = email_service.get_service_status()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        }), 500

# ===== SMS ENDPOINTS =====
@app.route('/sms/send', methods=['POST', 'OPTIONS'])
def send_sms():
    """
    Send single SMS endpoint
    
    POST /sms/send
    {
        "phone_number": "+1234567890",
        "message": "Your SMS message here",
        "sender_id": "IVR"
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        result = sms_service.send_sms(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'SMS sending failed: {str(e)}'
        }), 500

@app.route('/sms/bulk', methods=['POST', 'OPTIONS'])
def send_bulk_sms():
    """
    Send bulk SMS endpoint
    
    POST /sms/bulk
    {
        "phone_numbers": ["+1234567890", "+0987654321"],
        "message": "Bulk SMS message",
        "sender_id": "IVR"
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        result = sms_service.send_bulk_sms(data)
        
        return jsonify(result), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Bulk SMS sending failed: {str(e)}'
        }), 500

@app.route('/sms/status', methods=['GET'])
def sms_status():
    """Get SMS service status"""
    try:
        result = sms_service.get_sms_status()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'SMS status check failed: {str(e)}'
        }), 500

# ===== TEMPLATED EMAIL ENDPOINTS =====

@app.route('/templated-email', methods=['POST', 'OPTIONS'])
def send_unified_templated_email():
    """
    Send templated email with unified interface
    
    POST /templated-email
    Body: {
        "email_type": "smtp|customdomain|subdomain",
        "template_type": "otp|login|registration", 
        "to_email": "recipient@example.com",
        "username": "User Name",
        "otp_code": "123456",  // for OTP template
        "expiry_minutes": 10,   // for OTP template
        "login_time": "2025-10-04 10:30",  // for login template
        "device": "Chrome Browser",        // for login template
        "registration_date": "2025-10-04", // for registration template
        "login_url": "https://app.com/login", // for registration template
        "smtp_email": "sender@gmail.com",  // for SMTP only
        "smtp_password": "app_password"    // for SMTP only
    }
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
            
        result = unified_templated_email_service.send_templated_email(data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Templated email failed: {str(e)}'
        }), 500

@app.route('/templated-email/otp', methods=['POST', 'OPTIONS'])
def send_otp_email():
    """
    Send OTP email
    
    POST /templated-email/otp
    {
        "to": "user@example.com",
        "username": "John Doe",
        "otp_code": "123456",
        "expiry_minutes": 10
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        result = templated_email_service.send_otp_email(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'OTP email failed: {str(e)}'
        }), 500

@app.route('/templated-email/welcome', methods=['POST', 'OPTIONS'])
def send_welcome_email():
    """
    Send welcome email with PDF
    
    POST /templated-email/welcome
    {
        "to": "user@example.com",
        "username": "John Doe",
        "company_name": "Tech Corp",
        "course_name": "AI Basics"
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        result = templated_email_service.send_welcome_pack_email(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Welcome email failed: {str(e)}'
        }), 500

@app.route('/templated-email/order', methods=['POST', 'OPTIONS'])
def send_order_email():
    """
    Send order confirmation email
    
    POST /templated-email/order
    {
        "to": "user@example.com",
        "username": "John Doe",
        "order_id": "ORD123",
        "order_total": "$99.99",
        "items": [
            {"name": "Product 1", "quantity": 2, "price": "$49.99"}
        ]
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        result = templated_email_service.send_order_confirmation_email(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Order email failed: {str(e)}'
        }), 500

@app.route('/templated-email/login', methods=['POST', 'OPTIONS'])
def send_login_email():
    """
    Send login notification email via unified service
    
    POST /templated-email/login
    Body: {
        "email_type": "smtp|customdomain|subdomain",
        "to": "user@example.com",  // or "to_email"
        "username": "User Name",
        "login_time": "2025-10-04 16:30",
        "device": "Chrome Browser"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        # Add template_type for unified service
        data['template_type'] = 'login'
        
        result = unified_templated_email_service.send_templated_email(data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login email failed: {str(e)}'
        }), 500

@app.route('/templated-email/registration', methods=['POST', 'OPTIONS'])
def send_registration_email():
    """
    Send registration welcome email via unified service
    
    POST /templated-email/registration
    Body: {
        "email_type": "smtp|customdomain|subdomain",
        "to": "user@example.com",  // or "to_email"
        "username": "User Name",
        "registration_date": "2025-10-04",
        "login_url": "https://app.com/login"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        # Add template_type for unified service
        data['template_type'] = 'registration'
        
        result = unified_templated_email_service.send_templated_email(data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Registration email failed: {str(e)}'
        }), 500

@app.route('/templated-email/status', methods=['GET'])
def templated_email_status():
    """Get templated email service status"""
    try:
        result = templated_email_service.get_service_status()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        }), 500

# ===== OVERALL STATUS ENDPOINT =====
@app.route('/status', methods=['GET'])
def overall_status():
    """Get status of all services"""
    try:
        status = {
            'overall_status': 'operational',
            'services': {
                'email': email_service.get_service_status(),
                'sms': sms_service.get_sms_status(),
                'templated_email': templated_email_service.get_service_status()
            }
        }
        
        return jsonify(status), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        }), 500

# ===== IVR INTEGRATION HELPERS =====
@app.route('/ivr/send-otp', methods=['POST'])
def ivr_send_otp():
    """
    IVR-specific OTP sending (both SMS and email)
    
    POST /ivr/send-otp
    {
        "phone": "+1234567890",
        "email": "user@example.com", 
        "name": "John Doe",
        "otp": "123456"
    }
    """
    try:
        data = request.get_json()
        
        results = {
            'otp_code': data.get('otp'),
            'sms_result': None,
            'email_result': None
        }
        
        # Send SMS OTP
        if data.get('phone'):
            sms_data = {
                'phone_number': data['phone'],
                'message': f"Your OTP is {data.get('otp')}. Valid for 10 minutes.",
                'sender_id': 'IVR'
            }
            results['sms_result'] = sms_service.send_sms(sms_data)
        
        # Send Email OTP
        if data.get('email'):
            email_data = {
                'to': data['email'],
                'username': data.get('name', 'User'),
                'otp_code': data.get('otp'),
                'expiry_minutes': 10
            }
            results['email_result'] = templated_email_service.send_otp_email(email_data)
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'IVR OTP sending failed: {str(e)}'
        }), 500

@app.route('/ivr/call-summary', methods=['POST'])
def ivr_call_summary():
    """
    Send call completion summary
    
    POST /ivr/call-summary
    {
        "email": "user@example.com",
        "name": "John Doe",
        "call_details": {
            "reference": "CALL123",
            "duration": "5 minutes",
            "status": "Completed"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Send via regular email
        email_data = {
            'email_type': 'smtp',
            'to_email': data['email'],
            'subject': 'Call Completion Summary',
            'body': f"""
Dear {data.get('name', 'User')},

Your call has been completed successfully.

Call Reference: {data.get('call_details', {}).get('reference', 'N/A')}
Duration: {data.get('call_details', {}).get('duration', 'N/A')}
Status: {data.get('call_details', {}).get('status', 'Completed')}

Thank you for using our service.

Best regards,
IVR Support Team
            """,
            'is_html': False
        }
        
        result = email_service.send_email(email_data)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Call summary sending failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Load environment variables
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Starting Email/SMS API Server on port {port}")
    print(f"📧 Email Service: Ready")
    print(f"📱 SMS Service: Ready") 
    print(f"📋 Templated Email Service: Ready")
    print(f"🔧 Debug Mode: {debug}")
    print(f"\n📚 Available endpoints:")
    print(f"   GET  /            - Health check")
    print(f"   POST /email       - Send email")
    print(f"   POST /email/bulk  - Send bulk email")
    print(f"   POST /sms/send    - Send SMS")
    print(f"   POST /sms/bulk    - Send bulk SMS")
    print(f"   POST /templated-email/otp     - Send OTP email")
    print(f"   POST /templated-email/welcome - Send welcome email") 
    print(f"   POST /templated-email/order   - Send order email")
    print(f"   POST /ivr/send-otp           - IVR OTP (SMS + Email)")
    print(f"   POST /ivr/call-summary       - IVR call summary")
    print(f"   GET  /status      - Overall status")
    print(f"\n🎯 Test with Postman: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)