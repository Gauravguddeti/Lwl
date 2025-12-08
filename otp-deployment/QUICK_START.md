# 🚀 OTP API - Quick Start Guide

## Ready to Deploy? Follow These Steps:

### 1️⃣ **Setup Prerequisites** (5 minutes)
```bash
# Install AWS CLI and configure
aws configure
# Enter your AWS credentials when prompted

# Install Node.js from https://nodejs.org/
# Install Python 3.12 from https://python.org/downloads/
```

### 2️⃣ **Deploy to AWS** (2 minutes)
```powershell
# Windows
cd otp-deployment
.\deploy.ps1

# Linux/Mac
cd otp-deployment
./deploy.sh
```

### 3️⃣ **Test Your API** (1 minute)
```bash
# Test locally
python tests/test_local.py

# Test deployed API (after deployment)
python tests/test_otp_api.py
```

### 4️⃣ **Get Your API URL**
After deployment, you'll see:
```
✅ Deployment successful!
endpoints:
  GET - https://abc123def4.execute-api.us-west-2.amazonaws.com/dev/otp/status
  POST - https://abc123def4.execute-api.us-west-2.amazonaws.com/dev/otp/send
  POST - https://abc123def4.execute-api.us-west-2.amazonaws.com/dev/otp/verify
```

**Copy this URL for your IVR system!**

## 🎯 **What You Get:**

✅ **REST API** for OTP sending and verification  
✅ **6-digit OTP** generation with 10-minute expiry  
✅ **Rate limiting** (5 requests per hour per mobile)  
✅ **Input validation** and error handling  
✅ **CORS enabled** for web integration  
✅ **CloudWatch logging** for monitoring  
✅ **Production-ready** with proper error handling  

## 📞 **IVR Integration Example:**

```python
import requests

def send_otp(mobile, purpose='login'):
    api_url = "https://your-api-gateway-url.amazonaws.com/dev"
    
    response = requests.post(
        f"{api_url}/otp/send",
        json={
            "mobile": mobile,
            "purpose": purpose,
            "sender_id": "IVR"
        }
    )
    
    return response.json()

def verify_otp(otp_id, otp_code, mobile):
    api_url = "https://your-api-gateway-url.amazonaws.com/dev"
    
    response = requests.post(
        f"{api_url}/otp/verify",
        json={
            "otp_id": otp_id,
            "otp_code": otp_code,
            "mobile": mobile
        }
    )
    
    return response.json()
```

## 🆘 **Need Help?**

- **Full Guide**: See `README.md`
- **Quick Reference**: See `DEPLOYMENT_GUIDE.md`
- **Test Issues**: Run `python tests/test_local.py`
- **Deployment Issues**: Check AWS credentials with `aws sts get-caller-identity`

## 📋 **Files Created:**

- `src/handler.py` - Main Lambda function
- `src/services/otp_service.py` - OTP service implementation
- `serverless.yml` - AWS deployment configuration
- `deploy.ps1` / `deploy.sh` - Deployment scripts
- `tests/` - Test suites for local and API testing

**You're all set! 🎉**
