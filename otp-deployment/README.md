# OTP API Service - AWS Lambda Deployment

A production-ready OTP (One-Time Password) API service built for AWS Lambda, designed for IVR system integration. This service provides REST API endpoints for sending and verifying OTPs using Amazon SNS.

## 🚀 Quick Start

### Choose Your Deployment Method

#### 🎯 **Method 1: AWS Console (No CLI Required) - RECOMMENDED**
**Easiest option - just use AWS web console!**

1. **Create deployment package**:
   ```powershell
   cd otp-deployment
   .\create-deployment-package.ps1
   ```

2. **Follow the step-by-step guide**: [AWS_CONSOLE_DEPLOYMENT.md](AWS_CONSOLE_DEPLOYMENT.md)

3. **Or use ZIP upload method**: [ZIP_DEPLOYMENT.md](ZIP_DEPLOYMENT.md)

#### 🎯 **Method 2: CloudFormation (No CLI Required)**
**One-click deployment using AWS CloudFormation!**

1. **Create deployment package**:
   ```powershell
   cd otp-deployment
   .\create-deployment-package.ps1
   ```

2. **Upload to S3** and deploy using `cloudformation-template.yaml`

3. **Follow guide**: [ZIP_DEPLOYMENT.md](ZIP_DEPLOYMENT.md) (Method 2)

#### 🎯 **Method 3: AWS CLI + Serverless (Advanced)**
**For developers who prefer command-line tools**

