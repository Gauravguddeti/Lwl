# Lambda Deployment Script for Windows
# ====================================

param(
    [string]$Region = "us-west-2",
    [string]$RoleName = "lambda-execution-role",
    [string]$FunctionPrefix = "ai-telecaller"
)

Write-Host "🚀 Deploying Lambda Functions..." -ForegroundColor Green

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Host "❌ AWS CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if AWS credentials are configured
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "❌ AWS credentials not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# Create IAM role if it doesn't exist
Write-Host "✅ Creating IAM role..." -ForegroundColor Green
$assumeRolePolicy = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
'@

try {
    aws iam create-role --role-name $RoleName --assume-role-policy-document $assumeRolePolicy
} catch {
    Write-Host "⚠️  Role already exists" -ForegroundColor Yellow
}

# Attach policies to role
Write-Host "✅ Attaching policies to role..." -ForegroundColor Green
aws iam attach-role-policy --role-name $RoleName --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
aws iam attach-role-policy --role-name $RoleName --policy-arn "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
aws iam attach-role-policy --role-name $RoleName --policy-arn "arn:aws:iam::aws:policy/AmazonSESFullAccess"
aws iam attach-role-policy --role-name $RoleName --policy-arn "arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess"

# Get role ARN
$RoleArn = (aws iam get-role --role-name $RoleName --query 'Role.Arn' --output text)

# Function to deploy a single Lambda
function Deploy-Lambda {
    param(
        [string]$FunctionName,
        [string]$PythonFile,
        [string]$Description
    )
    
    Write-Host "✅ Deploying $FunctionName..." -ForegroundColor Green
    
    # Create deployment package
    Compress-Archive -Path $PythonFile -DestinationPath "$FunctionName.zip" -Force
    
    # Environment variables
    $envVars = @{
        "DB_HOST" = $env:DB_HOST ?? "localhost"
        "DB_PORT" = $env:DB_PORT ?? "5432"
        "DB_NAME" = $env:DB_NAME ?? "lwl_pg_us_2"
        "DB_USER" = $env:DB_USER ?? "postgres"
        "DB_PASSWORD" = $env:DB_PASSWORD ?? ""
        "TWILIO_ACCOUNT_SID" = $env:TWILIO_ACCOUNT_SID ?? ""
        "TWILIO_AUTH_TOKEN" = $env:TWILIO_AUTH_TOKEN ?? ""
        "TWILIO_PHONE_NUMBER" = $env:TWILIO_PHONE_NUMBER ?? ""
    }
    
    $envJson = ($envVars | ConvertTo-Json -Compress)
    
    # Create or update Lambda function
    try {
        aws lambda create-function `
            --function-name $FunctionName `
            --runtime python3.12 `
            --role $RoleArn `
            --handler "$($PythonFile.Replace('.py', '')).lambda_handler" `
            --zip-file "fileb://$FunctionName.zip" `
            --description $Description `
            --timeout 30 `
            --memory-size 256 `
            --environment "Variables=$envJson" `
            --region $Region
    } catch {
        aws lambda update-function-code `
            --function-name $FunctionName `
            --zip-file "fileb://$FunctionName.zip" `
            --region $Region
    }
    
    # Clean up
    Remove-Item "$FunctionName.zip" -Force
    
    Write-Host "✅ $FunctionName deployed successfully" -ForegroundColor Green
}

# Deploy all Lambda functions
Deploy-Lambda "$FunctionPrefix-send-sms-single" "send_sms_single.py" "Send single SMS via AWS SNS"
Deploy-Lambda "$FunctionPrefix-send-sms-bulk" "send_sms_bulk.py" "Send bulk SMS via AWS SNS"
Deploy-Lambda "$FunctionPrefix-send-email-single" "send_email_single.py" "Send single email via AWS SES"
Deploy-Lambda "$FunctionPrefix-send-email-bulk" "send_email_bulk.py" "Send bulk email via AWS SES"
Deploy-Lambda "$FunctionPrefix-ivr-call-student" "ivr_call_student.py" "Make IVR calls to students via Twilio"
Deploy-Lambda "$FunctionPrefix-schedule-ivr-call" "schedule_ivr_call.py" "Schedule IVR calls using EventBridge"
Deploy-Lambda "$FunctionPrefix-send-otp" "send_otp.py" "Send OTP via SMS"

Write-Host "✅ All Lambda functions deployed successfully!" -ForegroundColor Green
Write-Host "⚠️  Don't forget to:" -ForegroundColor Yellow
Write-Host "1. Set up your database tables" -ForegroundColor Yellow
Write-Host "2. Configure your environment variables" -ForegroundColor Yellow
Write-Host "3. Verify your Twilio credentials" -ForegroundColor Yellow
Write-Host "4. Set up API Gateway endpoints if needed" -ForegroundColor Yellow

Write-Host ""
Write-Host "📋 Lambda Function ARNs:" -ForegroundColor Cyan
aws lambda list-functions --query "Functions[?starts_with(FunctionName, `'$FunctionPrefix`')].{Name:FunctionName,Arn:FunctionArn}" --output table
