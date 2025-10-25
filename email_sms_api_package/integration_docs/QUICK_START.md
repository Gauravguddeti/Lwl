# Quick Setup Guide for Your Friend's IVR Integration

## 🎯 For the IVR Developer (Your Friend)

This is a **ready-to-deploy** email and SMS API package extracted from a working system. Here's how to get it running in 10 minutes:

### Step 1: Deploy the APIs (5 minutes)

```bash
# 1. Copy the email_sms_api_package folder to your workspace
# 2. Open terminal in the package directory

# Install dependencies
npm install
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your AWS credentials

# Deploy to AWS
npm run deploy
```

**You'll get endpoints like:**
```
Email API: https://abc123.execute-api.us-west-2.amazonaws.com/dev/email
SMS API: https://abc123.execute-api.us-west-2.amazonaws.com/dev/sms  
Templates: https://abc123.execute-api.us-west-2.amazonaws.com/dev/templated-email
```

### Step 2: Test the APIs (2 minutes)

```bash
# Test email
curl -X POST https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/email \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","subject":"Test","body":"It works!","method":"ses_custom"}'

# Test SMS  
curl -X POST https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/sms/send \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+1234567890","message":"SMS test from IVR"}'
```

### Step 3: Integrate into Your IVR (3 minutes)

Add this helper class to your IVR project:

```python
# ivr_notifications.py
import requests
import json

class IVRNotifications:
    def __init__(self, api_base_url):
        self.base_url = api_base_url
        self.headers = {'Content-Type': 'application/json'}
    
    def send_otp_sms(self, phone, otp):
        """Send OTP via SMS"""
        url = f"{self.base_url}/sms/send"
        data = {"phone_number": phone, "message": f"Your OTP is {otp}"}
        return requests.post(url, json=data, headers=self.headers).json()
    
    def send_otp_email(self, email, username, otp):
        """Send professional OTP email"""
        url = f"{self.base_url}/templated-email/otp"
        data = {
            "to": email,
            "username": username, 
            "otp_code": otp,
            "expiry_minutes": 10
        }
        return requests.post(url, json=data, headers=self.headers).json()
    
    def send_call_summary(self, email, username, call_details):
        """Send call completion email"""
        url = f"{self.base_url}/email"
        body = f"""
        Dear {username},
        
        Your call has been completed successfully.
        
        Call Reference: {call_details.get('reference', 'N/A')}
        Duration: {call_details.get('duration', 'N/A')}
        Status: {call_details.get('status', 'Completed')}
        
        Thank you for using our service.
        """
        
        data = {
            "to": email,
            "subject": "Call Completion Summary",
            "body": body,
            "method": "ses_custom"
        }
        return requests.post(url, json=data, headers=self.headers).json()

# Initialize in your IVR system
notifications = IVRNotifications("https://your-api-id.execute-api.us-west-2.amazonaws.com/dev")
```

### Step 4: Use in Your IVR Flows

```python
# In your IVR call handling code

# 1. Send OTP during verification
def handle_otp_verification(customer_phone, customer_email, customer_name):
    otp = generate_random_otp()  # Your existing OTP logic
    
    # Send via both SMS and email
    sms_result = notifications.send_otp_sms(customer_phone, otp)
    email_result = notifications.send_otp_email(customer_email, customer_name, otp)
    
    return otp  # Use in your verification flow

# 2. Send completion notifications
def handle_call_completion(customer_info, call_summary):
    notifications.send_call_summary(
        customer_info['email'],
        customer_info['name'], 
        call_summary
    )
    
    # Also send SMS notification
    notifications.send_otp_sms(
        customer_info['phone'],
        f"Call completed. Reference: {call_summary['reference']}"
    )
```

## 🔧 Required Environment Variables

Add to your `.env` file:

```bash
# Minimum required for basic functionality
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-west-2

# Email configuration
SES_SENDER_EMAIL=support@f5universe.com
EMAIL_USERNAME=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password

# SMS configuration  
SMS_SENDER_ID=IVR
SMS_SANDBOX_MODE=true
```

## 📞 Common IVR Integration Patterns

### Pattern A: Customer Verification
```python
# During customer verification in IVR
customer = get_customer_info(phone_number)
otp = generate_otp()

# Send OTP via SMS (primary)
notifications.send_otp_sms(customer['phone'], otp)

# Send OTP via email (backup) 
notifications.send_otp_email(customer['email'], customer['name'], otp)

# Continue with IVR verification flow...
```

### Pattern B: Transaction Confirmation
```python
# After completing a transaction in IVR
transaction_details = process_transaction(customer_data)

# Send confirmation email
notifications.send_call_summary(
    customer_data['email'],
    customer_data['name'],
    {
        'reference': transaction_details['id'],
        'status': 'Completed',
        'amount': transaction_details['amount']
    }
)
```

### Pattern C: Appointment Booking
```python
# After booking appointment via IVR
appointment = book_appointment(customer_info, slot)

# Send confirmation via templated email
url = f"{notifications.base_url}/templated-email/order"
confirmation_data = {
    "to": customer_info['email'],
    "username": customer_info['name'],
    "order_id": appointment['id'],
    "order_total": "Appointment Booked",
    "items": [
        {
            "name": f"Appointment on {appointment['date']}",
            "quantity": 1,
            "price": appointment['time']
        }
    ]
}
requests.post(url, json=confirmation_data, headers=notifications.headers)
```

## 🚨 Error Handling in IVR

```python
def safe_send_notification(func, *args, **kwargs):
    """Wrapper for safe notification sending"""
    try:
        result = func(*args, **kwargs)
        if result.get('success'):
            return True
        else:
            log_error(f"Notification failed: {result.get('error')}")
            return False
    except Exception as e:
        log_error(f"Notification exception: {str(e)}")
        return False

# Usage in IVR
sms_sent = safe_send_notification(notifications.send_otp_sms, phone, otp)
if not sms_sent:
    # Fallback: try email or voice announcement
    email_sent = safe_send_notification(notifications.send_otp_email, email, name, otp)
```

## 📋 Testing Checklist

Before going live, test these scenarios:

- [ ] Send OTP SMS to your phone number
- [ ] Send OTP email to your email address  
- [ ] Send call summary email
- [ ] Test with invalid phone numbers (should return error)
- [ ] Test with invalid email addresses (should return error)
- [ ] Check AWS CloudWatch logs for any errors

## 🎉 That's It!

Your friend now has working email and SMS APIs that can be called from any part of the IVR system. The APIs are:

✅ **Production-ready** - Extracted from working system  
✅ **Scalable** - AWS Lambda auto-scales  
✅ **Reliable** - Professional error handling  
✅ **Easy to use** - Simple REST API calls  
✅ **Well-documented** - Clear examples for every use case  

The heavy lifting of email templates, SMS formatting, error handling, and AWS integration is all done. Your friend just needs to make HTTP requests from their IVR code!

## 🔗 Quick Reference

**API Endpoints after deployment:**
- Email: `POST /email`
- SMS: `POST /sms/send` 
- Bulk SMS: `POST /sms/bulk`
- OTP Email: `POST /templated-email/otp`
- Status checks: `GET /email/status`, `GET /sms/status`

**Support:** Check `integration_docs/README.md` for complete API documentation and advanced examples.