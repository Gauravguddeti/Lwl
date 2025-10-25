# 📧📱 Email & SMS API Package for IVR Integration

**Production-ready email and SMS services extracted from working system, packaged as clean REST APIs for easy integration into your friend's IVR system.**

## 🎯 What This Package Provides

✅ **Working Email Services**
- SMTP (Gmail) 
- SES Custom Domain (f5universe.com)
- SES Subdomain (mail.futuristic5.com)
- File attachments support

✅ **Working SMS Services**  
- Amazon SNS integration
- Single and bulk SMS
- International phone numbers
- Sandbox mode for testing

✅ **Professional Email Templates**
- Account signup emails
- OTP verification emails  
- Password reset emails
- Welcome pack with PDF generation
- Order confirmation emails

✅ **Ready-to-Deploy APIs**
- AWS Lambda functions
- REST endpoints with CORS
- Comprehensive error handling
- Environment configuration
- Deployment automation

## 🚀 Quick Deployment

```bash
# 1. Install dependencies
npm install
pip install -r requirements.txt

# 2. Configure environment  
cp .env.template .env
# Edit .env with your AWS credentials

# 3. Deploy to AWS
npm run deploy

# 4. Get your API endpoints
# Email: https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/email
# SMS: https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/sms
# Templates: https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/templated-email
```

## 📁 Package Structure

```
email_sms_api_package/
├── services/                    # Core business logic
│   ├── email_service.py        # Email sending (SMTP, SES)
│   ├── sms_service.py          # SMS via Amazon SNS
│   └── templated_email_service.py # Professional email templates
├── api/                        # AWS Lambda handlers
│   ├── email_handler.py        # Email API endpoints
│   ├── sms_handler.py          # SMS API endpoints  
│   └── templated_email_handler.py # Template API endpoints
├── config/                     # Configuration management
│   └── settings.py             # Environment & settings
├── integration_docs/           # Documentation for your friend
│   ├── README.md              # Complete API documentation
│   └── QUICK_START.md         # 10-minute setup guide
├── serverless.yml              # AWS deployment configuration
├── requirements.txt            # Python dependencies
├── package.json               # Node.js & deployment scripts
├── .env.template              # Environment configuration template
└── test_package.py            # Test suite
```

## 🧪 Test Before Deployment

```bash
# Run the test suite
python test_package.py
```

## 📚 Documentation

- **[QUICK_START.md](integration_docs/QUICK_START.md)** - 10-minute setup guide for your friend
- **[README.md](integration_docs/README.md)** - Complete API documentation with examples

## 🔧 Configuration

Required environment variables in `.env`:

```bash
# AWS Configuration (Required)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-west-2

# Email Configuration
SES_SENDER_EMAIL=support@f5universe.com
EMAIL_USERNAME=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password

# SMS Configuration
SMS_SENDER_ID=IVR
SMS_SANDBOX_MODE=true
```

## 📞 IVR Integration Example

```python
import requests

class IVRNotifications:
    def __init__(self, api_base_url):
        self.base_url = api_base_url
    
    def send_otp_sms(self, phone, otp):
        response = requests.post(f"{self.base_url}/sms/send", json={
            "phone_number": phone,
            "message": f"Your OTP is {otp}"
        })
        return response.json()
    
    def send_otp_email(self, email, username, otp):
        response = requests.post(f"{self.base_url}/templated-email/otp", json={
            "to": email,
            "username": username,
            "otp_code": otp,
            "expiry_minutes": 10
        })
        return response.json()

# Usage in IVR system
notifications = IVRNotifications("https://your-api-id.execute-api.us-west-2.amazonaws.com/dev")

# Send OTP during customer verification
otp = "123456"
notifications.send_otp_sms("+1234567890", otp)
notifications.send_otp_email("customer@example.com", "John Doe", otp)
```

## 🌟 Key Features

- **Battle-tested**: Extracted from production system
- **Scalable**: AWS Lambda auto-scales based on demand
- **Reliable**: Comprehensive error handling and logging
- **Easy Integration**: Simple REST API calls from any language
- **Well-documented**: Complete examples for every use case
- **Cost-effective**: Pay only for what you use
- **Secure**: AWS IAM roles with minimal permissions

## 🛡️ Security & Reliability

- Environment-based configuration (no hardcoded secrets)
- AWS IAM roles with least-privilege access
- Input validation and sanitization
- Comprehensive error handling
- CloudWatch logging for monitoring
- CORS support for web integration

## 📊 API Endpoints Summary

### Email API
- `POST /email` - Send email (SMTP/SES)
- `GET /email/status` - Service health check

### SMS API  
- `POST /sms/send` - Send single SMS
- `POST /sms/bulk` - Send bulk SMS
- `POST /sms/sandbox` - Add test phone number
- `GET /sms/status` - Service health check

### Templated Email API
- `POST /templated-email/otp` - Send OTP email
- `POST /templated-email/signup` - Send signup email
- `POST /templated-email/password-reset` - Send password reset
- `POST /templated-email/welcome` - Send welcome pack
- `POST /templated-email/order` - Send order confirmation
- `GET /templated-email/status` - Service health check

## 🤝 For Your Friend (IVR Developer)

This package solves your email and SMS problems:

1. **No need to debug broken code** - Use these working APIs
2. **No complex setup** - Deploy in 10 minutes
3. **Professional templates** - Beautiful emails out of the box  
4. **Scalable infrastructure** - AWS handles the heavy lifting
5. **Complete documentation** - Examples for every use case

## 🎉 Ready to Deploy!

This package is production-ready and contains everything needed for email and SMS integration into an IVR system. Your friend can focus on IVR logic while these APIs handle all communication needs.

---

**Package extracted from working production system and prepared for IVR integration. No assembly required - just deploy and use!**