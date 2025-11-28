# Independent Lambda Functions
=============================

This directory contains 7 independent AWS Lambda functions for the AI Telecaller system. Each function is designed to be deployed and used independently.

## 📁 Functions Overview

| Function | Description | Input | Output |
|----------|-------------|-------|--------|
| `send_sms_single.py` | Send single SMS via AWS SNS | `{mobile, message}` | `{status, message_id, cost}` |
| `send_sms_bulk.py` | Send bulk SMS via AWS SNS | `{mobiles[], message}` | `{status, successful, failed, results[]}` |
| `send_email_single.py` | Send single email via AWS SES | `{email, subject, body}` | `{status, message_id, recipient}` |
| `send_email_bulk.py` | Send bulk email via AWS SES | `{emails[], subject, body}` | `{status, successful, failed, results[]}` |
| `ivr_call_student.py` | Make AI voice calls via Twilio | `{student_id, topic, phone}` | `{status, call_sid, student_id}` |
| `schedule_ivr_call.py` | Schedule IVR calls via EventBridge | `{student_id, time, topic, phone}` | `{status, schedule_id, scheduled_time}` |
| `send_otp.py` | Send OTP via SMS | `{mobile, purpose}` | `{status, otp_id, expires_in}` |

## 🚀 Quick Deployment

### Prerequisites

1. **AWS CLI** installed and configured
2. **Python 3.12** runtime
3. **Required AWS services**:
   - SNS (for SMS)
   - SES (for email)
   - EventBridge (for scheduling)
   - Lambda (for execution)

### Environment Variables

Set these environment variables before deployment:

```bash
# Database Configuration
export DB_HOST="your-db-host"
export DB_PORT="5432"
export DB_NAME="lwl_pg_us_2"
export DB_USER="postgres"
export DB_PASSWORD="your-password"

# Twilio Configuration
export TWILIO_ACCOUNT_SID="your-account-sid"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_PHONE_NUMBER="+1234567890"
```

### Deploy All Functions

**Windows (PowerShell):**
```powershell
cd lambdas
.\deploy.ps1
```

**Linux/Mac (Bash):**
```bash
cd lambdas
chmod +x deploy.sh
./deploy.sh
```

### Deploy Individual Function

```bash
# Example: Deploy only SMS single function
aws lambda create-function \
  --function-name ai-telecaller-send-sms-single \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR-ACCOUNT:role/lambda-execution-role \
  --handler send_sms_single.lambda_handler \
  --zip-file fileb://send_sms_single.zip \
  --description "Send single SMS via AWS SNS"
```

## 📋 Database Schema

Create these tables in your PostgreSQL database:

```sql
-- Students table
CREATE TABLE students (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    course VARCHAR(100),
    batch VARCHAR(50),
    fees_due DECIMAL(10,2),
    last_payment_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Call logs table
CREATE TABLE call_logs (
    id SERIAL PRIMARY KEY,
    call_sid VARCHAR(100) UNIQUE,
    student_id VARCHAR(50),
    phone VARCHAR(20),
    topic VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Scheduled calls table
CREATE TABLE scheduled_calls (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(200),
    student_id VARCHAR(50),
    scheduled_time TIMESTAMP,
    topic VARCHAR(50),
    phone VARCHAR(20),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- OTP requests table
CREATE TABLE otp_requests (
    id SERIAL PRIMARY KEY,
    otp_id VARCHAR(100) UNIQUE,
    mobile VARCHAR(20),
    otp_code VARCHAR(10),
    purpose VARCHAR(50),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

### Test Individual Functions

```bash
# Test SMS single
aws lambda invoke \
  --function-name ai-telecaller-send-sms-single \
  --payload '{"mobile":"+911234567890","message":"Test SMS"}' \
  response.json

# Test email single
aws lambda invoke \
  --function-name ai-telecaller-send-email-single \
  --payload '{"email":"test@example.com","subject":"Test","body":"Test email"}' \
  response.json

