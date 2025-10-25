# Email & SMS API Package - Integration Guide

## 📧📱 Clean APIs for IVR Integration

This package contains working email and SMS services extracted from a production system and packaged as clean APIs for easy integration into your IVR system.

## 🚀 Quick Start

### 1. Setup and Deployment

```bash
# Clone/copy the package
cd email_sms_api_package

# Install dependencies
npm install
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your AWS credentials and settings

# Deploy to AWS
npm run deploy
```

### 2. Get Your API Endpoints

After deployment, you'll get endpoints like:
```
https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/email
https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/sms
https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/templated-email
```

## 📡 API Reference

### Email API

#### Send Email
```http
POST /email
Content-Type: application/json

{
  "to": "user@example.com",
  "subject": "Test Email",
  "body": "Hello from IVR system!",
  "method": "ses_custom",
  "attachments": [
    {
      "filename": "document.pdf",
      "content": "base64_encoded_content",
      "mimetype": "application/pdf"
    }
  ]
}
```

**Methods Available:**
- `smtp` - Gmail SMTP
- `ses_custom` - SES with custom domain (f5universe.com)
- `ses_subdomain` - SES with subdomain (mail.futuristic5.com)

#### Get Email Status
```http
GET /email/status
```

### SMS API

#### Send Single SMS
```http
POST /sms/send
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "message": "Your OTP is 123456"
}
```

#### Send Bulk SMS
```http
POST /sms/bulk
Content-Type: application/json

{
  "phone_numbers": ["+1234567890", "+0987654321"],
  "message": "Bulk message from IVR system"
}
```

#### Add Sandbox Number (for testing)
```http
POST /sms/sandbox
Content-Type: application/json

{
  "phone_number": "+1234567890"
}
```

### Templated Email API

#### Send Account Signup Email
```http
POST /templated-email/signup
Content-Type: application/json

{
  "to": "newuser@example.com",
  "username": "John Doe",
  "activation_link": "https://yourapp.com/activate/token123"
}
```

#### Send OTP Email
```http
POST /templated-email/otp
Content-Type: application/json

{
  "to": "user@example.com",
  "username": "John Doe",
  "otp_code": "123456",
  "expiry_minutes": 10
}
```

#### Send Password Reset Email
```http
POST /templated-email/password-reset
Content-Type: application/json

{
  "to": "user@example.com",
  "username": "John Doe",
  "reset_link": "https://yourapp.com/reset/token123"
}
```

#### Send Welcome Pack with PDF
```http
POST /templated-email/welcome
Content-Type: application/json

{
  "to": "newuser@example.com",
  "username": "John Doe",
  "include_pdf": true
}
```

#### Send Order Confirmation
```http
POST /templated-email/order
Content-Type: application/json

{
  "to": "customer@example.com",
  "username": "John Doe",
  "order_id": "ORD-12345",
  "order_total": "$99.99",
  "items": [
    {"name": "Product 1", "quantity": 2, "price": "$49.99"}
  ]
}
```

## 🔗 IVR Integration Examples

### Python Integration (for your friend's IVR)

```python
import requests
import json

class EmailSMSClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}
    
    def send_email(self, to, subject, body, method='ses_custom'):
        """Send email via the API"""
        url = f"{self.base_url}/email"
        data = {
            "to": to,
            "subject": subject,
            "body": body,
            "method": method
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()
    
    def send_sms(self, phone, message):
        """Send SMS via the API"""
        url = f"{self.base_url}/sms/send"
        data = {
            "phone_number": phone,
            "message": message
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()
    
    def send_otp_email(self, email, username, otp_code):
        """Send OTP email using template"""
        url = f"{self.base_url}/templated-email/otp"
        data = {
            "to": email,
            "username": username,
            "otp_code": otp_code,
            "expiry_minutes": 10
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

# Usage in IVR system
client = EmailSMSClient("https://your-api-id.execute-api.us-west-2.amazonaws.com/dev")

# Send OTP via SMS
sms_result = client.send_sms("+1234567890", "Your OTP is 123456")

# Send OTP via email
email_result = client.send_otp_email("user@example.com", "John Doe", "123456")

# Send confirmation email
confirmation = client.send_email(
    "user@example.com",
    "Call Completed",
    "Thank you for using our IVR system. Your request has been processed."
)
```

### JavaScript/Node.js Integration

```javascript
class EmailSMSClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async sendEmail(to, subject, body, method = 'ses_custom') {
        const response = await fetch(`${this.baseUrl}/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ to, subject, body, method })
        });
        return response.json();
    }
    
    async sendSMS(phoneNumber, message) {
        const response = await fetch(`${this.baseUrl}/sms/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone_number: phoneNumber, message })
        });
        return response.json();
    }
    
    async sendOTPEmail(email, username, otpCode) {
        const response = await fetch(`${this.baseUrl}/templated-email/otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to: email,
                username: username,
                otp_code: otpCode,
                expiry_minutes: 10
            })
        });
        return response.json();
    }
}

