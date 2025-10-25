# 📧 Email & SMS API - Complete Documentation

## 📍 Base URL

```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev
```

---

## 📋 Table of Contents

1. [Email APIs](#email-apis)
   - [Send Single Email](#1-send-single-email)
   - [Send Bulk Emails](#2-send-bulk-emails)
   - [Check Email Status](#3-check-email-status)
2. [SMS APIs](#sms-apis)
   - [Send Single SMS](#1-send-single-sms)
   - [Send Bulk SMS](#2-send-bulk-sms)
   - [Check SMS Status](#3-check-sms-status)
3. [Templated Email APIs](#templated-email-apis)
   - [Send Generic Templated Email](#1-send-generic-templated-email)
   - [Send Login Verification Email](#2-send-login-verification-email)
   - [Send Registration Email](#3-send-registration-email)
   - [Send Custom Template Email](#4-send-custom-template-email)
4. [System Status](#system-status)
5. [Error Codes](#error-codes)

---

## 📧 Email APIs

### 1. Send Single Email

Send a single email using different providers (Custom Domain, Subdomain, or SMTP).

#### Endpoint
```
POST /email
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email
```

---

#### Option A: Custom Domain (f5universe.com)

**Request Body:**
```json
{
  "email_type": "customdomain",
  "sender_email": "support@f5universe.com",
  "to_email": "recipient@example.com",
  "subject": "Your Subject Here",
  "body": "Your email message here",
  "is_html": false
}
```

**Optional Parameters:**
```json
{
  "cc": ["cc1@example.com", "cc2@example.com"],
  "bcc": ["bcc@example.com"],
  "reply_to": "noreply@f5universe.com"
}
```

**cURL Example:**
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email \
  -H "Content-Type: application/json" \
  -d '{
    "email_type": "customdomain",
    "sender_email": "support@f5universe.com",
    "to_email": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email from custom domain",
    "is_html": false
  }'
```

**PowerShell Example:**
```powershell
$body = @{
    email_type = "customdomain"
    sender_email = "support@f5universe.com"
    to_email = "recipient@example.com"
    subject = "Test Email"
    body = "This is a test email"
    is_html = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email" `
  -Method Post -Body $body -ContentType "application/json"
```

**Success Response:**
```json
{
  "success": true,
  "message": "SES Custom Domain email sent to recipient@example.com",
  "message_id": "0101019a1a9d37c9-f7c26988-bbf6-4311-b271-3d216e8a9c2a-000000",
  "provider": "SES Custom Domain (f5universe.com)",
  "recipient": "recipient@example.com"
}
```

---

#### Option B: Subdomain (mail.futuristic5.com)

**Request Body:**
```json
{
  "email_type": "subdomain",
  "sender_email": "noreply@mail.futuristic5.com",
  "to_email": "recipient@example.com",
  "subject": "Your Subject Here",
  "body": "Your email message here",
  "is_html": false
}
```

**cURL Example:**
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email \
  -H "Content-Type: application/json" \
  -d '{
    "email_type": "subdomain",
    "sender_email": "noreply@mail.futuristic5.com",
    "to_email": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email from subdomain",
    "is_html": false
  }'
```

**Success Response:**
```json
{
  "success": true,
  "message": "SES Subdomain email sent to recipient@example.com",
  "message_id": "0101019a1a9d37c9-a1b2c3d4-e5f6-7890-abcd-ef1234567890-000000",
  "provider": "SES Subdomain (mail.futuristic5.com)",
  "recipient": "recipient@example.com"
}
```

---

#### Option C: SMTP (Gmail)

**Request Body:**
```json
{
  "email_type": "smtp",
  "smtp_email": "youremail@gmail.com",
  "smtp_password": "your-app-password",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "to_email": "recipient@example.com",
  "subject": "Your Subject Here",
  "body": "Your email message here",
  "is_html": false
}
```

**cURL Example:**
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email \
  -H "Content-Type: application/json" \
  -d '{
    "email_type": "smtp",
    "smtp_email": "youremail@gmail.com",
    "smtp_password": "your-app-password",
    "to_email": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email via SMTP",
    "is_html": false
  }'
```

**Success Response:**
```json
{
  "success": true,
  "message": "SMTP email sent successfully to recipient@example.com",
  "provider": "SMTP (Gmail)",
  "recipient": "recipient@example.com",
  "attachments_count": 0
}
```

---

#### HTML Email Example

**Request Body:**
```json
{
  "email_type": "customdomain",
  "sender_email": "support@f5universe.com",
  "to_email": "recipient@example.com",
  "subject": "HTML Email Test",
  "body": "<h1>Hello!</h1><p>This is an <strong>HTML</strong> email.</p>",
  "is_html": true
}
```

---

### 2. Send Bulk Emails

Send the same email to multiple recipients.

#### Endpoint
```
POST /email/bulk
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email/bulk
```

#### Request Body
```json
{
  "email_type": "customdomain",
  "sender_email": "support@f5universe.com",
  "recipients": [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
  ],
  "subject": "Bulk Email Subject",
  "body": "This message is sent to multiple recipients",
  "is_html": false
}
```

#### cURL Example
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "email_type": "customdomain",
    "sender_email": "support@f5universe.com",
    "recipients": ["user1@example.com", "user2@example.com"],
    "subject": "Bulk Email",
    "body": "Hello everyone!",
    "is_html": false
  }'
```

#### Success Response
```json
{
  "success": true,
  "total_sent": 3,
  "failed": 0,
  "details": [
    {
      "email": "user1@example.com",
      "status": "sent",
      "message_id": "0101019a1a9d37c9-..."
    },
    {
      "email": "user2@example.com",
      "status": "sent",
      "message_id": "0101019a1a9d37c9-..."
    },
    {
      "email": "user3@example.com",
      "status": "sent",
      "message_id": "0101019a1a9d37c9-..."
    }
  ]
}
```

---

### 3. Check Email Status

Check the status of the email service.

#### Endpoint
```
GET /email/status
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email/status
```

#### cURL Example
```bash
curl https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email/status
```

#### Response
```json
{
  "success": true,
  "service": "SES",
  "region": "us-west-2",
  "sender": "support@f5universe.com",
  "status": "operational"
}
```

---

## 📱 SMS APIs

### 1. Send Single SMS

Send a single SMS message using AWS SNS.

#### Endpoint
```
POST /sms/send
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/send
```

#### Request Body
```json
{
  "phone_number": "+1234567890",
  "message": "Your SMS message here (max 160 characters)"
}
```

#### Optional Parameters
```json
{
  "phone_number": "+1234567890",
  "message": "Your SMS message",
  "sender_id": "EduServices"
}
```

#### cURL Example
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Test SMS from AI IVR System"
  }'
```

#### PowerShell Example
```powershell
$body = @{
    phone_number = "+1234567890"
    message = "Test SMS from AI IVR System"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/send" `
  -Method Post -Body $body -ContentType "application/json"
```

#### Success Response
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "message_id": "12345678-abcd-1234-efgh-123456789012",
  "recipient": "+1234567890"
}
```

---

### 2. Send Bulk SMS

Send SMS to multiple phone numbers.

#### Endpoint
```
POST /sms/bulk
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/bulk
```

#### Request Body
```json
{
  "recipients": [
    "+1234567890",
    "+0987654321",
    "+1122334455"
  ],
  "message": "Bulk SMS notification for all recipients"
}
```

#### cURL Example
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["+1234567890", "+0987654321"],
    "message": "Bulk SMS test"
  }'
```

#### Success Response
```json
{
  "success": true,
  "total_sent": 3,
  "failed": 0,
  "details": [
    {
      "phone": "+1234567890",
      "status": "sent",
      "message_id": "12345678-abcd-..."
    },
    {
      "phone": "+0987654321",
      "status": "sent",
      "message_id": "87654321-dcba-..."
    },
    {
      "phone": "+1122334455",
      "status": "sent",
      "message_id": "11223344-aabb-..."
    }
  ]
}
```

---

### 3. Check SMS Status

Check the status of the SMS service.

#### Endpoint
```
GET /sms/status
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/status
```

#### cURL Example
```bash
curl https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/status
```

#### Response
```json
{
  "success": true,
  "service": "SNS",
  "region": "us-west-2",
  "sender_id": "EduServices",
  "status": "operational"
}
```

---

## 📨 Templated Email APIs

### 1. Send Generic Templated Email

Send email using a generic template.

#### Endpoint
```
POST /templated-email
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email
```

#### Request Body
```json
{
  "to_email": "user@example.com",
  "template_name": "welcome",
  "template_data": {
    "user_name": "John Doe",
    "company": "ABC Corporation",
    "custom_field": "Custom Value"
  }
}
```

#### cURL Example
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "template_name": "welcome",
    "template_data": {
      "user_name": "John Doe",
      "company": "ABC Corp"
    }
  }'
```

#### Success Response
```json
{
  "success": true,
  "message": "Templated email sent successfully",
  "message_id": "0101019a1a9d37c9-...",
  "template": "welcome",
  "recipient": "user@example.com"
}
```

---

### 2. Send Login Verification Email

Send login verification email with OTP/verification code.

#### Endpoint
```
POST /templated-email/login
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/login
```

#### Request Body
```json
{
  "to_email": "user@example.com",
  "user_name": "John Doe",
  "verification_code": "123456",
  "ip_address": "192.168.1.1",
  "device": "Chrome on Windows",
  "login_time": "2025-10-25 14:30:00"
}
```

#### Required Parameters
- `to_email` (string) - Recipient email address
- `user_name` (string) - User's name
- `verification_code` (string) - OTP or verification code

#### Optional Parameters
- `ip_address` (string) - Login IP address
- `device` (string) - Device/browser info
- `login_time` (string) - Login timestamp

#### cURL Example
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/login \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "user_name": "John Doe",
    "verification_code": "987654",
    "ip_address": "203.45.67.89",
    "device": "Chrome on Windows"
  }'
```

#### PowerShell Example
```powershell
$body = @{
    to_email = "user@example.com"
    user_name = "John Doe"
    verification_code = "123456"
    ip_address = "192.168.1.1"
    device = "Chrome on Windows"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/login" `
  -Method Post -Body $body -ContentType "application/json"
```

#### Success Response
```json
{
  "success": true,
  "message": "Login verification email sent",
  "message_id": "0101019a1a9d37c9-...",
  "template": "login_verification",
  "recipient": "user@example.com"
}
```

---

### 3. Send Registration Email

Send registration confirmation email with activation link.

#### Endpoint
```
POST /templated-email/registration
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/registration
```

#### Request Body
```json
{
  "to_email": "newuser@example.com",
  "user_name": "Jane Smith",
  "activation_link": "https://yourdomain.com/activate/abc123def456",
  "company_name": "Your Company",
  "support_email": "support@yourdomain.com"
}
```

#### Required Parameters
- `to_email` (string) - Recipient email address
- `user_name` (string) - User's name
- `activation_link` (string) - Account activation URL

#### Optional Parameters
- `company_name` (string) - Your company name
- `support_email` (string) - Support contact email

#### cURL Example
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/registration \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "newuser@example.com",
    "user_name": "Jane Smith",
    "activation_link": "https://example.com/activate/xyz789",
    "company_name": "AI IVR Systems"
  }'
```

#### PowerShell Example
```powershell
$body = @{
    to_email = "newuser@example.com"
    user_name = "Jane Smith"
    activation_link = "https://example.com/activate/abc123"
    company_name = "AI IVR Systems"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/registration" `
  -Method Post -Body $body -ContentType "application/json"
```

#### Success Response
```json
{
  "success": true,
  "message": "Registration email sent",
  "message_id": "0101019a1a9d37c9-...",
  "template": "registration",
  "recipient": "newuser@example.com"
}
```

---

### 4. Send Custom Template Email

Send email using any custom template type.

#### Endpoint
```
POST /templated-email/{template_type}
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/{template_type}
```

#### Available Template Types
- `password-reset` - Password reset emails
- `welcome` - Welcome emails
- `notification` - General notifications
- `invoice` - Invoice emails
- `reminder` - Reminder emails
- Any custom template you define

---

#### Example 1: Password Reset Email

**Endpoint:**
```
POST /templated-email/password-reset
```

**Request Body:**
```json
{
  "to_email": "user@example.com",
  "user_name": "John Doe",
  "reset_link": "https://yourdomain.com/reset-password/token123",
  "expiry_time": "24 hours"
}
```

**cURL Example:**
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "user_name": "John Doe",
    "reset_link": "https://example.com/reset/abc123"
  }'
```

---

#### Example 2: Welcome Email

**Endpoint:**
```
POST /templated-email/welcome
```

**Request Body:**
```json
{
  "to_email": "newuser@example.com",
  "user_name": "Alice Johnson",
  "company_name": "AI IVR Systems",
  "login_link": "https://yourdomain.com/login"
}
```

**cURL Example:**
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/welcome \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "newuser@example.com",
    "user_name": "Alice Johnson",
    "company_name": "AI IVR Systems"
  }'
```

---

#### Example 3: Invoice Email

**Endpoint:**
```
POST /templated-email/invoice
```

**Request Body:**
```json
{
  "to_email": "customer@example.com",
  "customer_name": "Bob Wilson",
  "invoice_number": "INV-2025-001",
  "amount": "$99.99",
  "due_date": "2025-11-15",
  "invoice_link": "https://yourdomain.com/invoices/INV-2025-001"
}
```

**cURL Example:**
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/invoice \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "customer@example.com",
    "customer_name": "Bob Wilson",
    "invoice_number": "INV-2025-001",
    "amount": "$99.99"
  }'
```

---

## 🔍 System Status

Check overall API health and configuration.

#### Endpoint
```
GET /api-status
```

#### Full URL
```
https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/api-status
```

#### cURL Example
```bash
curl https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/api-status
```

#### Response
```json
{
  "status": "healthy",
  "service": "email-sms-api",
  "timestamp": "2025-10-25T14:30:00Z",
  "email_service": "SES",
  "sms_service": "SNS",
  "region": "us-west-2",
  "functions": {
    "email": "operational",
    "sms": "operational",
    "templated_email": "operational"
  }
}
```

---

## ⚠️ Error Codes

### Common Error Responses

#### 400 Bad Request - Missing Required Field
```json
{
  "success": false,
  "error": "Missing required field: to_email"
}
```

#### 400 Bad Request - Invalid Email Type
```json
{
  "success": false,
  "error": "Invalid email_type: invalid. Supported: smtp, customdomain, subdomain"
}
```

#### 401 Unauthorized - Invalid SMTP Credentials
```json
{
  "success": false,
  "error": "SMTP email and password are required for Gmail sending"
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error": "SES Custom Domain sending failed: Email address not verified"
}
```

---

## 📊 Parameter Reference Table

### Email Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `email_type` | string | Yes | Email provider type | `customdomain`, `subdomain`, `smtp` |
| `to_email` | string | Yes | Recipient email | `user@example.com` |
| `subject` | string | Yes | Email subject | `Test Email` |
| `body` | string | Yes | Email content | `Hello World` |
| `is_html` | boolean | No | HTML email flag | `true` or `false` |
| `sender_email` | string | Conditional | Sender email (SES) | `support@f5universe.com` |
| `smtp_email` | string | Conditional | SMTP email (Gmail) | `your@gmail.com` |
| `smtp_password` | string | Conditional | SMTP password | `app-password` |
| `smtp_server` | string | No | SMTP server | `smtp.gmail.com` |
| `smtp_port` | integer | No | SMTP port | `587` |
| `cc` | array | No | CC recipients | `["cc@example.com"]` |
| `bcc` | array | No | BCC recipients | `["bcc@example.com"]` |
| `reply_to` | string | No | Reply-to address | `noreply@example.com` |

### SMS Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `phone_number` | string | Yes | Recipient phone (E.164) | `+1234567890` |
| `message` | string | Yes | SMS content (max 160 chars) | `Hello!` |
| `sender_id` | string | No | Sender ID | `EduServices` |

### Templated Email Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `to_email` | string | Yes | Recipient email | `user@example.com` |
| `user_name` | string | Yes | User's name | `John Doe` |
| `verification_code` | string | Login only | OTP/code | `123456` |
| `activation_link` | string | Registration only | Activation URL | `https://...` |
| `reset_link` | string | Password reset | Reset URL | `https://...` |
| `template_data` | object | Generic only | Custom template data | `{"key": "value"}` |

---

## 🧪 Testing Examples

### Quick Test - Custom Domain Email
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/email \
  -H "Content-Type: application/json" \
  -d '{
    "email_type": "customdomain",
    "sender_email": "support@f5universe.com",
    "to_email": "your-email@example.com",
    "subject": "Quick Test",
    "body": "Testing email API",
    "is_html": false
  }'
```

### Quick Test - SMS
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Quick SMS test"
  }'
```

### Quick Test - Login Email
```bash
curl -X POST https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev/templated-email/login \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-email@example.com",
    "user_name": "Test User",
    "verification_code": "123456"
  }'
```

---

## 📝 Best Practices

1. **Email Type Selection**
   - Use `customdomain` for professional emails (support@f5universe.com)
   - Use `subdomain` for transactional emails (noreply@mail.futuristic5.com)
   - Use `smtp` only when SES is not available

2. **Phone Number Format**
   - Always use E.164 format: `+[country code][number]`
   - Example: `+12025551234` (USA), `+919876543210` (India)

3. **SMS Message Length**
   - Keep messages under 160 characters
   - Longer messages may be split into multiple SMS

4. **Error Handling**
   - Always check `success` field in response
   - Log `message_id` for tracking
   - Implement retry logic for failed sends

5. **Rate Limiting**
   - AWS SES: 14 emails/second (default)
   - AWS SNS: 20 SMS/second (default)
   - Contact AWS to increase limits if needed

---

## 🔗 Related Documentation

- `AWS_LAMBDA_ENDPOINTS.md` - Complete endpoint reference
- `AI_IVR_USER_GUIDE.md` - AI IVR system usage guide
- `LWL_DATABASE_ANALYSIS_AND_RECOMMENDATIONS.md` - Database schema

---

**Last Updated**: October 25, 2025  
**Version**: 1.0  
**API Base URL**: https://zfoyqsng66.execute-api.us-west-2.amazonaws.com/dev
