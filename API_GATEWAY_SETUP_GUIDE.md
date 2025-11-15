# 🔧 Fix: "Missing Authentication Token" Error

## ❌ **The Problem:**
You're getting `{"message":"Missing Authentication Token"}` because you're trying to access the Lambda function directly instead of through API Gateway.

## ✅ **The Solution:**
You need to set up API Gateway to expose your Lambda function as a REST API.

## 🚀 **Quick Fix - Follow These Steps:**

### **Method 1: API Gateway Console Setup (Recommended)**

#### **Step 1: Create API Gateway**
1. **Go to API Gateway Console**: https://console.aws.amazon.com/apigateway/
2. **Click "Create API"**
3. **Choose "REST API"** → **"Build"**
4. **API name**: `sms-api` (or `otp-api`)
5. **Description**: `SMS API for IVR Integration`
6. **Click "Create API"**

#### **Step 2: Create Resources and Methods**

**For SMS API:**
1. **Create `/sms` resource**:
   - Click "Actions" → "Create Resource"
   - Resource Name: `sms`
   - Resource Path: `/sms`
   - Click "Create Resource"

2. **Create sub-resources**:
   - `/sms/status` (GET)
   - `/sms/send` (POST)
   - `/sms/bulk` (POST)
   - `/sms/sandbox` (POST)

**For OTP API:**
1. **Create `/otp` resource**:
   - Click "Actions" → "Create Resource"
   - Resource Name: `otp`
   - Resource Path: `/otp`
   - Click "Create Resource"

2. **Create sub-resources**:
   - `/otp/status` (GET)
   - `/otp/send` (POST)
   - `/otp/verify` (POST)

#### **Step 3: Create Methods**
For each resource:
1. **Select the resource**
2. **Click "Actions"** → **"Create Method"** → **Select method type**
3. **Integration type**: Lambda Function
4. **Lambda Function**: Select your function name
5. **Click "Save"** → **"OK"**

#### **Step 4: Enable CORS**
1. **Select each method** (GET, POST)
2. **Click "Actions"** → **"Enable CORS"**
3. **Click "Enable CORS and replace existing CORS headers"**

#### **Step 5: Deploy API**
1. **Click "Actions"** → **"Deploy API"**
2. **Deployment stage**: `[New Stage]`
3. **Stage name**: `dev`
4. **Click "Deploy"**

#### **Step 6: Get Your API URL**
After deployment, you'll see:
```
https://abc123def4.execute-api.us-west-2.amazonaws.com/dev
```

**Use this URL instead of the Lambda function URL!**

### **Method 2: Test Lambda Function Directly**

If you want to test the Lambda function directly (without API Gateway):

#### **Step 1: Go to Lambda Console**
1. **Go to**: https://console.aws.amazon.com/lambda/
2. **Select your function**
3. **Click "Test"**

#### **Step 2: Create Test Event**
**For SMS API:**
```json
{
  "httpMethod": "POST",
  "path": "/sms/send",
  "body": "{\"phone_number\": \"+1234567890\", \"message\": \"Test message\"}"
}
```

**For OTP API:**
```json
{
  "httpMethod": "POST",
  "path": "/otp/send",
  "body": "{\"mobile\": \"+1234567890\", \"purpose\": \"login\"}"
}
```

#### **Step 3: Run Test**
1. **Click "Test"**
2. **Check the response**

## 🧪 **Test Your API:**

### **Using API Gateway URL:**
```bash
# Test SMS API
curl -X POST https://your-api-gateway-url.amazonaws.com/dev/sms/send \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "Test message"}'

# Test OTP API
curl -X POST https://your-api-gateway-url.amazonaws.com/dev/otp/send \
  -H "Content-Type: application/json" \
  -d '{"mobile": "+1234567890", "purpose": "login"}'
```

### **Using Lambda Test Console:**
Use the test events provided above in the Lambda console.

## 🔍 **Common Issues & Solutions:**

### **Issue 1: Still Getting Auth Token Error**
- **Solution**: Make sure you're using the API Gateway URL, not the Lambda function URL
- **API Gateway URL**: `https://abc123def4.execute-api.us-west-2.amazonaws.com/dev`
- **Lambda URL**: `https://abc123def4.lambda-url.us-west-2.on.aws/` ❌

### **Issue 2: CORS Errors**
- **Solution**: Make sure you enabled CORS for all methods
- **Check**: API Gateway → Your API → Resources → Actions → Enable CORS

### **Issue 3: Method Not Allowed**
- **Solution**: Make sure you're using the correct HTTP method (GET/POST)
- **Check**: API Gateway → Your API → Resources → Methods

### **Issue 4: Lambda Function Not Found**
- **Solution**: Make sure the Lambda function name matches exactly
- **Check**: API Gateway → Integration → Lambda Function

## 📋 **Quick Checklist:**

- [ ] API Gateway created
- [ ] Resources and methods created
- [ ] CORS enabled
- [ ] API deployed
- [ ] Using API Gateway URL (not Lambda URL)
- [ ] Correct HTTP methods (GET/POST)
- [ ] Proper JSON body format

## 🎉 **You're All Set!**

Once you set up API Gateway, you'll get a proper REST API URL that you can use in your IVR system. The "Missing Authentication Token" error will be resolved!

## 🆘 **Need Help?**

1. **Check the API Gateway setup** step by step
2. **Verify you're using the API Gateway URL**
3. **Test with the provided test events**
4. **Check CloudWatch logs** for any errors

**The fix is straightforward - just set up API Gateway and use the correct URL!** 🚀