// Usage
const client = new EmailSMSClient('https://your-api-id.execute-api.us-west-2.amazonaws.com/dev');

// Send notifications from IVR
await client.sendSMS('+1234567890', 'Your call has been completed');
await client.sendEmail('user@example.com', 'IVR Summary', 'Call details...');
```

## 🔧 Configuration

### Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
# AWS credentials (required)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-west-2

# Email settings
SES_SENDER_EMAIL=support@f5universe.com
EMAIL_USERNAME=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password

# SMS settings
SMS_SENDER_ID=IVR
SMS_SANDBOX_MODE=true  # Set to false for production
```

### Service Features

Each service can be enabled/disabled:
- `EMAIL_ENABLED=true` - Basic email sending
- `SMS_ENABLED=true` - SMS via Amazon SNS
- `TEMPLATED_EMAIL_ENABLED=true` - Professional email templates

## 🧪 Testing

### Test Email Service
```bash
curl -X POST https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test from IVR",
    "body": "This is a test email",
    "method": "ses_custom"
  }'
```

### Test SMS Service
```bash
curl -X POST https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Test SMS from IVR"
  }'
```

### Test Templated Email
```bash
curl -X POST https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/templated-email/otp \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "username": "Test User",
    "otp_code": "123456",
    "expiry_minutes": 10
  }'
```

## 📞 IVR Integration Patterns

### Pattern 1: OTP Verification
```python
# In your IVR system
def handle_otp_verification(phone_number, email):
    otp = generate_otp()  # Your OTP generation logic
    
    # Send OTP via SMS
    sms_result = client.send_sms(phone_number, f"Your OTP is {otp}")
    
    # Send OTP via email as backup
    email_result = client.send_otp_email(email, "User", otp)
    
    return {"otp": otp, "sms_sent": sms_result, "email_sent": email_result}
```

### Pattern 2: Call Completion Notification
```python
def notify_call_completion(customer_info, call_summary):
    # Send SMS notification
    sms_message = f"Call completed. Reference: {call_summary['reference']}"
    client.send_sms(customer_info['phone'], sms_message)
    
    # Send detailed email
    email_body = f"""
    Dear {customer_info['name']},
    
    Your call has been completed successfully.
    
    Call Details:
    - Reference: {call_summary['reference']}
    - Duration: {call_summary['duration']}
    - Status: {call_summary['status']}
    
    Thank you for using our service.
    """
    
    client.send_email(
        customer_info['email'],
        "Call Completion Summary",
        email_body
    )
```

### Pattern 3: Account Registration via IVR
```python
def handle_account_registration(user_data):
    # Create account in your system
    account = create_user_account(user_data)
    
    # Send welcome email with account details
    result = client.send_templated_email(
        'signup',
        user_data['email'],
        {
            'username': user_data['name'],
            'activation_link': f"https://yourapp.com/activate/{account['token']}"
        }
    )
    
    # Send SMS confirmation
    client.send_sms(
        user_data['phone'],
        f"Welcome {user_data['name']}! Your account has been created. Check your email for activation."
    )
```

## 🚨 Error Handling

All APIs return consistent error responses:

```json
{
  "success": false,
  "error": "Error description",
  "error_code": "EMAIL_SEND_FAILED",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

Common error codes:
- `EMAIL_SEND_FAILED` - Email sending failed
- `SMS_SEND_FAILED` - SMS sending failed
- `INVALID_PHONE_NUMBER` - Phone number format invalid
- `INVALID_EMAIL` - Email format invalid
- `SERVICE_DISABLED` - Service is disabled in configuration
- `AWS_CREDENTIALS_ERROR` - AWS authentication failed

## 📊 Monitoring

### Health Check Endpoints
- `GET /email/status` - Email service health
- `GET /sms/status` - SMS service health
- `GET /templated-email/status` - Templated email service health

### CloudWatch Logs
Monitor your APIs in AWS CloudWatch:
- Function: `email-sms-api-package-dev-email-api`
- Function: `email-sms-api-package-dev-sms-api`
- Function: `email-sms-api-package-dev-templated-email-api`

## 🛡️ Security

- All endpoints support CORS for web integration
- AWS IAM roles with minimal required permissions
- Environment variables for sensitive configuration
- Input validation and sanitization
- Error messages don't leak sensitive information

## 📞 Support

If you need help integrating these APIs into your IVR system:

1. Check the error response for specific error codes
2. Verify your environment configuration
3. Test individual endpoints with curl/Postman
4. Check CloudWatch logs for detailed error information

This package provides battle-tested email and SMS functionality extracted from a working production system, ready for integration into your IVR application!