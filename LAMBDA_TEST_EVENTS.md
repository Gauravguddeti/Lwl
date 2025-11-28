# 🧪 Lambda Test Events - Ready to Use

## 📋 **Copy-Paste Test Events for Lambda Console**

### **SMS API Test Events:**

#### **1. Health Check (GET)**
```json
{
  "httpMethod": "GET",
  "path": "/sms/status"
}
```

#### **2. Send Single SMS (POST)**
```json
{
  "httpMethod": "POST",
  "path": "/sms/send",
  "body": "{\"phone_number\": \"+1234567890\", \"message\": \"Test SMS from Lambda\", \"sender_id\": \"TEST\"}"
}
```

#### **3. Send Bulk SMS (POST)**
```json
{
  "httpMethod": "POST",
  "path": "/sms/bulk",
  "body": "{\"phone_numbers\": [\"+1234567890\", \"+1987654321\"], \"message\": \"Bulk SMS test\", \"sender_id\": \"TEST\"}"
}
```

#### **4. Add to Sandbox (POST)**
```json
{
  "httpMethod": "POST",
  "path": "/sms/sandbox",
  "body": "{\"phone_number\": \"+1234567890\"}"
}
```

### **OTP API Test Events:**

#### **1. Health Check (GET)**
```json
{
  "httpMethod": "GET",
  "path": "/otp/status"
}
```

#### **2. Send OTP (POST)**
```json
{
  "httpMethod": "POST",
  "path": "/otp/send",
  "body": "{\"mobile\": \"+1234567890\", \"purpose\": \"login\", \"sender_id\": \"EDUOTP\"}"
}
```

#### **3. Verify OTP (POST)**
```json
{
  "httpMethod": "POST",
  "path": "/otp/verify",
  "body": "{\"otp_id\": \"otp_1234567890\", \"otp_code\": \"123456\", \"mobile\": \"+1234567890\"}"
}
```

## 🚀 **How to Use These Test Events:**

### **Step 1: Go to Lambda Console**
1. **Go to**: https://console.aws.amazon.com/lambda/
2. **Select your function** (SMS or OTP)
3. **Click "Test"**

### **Step 2: Create Test Event**
1. **Click "Create new test event"**
2. **Choose "API Gateway AWS Proxy"** template
3. **Replace the JSON** with one of the test events above
4. **Give it a name** (e.g., "SMS Send Test")
5. **Click "Create"**

### **Step 3: Run Test**
1. **Click "Test"**
2. **Check the response**

## 📊 **Expected Responses:**

### **Successful SMS Send:**
```json
{
  "statusCode": 200,
  "headers": {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  },
  "body": "{\"success\": true, \"message\": \"SMS sent successfully to +1234567890\", \"message_id\": \"abc123\", \"phone_number\": \"+1234567890\", \"sender_id\": \"TEST\", \"character_count\": 20, \"estimated_cost\": 0.0075}"
}
```

### **Successful OTP Send:**
```json
{
  "statusCode": 200,
  "headers": {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  },
  "body": "{\"success\": true, \"message\": \"OTP sent successfully\", \"otp_id\": \"otp_1234567890\", \"mobile\": \"+1234567890\", \"purpose\": \"login\", \"expires_in\": 600, \"message_id\": \"abc123\", \"provider\": \"AWS SNS\", \"sender_id\": \"EDUOTP\"}"
}
```

### **Validation Error:**
```json
{
  "statusCode": 400,
  "headers": {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  },
  "body": "{\"success\": false, \"error\": \"Validation failed\", \"message\": \"Missing required field: phone_number\"}"
}
```

## 🔧 **Troubleshooting:**

### **If you get "Missing Authentication Token":**
- You're trying to access Lambda directly
- **Solution**: Use these test events in Lambda console instead
- **Or**: Set up API Gateway (see API_GATEWAY_SETUP_GUIDE.md)

### **If you get import errors:**
- Make sure you uploaded the fixed ZIP file
- **Handler should be**: `handler.lambda_handler`
- **Not**: `src.handler.lambda_handler`

### **If you get AWS credential errors:**
- Make sure your Lambda function has the right IAM permissions
- **Required permissions**: SNS Publish, GetSMSAttributes, SetSMSAttributes

## 🎯 **Quick Test Sequence:**

1. **Test Health Check** first (should return service status)
2. **Test Send SMS/OTP** (should return success with message_id)
3. **Test Validation** with invalid data (should return error)
4. **Test Bulk SMS** (should return success for multiple numbers)

## 🎉 **You're Ready!**

These test events will help you verify that your Lambda functions are working correctly before setting up API Gateway!

**Copy, paste, and test!** 🚀