# Test OTP
aws lambda invoke \
  --function-name ai-telecaller-send-otp \
  --payload '{"mobile":"+911234567890","purpose":"login"}' \
  response.json
```

### Test with API Gateway

If you set up API Gateway endpoints, test with curl:

```bash
# SMS Single
curl -X POST https://your-api-gateway-url/sms/single \
  -H "Content-Type: application/json" \
  -d '{"mobile":"+911234567890","message":"Hello from Lambda!"}'

# Email Single
curl -X POST https://your-api-gateway-url/email/single \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","subject":"Test","body":"Hello from Lambda!"}'
```

## 🔧 Configuration

### AWS SNS Setup

1. **Verify phone numbers** in SNS console
2. **Set up spending limits** to control costs
3. **Configure delivery status logging** for monitoring

### AWS SES Setup

1. **Verify sender email addresses** in SES console
2. **Request production access** if needed
3. **Set up bounce/complaint handling**

### Twilio Setup

1. **Purchase a phone number** for outbound calls
2. **Set up webhooks** for call status updates
3. **Configure TwiML** for call handling

## 📊 Monitoring

### CloudWatch Metrics

Each function automatically logs:
- **Execution duration**
- **Memory usage**
- **Error rates**
- **Invocation counts**

### Custom Logs

Functions log:
- **Success/failure status**
- **Input parameters** (sanitized)
- **External service responses**
- **Database operations**

### Alarms

Set up CloudWatch alarms for:
- **High error rates** (>5%)
- **Long execution times** (>25 seconds)
- **Memory usage** (>80% of allocated)

## 🔒 Security

### IAM Permissions

Each function uses minimal required permissions:
- **SNS**: `sns:Publish`
- **SES**: `ses:SendEmail`
- **EventBridge**: `events:PutRule`, `events:PutTargets`
- **Lambda**: `lambda:InvokeFunction` (for scheduling)

### Data Protection

- **Phone numbers** are validated and formatted
- **Email addresses** are validated
- **OTP codes** are hashed in logs
- **Database credentials** are environment variables

## 🚨 Troubleshooting

### Common Issues

1. **"Invalid phone number format"**
   - Ensure phone numbers are in E.164 format (+1234567890)
   - Check for proper country codes

2. **"SES email rejected"**
   - Verify sender email in SES console
   - Check if recipient email is valid

3. **"Database connection failed"**
   - Verify database credentials
   - Check VPC configuration if using RDS

4. **"Twilio call failed"**
   - Verify Twilio credentials
   - Check if phone number is valid
   - Ensure sufficient account balance

### Debug Mode

Enable detailed logging by setting environment variable:
```
LOG_LEVEL=DEBUG
```

## 📈 Scaling

### Concurrent Executions

- **Default limit**: 1000 concurrent executions
- **SMS functions**: Can handle high concurrency
- **Email functions**: Limited by SES sending quotas
- **Call functions**: Limited by Twilio account limits

### Cost Optimization

- **Memory allocation**: Start with 256MB, adjust based on usage
- **Timeout settings**: Set appropriate timeouts (30s for most functions)
- **Reserved concurrency**: Use for critical functions
- **Dead letter queues**: Handle failed messages

## 🔄 Updates

### Updating Functions

```bash
# Update function code
aws lambda update-function-code \
  --function-name ai-telecaller-send-sms-single \
  --zip-file fileb://send_sms_single.zip

# Update function configuration
aws lambda update-function-configuration \
  --function-name ai-telecaller-send-sms-single \
  --timeout 60 \
  --memory-size 512
```

### Version Management

```bash
# Publish new version
aws lambda publish-version --function-name ai-telecaller-send-sms-single

# Create alias
aws lambda create-alias \
  --function-name ai-telecaller-send-sms-single \
  --name PROD \
  --function-version 1
```

---

## 📞 Support

For issues or questions:
1. Check CloudWatch logs
2. Review function metrics
3. Verify environment variables
4. Test with sample payloads

**Happy coding! 🚀**
