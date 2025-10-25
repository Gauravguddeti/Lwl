# 🤖 AI IVR Telecaller System - Complete User Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Interactive Menu Features](#interactive-menu-features)
4. [Email & SMS Services](#email--sms-services)
5. [Database Integration](#database-integration)
6. [Twilio Configuration](#twilio-configuration)
7. [Python SDK Usage](#python-sdk-usage)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)

---

## 🎯 System Overview

The AI IVR (Interactive Voice Response) Telecaller System is an intelligent calling platform that:

- **Makes automated AI-powered phone calls** using OpenAI's Realtime API
- **Sends emails** via AWS SES with custom domain support
- **Sends SMS messages** via AWS SNS
- **Manages partner data** from PostgreSQL database
- **Provides timezone-aware greetings** for scheduled calls
- **Records and transcribes** all conversations
- **Supports both local and AWS Lambda deployment**

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                   AI IVR System                             │
├─────────────────────────────────────────────────────────────┤
│  Entry Point: main_modular.py                              │
│  Core System: ai_telecaller/core/telecaller.py             │
│  Flask App: app/flask_app.py                               │
│  Email Service: app/services/email_service.py              │
│  SMS Service: app/services/sms_service.py                  │
│  Database: app/database/postgres_data_access.py            │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  Twilio API    │  │   OpenAI API     │  │  PostgreSQL DB  │
│  (Voice Calls) │  │  (AI Responses)  │  │  (Partner Data) │
└────────────────┘  └──────────────────┘  └─────────────────┘
         ↓                    ↓                    ↓
┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│   AWS SES      │  │    AWS SNS       │  │     Ngrok       │
│   (Emails)     │  │    (SMS)         │  │  (Webhooks)     │
└────────────────┘  └──────────────────┘  └─────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites

1. **Python 3.9+** installed
2. **Ngrok** installed and configured
3. **Environment variables** configured in `.env` file
4. **Twilio account** with phone number
5. **AWS account** with SES and SNS access
6. **OpenAI API key**

### Installation

```powershell
# Navigate to project directory
cd "d:\intern\AI IVR\Telecaller-ai\Lwl-v2-integrated\Lwl-v2-ivrnotworking\Lwl-v1-ivrnotworking\Lwl"

# Install dependencies
pip install -r requirements.txt
```

### Running the System

```powershell
# Start the AI IVR system
python main_modular.py
```

### What Happens When You Run It?

1. ✅ **Environment loads** from `.env` file
2. ✅ **Database connects** to PostgreSQL (retrieves partners)
3. ✅ **Email service initializes** (AWS SES)
4. ✅ **SMS service initializes** (AWS SNS)
5. ✅ **Ngrok tunnel starts** (creates public webhook URL)
6. ✅ **Flask server starts** on port 3000
7. ✅ **Interactive menu displays** with calling options

---

##  Interactive Menu Features

### Main Menu Options

When you run the system locally, you get an interactive menu:

```
============================================================
CALLING OPTIONS:
============================================================
1. 📞 Call specific partner (enter partner number)
2. 📞 Call ALL partners simultaneously
3. 🔄 Refresh partner list from database
4. 📊 View call storage statistics

============================================================
7. 🔍 Demonstrate getcallstobedone function LIVE
8. 📞 Call scheduled contacts with timezone greetings
9. 🧪 Test timezone greeting system

============================================================
10. 🚪 Exit system
============================================================
```

### Menu Option Details

#### Option 1: Call Specific Partner
- Select from list of active partners in database
- AI makes personalized call using partner data
- Conversation uses OpenAI Realtime API
- Call is recorded and transcribed

#### Option 2: Call ALL Partners
- Initiates calls to all active partners simultaneously
- Each call runs in separate thread
- All conversations logged to database

#### Option 3: Refresh Partner List
- Reloads partner data from PostgreSQL
- Updates contact information
- Shows count of active partners

#### Option 4: View Call Statistics
- Shows total calls made
- Displays recordings saved
- Shows transcriptions generated
- Storage usage information

#### Option 7: Demonstrate getcallstobedone
- Shows LIVE query of scheduled calls
- Filters by timezone and scheduling rules
- Demonstrates database integration

#### Option 8: Call Scheduled Contacts
- Calls only scheduled partners
- Uses timezone-aware greeting system
- Respects call scheduling preferences

#### Option 9: Test Timezone Greetings
- Interactive test of timezone system
- Enter phone number and timezone
- Hear appropriate greeting (morning/afternoon/evening)

#### Option 10: Exit System
- Gracefully shuts down Flask server
- Closes ngrok tunnel
- Saves all call data
- Exits cleanly

---

## 📧 Email & SMS Services

### Email Service Features

**Implementation**: `app/services/email_service.py`

#### Supported Email Types:

1. **Plain Text Emails** - Simple text-based messages
2. **HTML Emails** - Rich formatted content
3. **Templated Emails** - Pre-designed email templates
4. **Bulk Emails** - Send to multiple recipients

#### Email Templates Available:

- **Login Verification** - OTP/verification codes
- **Registration Confirmation** - Welcome emails
- **Password Reset** - Secure reset links
- **Custom Templates** - Define your own

#### Email Configuration:

```python
# Using AWS SES with custom domain
EMAIL_SERVICE_TYPE=ses_custom_domain
SES_SENDER_EMAIL=noreply@yourdomain.com
SES_CUSTOM_DOMAIN=yourdomain.com
SES_SUBDOMAIN=mail

# Using SMTP (alternative)
EMAIL_SERVICE_TYPE=smtp
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### SMS Service Features

**Implementation**: `app/services/sms_service.py`

#### Supported SMS Types:

1. **Single SMS** - One message to one recipient
2. **Bulk SMS** - Multiple messages to multiple recipients
3. **Scheduled SMS** - Time-delayed sending

#### SMS Configuration:

```python
SMS_SENDER_ID=EduServices  # Shows as sender name
SMS_SANDBOX_MODE=false      # Set to true for testing
AWS_REGION=us-west-2        # SNS region
```

#### SMS Limitations:

- Maximum 160 characters per SMS
- Sender ID support varies by country
- AWS SNS rate limits apply

---

## 🗄️ Database Integration

### Database Details

- **Type**: PostgreSQL
- **Host**: `lwl-pg-us-2.czq8mh1i8p1n.us-west-2.rds.amazonaws.com`
- **Database**: `lwl_pg_us_2`
- **Port**: 5432
- **Schema**: 32 tables (see `LWL_DATABASE_ANALYSIS_AND_RECOMMENDATIONS.md`)

### Key Tables Used

#### 1. `partners` Table
- Stores partner organization information
- Contains contact person details
- Tracks active/inactive status

#### 2. `scheduled_jobs` Table (Recommended)
- Stores scheduled call information
- Contains timezone preferences
- Tracks call scheduling rules

#### 3. `ivr_call_sessions` Table (Recommended)
- Logs all IVR call sessions
- Stores call metadata and outcomes
- Links to conversation transcripts

### Database Access

```python
from app.database.postgres_data_access import PostgresDataAccess

# Initialize database
db = PostgresDataAccess()

# Get active partners
partners = db.get_all_active_partners()

# Get scheduled calls
scheduled = db.get_scheduled_calls_to_be_done()
```

---

## 📞 Twilio Configuration

### Setup Steps

1. **Get Twilio Credentials**
   - Sign up at https://www.twilio.com
   - Get Account SID and Auth Token
   - Purchase a phone number

2. **Configure Webhook URLs**

   When you run the system locally, it will create an ngrok URL like:
   ```
   https://30a54433f5bf.ngrok-free.app
   ```

   Configure this URL in your Twilio console:
   - Go to Phone Numbers → Active Numbers
   - Select your phone number
   - Under "Voice & Fax", set the Voice URL to your ngrok webhook
   - Under "Voice Configuration", set the Status Callback URL

   **Note**: The ngrok URL changes each time you restart. For production, use AWS Lambda endpoints (see `AWS_LAMBDA_ENDPOINTS.md`).

3. **Update .env File**
   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=+1234567890
   ```

### Twilio Call Flow

```
1. System initiates call via Twilio API
   ↓
2. Twilio dials recipient
   ↓
3. On answer, Twilio requests TwiML from webhook
   ↓
4. System returns TwiML with WebSocket connection
   ↓
5. OpenAI Realtime API handles conversation
   ↓
6. Call completes, recording saved
   ↓
7. Twilio posts status to callback URL
   ↓
8. System logs call outcome to database
```

---

## 📚 Python SDK Usage

#### Making a Call

```python
from ai_telecaller.core.telecaller import create_system

# Create system instance
system = create_system()

# Start services
system.start_ngrok()
system.start_flask_server()

# Make a call
result = system.call_partner(
    partner_id=1,
    phone_number="+1234567890",
    partner_name="ABC Company"
)

print(f"Call Status: {result['status']}")
print(f"Call SID: {result['call_sid']}")
```

#### Sending Email

```python
from app.services.email_service import EmailService

# Initialize service
email_service = EmailService()

# Send email
result = email_service.send_email(
    to_email="recipient@example.com",
    subject="Test Email",
    body="This is a test message",
    is_html=False
)

if result['success']:
    print(f"Email sent! Message ID: {result['message_id']}")
```

#### Sending SMS

```python
from app.services.sms_service import SMSService

# Initialize service
sms_service = SMSService()

# Send SMS
result = sms_service.send_sms(
    phone_number="+1234567890",
    message="Test SMS from AI IVR"
)

if result['success']:
    print(f"SMS sent! Message ID: {result['message_id']}")
```

#### Getting Scheduled Calls

```python
from app.database.postgres_data_access import PostgresDataAccess

# Initialize database
db = PostgresDataAccess()

# Get calls to be made
calls = db.get_scheduled_calls_to_be_done()

for call in calls:
    print(f"Call Partner: {call['partner_name']}")
    print(f"Phone: {call['phone_number']}")
    print(f"Timezone: {call['timezone']}")
    print(f"Greeting: {call['greeting']}")
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Module not found" errors

```powershell
# Solution: Install all dependencies
pip install -r requirements.txt
```

#### 2. Ngrok tunnel not starting

```powershell
# Solution: Check if ngrok is installed
ngrok version

# Install ngrok if needed
# Download from: https://ngrok.com/download
```

#### 3. Database connection fails

```
Error: Could not connect to PostgreSQL
```

**Solution**: Check `.env` file:
- Verify `POSTGRES_HOST` is correct
- Ensure `POSTGRES_PASSWORD` is accurate
- Check network connectivity to AWS RDS

#### 4. Email not sending

```
Error: SES sender email not verified
```

**Solution**: Verify email in AWS SES:
1. Go to AWS SES Console
2. Navigate to "Verified Identities"
3. Add and verify your sender email
4. If in sandbox mode, verify recipient emails too

#### 5. SMS not sending

```
Error: Phone number not verified
```

**Solution**: 
- If `SMS_SANDBOX_MODE=true`, verify recipient numbers in AWS SNS
- Set `SMS_SANDBOX_MODE=false` for production
- Check AWS SNS spending limits

#### 6. Twilio webhook errors

```
Error: Webhook URL unreachable
```

**Solution**:
- Ensure ngrok tunnel is running
- Update Twilio console with current ngrok URL
- Check firewall settings

#### 7. OpenAI API errors

```
Error: Invalid API key
```

**Solution**:
- Verify `OPENAI_API_KEY` in `.env`
- Check API key validity at https://platform.openai.com
- Ensure billing is set up

### Debug Mode

Enable debug logging:

```bash
# In .env file
DEBUG=true
```

This will show:
- Detailed API responses
- Database query logs
- Webhook payloads
- Error stack traces

### Log Files

System logs are stored in:
- **Call Recordings**: `./call_recordings/`
- **Call Transcriptions**: `./call_transcriptions/`
- **Sentiment Analysis**: `./call_transcriptions/sentiment_analysis/`

### Getting Help

1. Check the logs in terminal output
2. Review `LWL_DATABASE_ANALYSIS_AND_RECOMMENDATIONS.md` for database issues
3. Review `AWS_LAMBDA_ENDPOINTS.md` for production API endpoints
4. Check AWS CloudWatch logs for Lambda errors (if deployed)

---

## ⚙️ Advanced Configuration

### Environment Variables Reference

The system uses the following environment variables (configured in `.env` file):

#### Database Configuration
```bash
POSTGRES_HOST=lwl-pg-us-2.czq8mh1i8p1n.us-west-2.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DB=lwl_pg_us_2
POSTGRES_USER=lwl_db_user
POSTGRES_PASSWORD=Lwl2024pass!
```

#### AWS Configuration
```bash
AWS_REGION=us-west-2
SES_SENDER_EMAIL=noreply@yourdomain.com
SES_CUSTOM_DOMAIN=yourdomain.com
SMS_SENDER_ID=EduServices
```

#### Twilio Configuration
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

#### OpenAI Configuration
```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_REALTIME_MODEL=gpt-4o-mini-realtime-preview-2024-12-17
OPENAI_REALTIME_VOICE=alloy  # Options: alloy, echo, fable, onyx, nova, shimmer
AI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1000
```

### Voice Configuration

You can customize the AI voice by changing the `OPENAI_REALTIME_VOICE` variable:

- **alloy** - Neutral and balanced (default)
- **echo** - Clear and articulate
- **fable** - Warm and expressive
- **onyx** - Deep and authoritative
- **nova** - Energetic and friendly
- **shimmer** - Soft and gentle

### Call Scheduling

The system supports timezone-aware scheduling. Configure call schedules in the database:

```sql
-- Example: Schedule calls for partners in different timezones
INSERT INTO scheduled_jobs (partner_id, timezone, preferred_time)
VALUES (1, 'America/New_York', '09:00:00');
```

### Monitoring & Analytics

#### View Call Statistics

Use **Option 4** in the interactive menu to view:
- Total calls made
- Recordings saved
- Transcriptions generated
- Storage usage

#### Call Recordings Location

All call data is stored locally in:
- **Recordings**: `./call_recordings/`
- **Transcriptions**: `./call_transcriptions/`
- **Sentiment Analysis**: `./call_transcriptions/sentiment_analysis/`

### Performance Tuning

#### Adjust AI Response Parameters

Modify in `.env`:
```bash
AI_TEMPERATURE=0.7   # Lower = more focused, Higher = more creative (0.0-1.0)
AI_MAX_TOKENS=1000   # Maximum response length
```

#### Database Connection Pooling

The system automatically manages database connections. For high-volume usage, consider:
- Increasing connection pool size in `postgres_data_access.py`
- Using read replicas for analytics queries

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** to version control
2. **Rotate API keys** regularly (OpenAI, Twilio, AWS)
3. **Use IAM roles** for Lambda functions (not access keys)
4. **Enable AWS CloudTrail** for audit logging
5. **Verify Twilio webhook signatures** to prevent spoofing
6. **Use HTTPS** for all webhook URLs
7. **Limit database user permissions** (read-only where possible)
8. **Enable SES sandbox mode** for testing

---

## 📝 System Requirements

### Software Requirements

- Python 3.9 or higher
- Node.js 14+ (for Serverless Framework)
- Ngrok (for local development)
- PostgreSQL client tools (optional)

### AWS Services Required

- AWS Lambda
- AWS API Gateway
- AWS SES (Simple Email Service)
- AWS SNS (Simple Notification Service)
- AWS RDS (PostgreSQL database)
- AWS CloudWatch (logging)
- AWS IAM (permissions)

### Python Packages

See `requirements.txt` for full list. Key packages:
- `flask` - Web framework
- `twilio` - Twilio SDK
- `langchain` - LangGraph for conversation flow
- `openai` - OpenAI API client
- `psycopg2-binary` - PostgreSQL adapter
- `boto3` - AWS SDK
- `websocket-client` - WebSocket support
- `pytz` - Timezone handling

---

## 📞 Support

For technical support:
1. Check this documentation
2. Review error logs in terminal
3. Check AWS CloudWatch logs
4. Review database schema documentation

---

## 📄 Related Documentation

- `AWS_LAMBDA_ENDPOINTS.md` - AWS Lambda API endpoints and deployment info
- `LWL_DATABASE_ANALYSIS_AND_RECOMMENDATIONS.md` - Database schema and optimization
- `README.md` - Project overview
- `serverless.yml` - AWS Lambda deployment configuration
- `requirements.txt` - Python dependencies

---

## 🎉 Quick Reference Card

### Start the AI IVR System
```powershell
python main_modular.py
```

### Interactive Menu Options
1. Call specific partner
2. Call all partners
3. Refresh partner list
4. View call statistics
7. Demonstrate scheduled calls
8. Call scheduled contacts
9. Test timezone greetings
10. Exit system

### Environment Variables (`.env`)
```bash
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_PHONE_NUMBER=+1...
POSTGRES_HOST=lwl-pg-us-2...
AWS_REGION=us-west-2
```

### Database
```
Host: lwl-pg-us-2.czq8mh1i8p1n.us-west-2.rds.amazonaws.com
Database: lwl_pg_us_2
Port: 5432
```

### Storage Locations
- Call Recordings: `./call_recordings/`
- Transcriptions: `./call_transcriptions/`
- Sentiment Analysis: `./call_transcriptions/sentiment_analysis/`

---

**Last Updated**: October 25, 2025  
**Version**: 1.0  
**System**: AI IVR Telecaller with Email/SMS Integration