**Prerequisites:**
1. **AWS CLI** - [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. **Node.js** (v14 or higher) - [Install Node.js](https://nodejs.org/)
3. **Python 3.12** - [Install Python](https://www.python.org/downloads/)

**Deploy:**
```bash
# Configure AWS CLI
aws configure

# Deploy using PowerShell (Windows)
cd otp-deployment
.\deploy.ps1

# Deploy using Bash (Linux/Mac)
cd otp-deployment
./deploy.sh
```

### Test Your Deployment

```bash
# Test locally
python tests/test_local.py

# Test deployed API (after deployment)
python tests/test_otp_api.py
```

## 📁 Project Structure

```
otp-deployment/
├── src/
│   ├── handler.py              # Main Lambda handler
│   └── services/
│       ├── __init__.py
│       └── otp_service.py      # OTP service implementation
├── tests/
│   ├── test_local.py           # Local testing
│   └── test_otp_api.py         # API testing
├── serverless.yml              # Serverless configuration
├── requirements.txt            # Python dependencies
├── package.json               # Node.js dependencies
├── deploy.ps1                 # Windows deployment script
├── deploy.sh                  # Linux/Mac deployment script
├── README.md                  # This file
├── DEPLOYMENT_GUIDE.md        # Step-by-step guide
├── QUICK_START.md            # Quick start instructions
└── .gitignore                # Git ignore file
```

## 🔧 Configuration

### Environment Variables

The service uses these environment variables:

- `AWS_REGION`: AWS region (default: us-west-2)
- `STAGE`: Deployment stage (default: dev)

### AWS Permissions Required

Your AWS user/role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish",
                "sns:GetSMSAttributes",
                "sns:SetSMSAttributes"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

## 📡 API Endpoints

### Base URL
After deployment, you'll get an API Gateway URL like:
```
https://abc123def4.execute-api.us-west-2.amazonaws.com/dev
```

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/otp/status` | Check service status |
| `GET` | `/otp/status/{otp_id}` | Check specific OTP status |
| `POST` | `/otp/send` | Send OTP |
| `POST` | `/otp/verify` | Verify OTP |
| `OPTIONS` | `/otp/*` | CORS preflight |

### Request Examples

#### Send OTP
```bash
curl -X POST https://your-api-url/otp/send \
  -H "Content-Type: application/json" \
  -d '{
    "mobile": "+1234567890",
    "purpose": "login",
    "sender_id": "EDUOTP"
  }'
```

#### Verify OTP
```bash
curl -X POST https://your-api-url/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "otp_id": "otp_1234567890",
    "otp_code": "123456",
    "mobile": "+1234567890"
  }'
```

#### Check Service Status
```bash
curl https://your-api-url/otp/status
```

## 🧪 Testing

### Local Testing
```bash
python tests/test_local.py
```

### API Testing
```bash
# Set your API URL
export OTP_API_URL="https://your-api-gateway-url.amazonaws.com/dev"

# Run tests
python tests/test_otp_api.py
```

### Manual Testing with curl

```bash
# Health check
curl https://your-api-url/otp/status

# Send OTP
curl -X POST https://your-api-url/otp/send \
  -H "Content-Type: application/json" \
  -d '{"mobile": "+1234567890", "purpose": "login"}'
```

## 🔍 Monitoring

### CloudWatch Logs
```bash
# View logs
serverless logs -f otpHandler

# Or using the deployment script
.\deploy.ps1 -Logs
```

### CloudWatch Metrics
Monitor these metrics in AWS CloudWatch:
- Lambda invocations
- Lambda errors
- Lambda duration
- SNS delivery success/failure

## 🚨 Troubleshooting

### Common Issues

1. **AWS Credentials Not Configured**
   ```bash
   aws configure
   ```

2. **OTP Not Sending**
   - Check if you're in SMS sandbox mode
   - Verify phone numbers are verified in sandbox
   - Check CloudWatch logs for errors

3. **CORS Issues**
   - The service includes CORS headers
   - Make sure to handle preflight OPTIONS requests

4. **Rate Limiting**
   - Default rate limit: 5 OTP requests per hour per mobile
   - OTP expiry: 10 minutes
   - OTP length: 6 digits

### Debug Commands

```bash
# Check deployment status
serverless info

# View function logs
serverless logs -f otpHandler --tail

# Remove service
serverless remove
```

## 🔒 Security Considerations

1. **API Gateway Authentication**: Consider adding API keys or JWT authentication
2. **Rate Limiting**: Implement API Gateway throttling for production
3. **Input Validation**: The service validates all inputs
4. **CORS**: Configured for web integration
5. **OTP Security**: OTPs expire in 10 minutes and are 6 digits

## 💰 Cost Optimization

1. **Memory**: Set to 512MB (adjust based on usage)
2. **Timeout**: Set to 30 seconds (adjust based on needs)
3. **Log Retention**: Set to 14 days (adjust as needed)
4. **SMS Costs**: Monitor SNS usage and costs

## 🚀 Production Deployment

### 1. Deploy to Production Stage
```bash
serverless deploy --stage prod
```

### 2. Configure Custom Domain (Optional)
```yaml
# Add to serverless.yml
custom:
  customDomain:
    domainName: api.yourdomain.com
    basePath: otp
    stage: prod
```

### 3. Set Up Monitoring
- Configure CloudWatch alarms
- Set up SNS notifications for errors
- Monitor costs and usage

## 📞 IVR Integration

### Example Integration Code

```python
import requests

class IVROTPIntegration:
    def __init__(self, api_url):
        self.api_url = api_url
    
    def send_otp(self, mobile, purpose='login'):
        response = requests.post(
            f"{self.api_url}/otp/send",
            json={
                "mobile": mobile,
                "purpose": purpose,
                "sender_id": "IVR"
            }
        )
        return response.json()
    
    def verify_otp(self, otp_id, otp_code, mobile):
        response = requests.post(
            f"{self.api_url}/otp/verify",
            json={
                "otp_id": otp_id,
                "otp_code": otp_code,
                "mobile": mobile
            }
        )
        return response.json()
```

## 📋 Deployment Checklist

- [ ] AWS CLI configured
- [ ] Node.js installed
- [ ] Python 3.12 installed
- [ ] Service deployed successfully
- [ ] Health check passes
- [ ] Test OTP sent successfully
- [ ] CloudWatch logs accessible
- [ ] CORS working for web integration
- [ ] IVR system integrated
- [ ] Monitoring configured

## 🆘 Support

If you encounter issues:

1. Check CloudWatch logs
2. Verify AWS permissions
3. Test locally first
4. Check the troubleshooting section above

## 📄 License

MIT License - See LICENSE file for details
