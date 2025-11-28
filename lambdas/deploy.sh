#!/bin/bash
# Lambda Deployment Script
# ========================

set -e

echo "🚀 Deploying Lambda Functions..."

# Configuration
REGION="us-west-2"
ROLE_NAME="lambda-execution-role"
FUNCTION_PREFIX="ai-telecaller"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Create IAM role if it doesn't exist
print_status "Creating IAM role..."
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document '{
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
    }' 2>/dev/null || print_warning "Role already exists"

# Attach policies to role
print_status "Attaching policies to role..."
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSESFullAccess

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)

# Function to deploy a single Lambda
deploy_lambda() {
    local function_name=$1
    local python_file=$2
    local description=$3
    
    print_status "Deploying $function_name..."
    
    # Create deployment package
    zip -r ${function_name}.zip $python_file
    
    # Create or update Lambda function
    aws lambda create-function \
        --function-name $function_name \
        --runtime python3.12 \
        --role $ROLE_ARN \
        --handler ${python_file%.py}.lambda_handler \
        --zip-file fileb://${function_name}.zip \
        --description "$description" \
        --timeout 30 \
        --memory-size 256 \
        --environment Variables='{
            "DB_HOST":"'${DB_HOST:-localhost}'",
            "DB_PORT":"'${DB_PORT:-5432}'",
            "DB_NAME":"'${DB_NAME:-lwl_pg_us_2}'",
            "DB_USER":"'${DB_USER:-postgres}'",
            "DB_PASSWORD":"'${DB_PASSWORD:-}'",
            "TWILIO_ACCOUNT_SID":"'${TWILIO_ACCOUNT_SID:-}'",
            "TWILIO_AUTH_TOKEN":"'${TWILIO_AUTH_TOKEN:-}'",
            "TWILIO_PHONE_NUMBER":"'${TWILIO_PHONE_NUMBER:-}'"
        }' \
        --region $REGION 2>/dev/null || \
    aws lambda update-function-code \
        --function-name $function_name \
        --zip-file fileb://${function_name}.zip \
        --region $REGION
    
    # Clean up
    rm ${function_name}.zip
    
    print_status "$function_name deployed successfully"
}

# Deploy all Lambda functions
deploy_lambda "${FUNCTION_PREFIX}-send-sms-single" "send_sms_single.py" "Send single SMS via AWS SNS"
deploy_lambda "${FUNCTION_PREFIX}-send-sms-bulk" "send_sms_bulk.py" "Send bulk SMS via AWS SNS"
deploy_lambda "${FUNCTION_PREFIX}-send-email-single" "send_email_single.py" "Send single email via AWS SES"
deploy_lambda "${FUNCTION_PREFIX}-send-email-bulk" "send_email_bulk.py" "Send bulk email via AWS SES"
deploy_lambda "${FUNCTION_PREFIX}-ivr-call-student" "ivr_call_student.py" "Make IVR calls to students via Twilio"
deploy_lambda "${FUNCTION_PREFIX}-schedule-ivr-call" "schedule_ivr_call.py" "Schedule IVR calls using EventBridge"
deploy_lambda "${FUNCTION_PREFIX}-send-otp" "send_otp.py" "Send OTP via SMS"

print_status "All Lambda functions deployed successfully!"
print_warning "Don't forget to:"
print_warning "1. Set up your database tables"
print_warning "2. Configure your environment variables"
print_warning "3. Verify your Twilio credentials"
print_warning "4. Set up API Gateway endpoints if needed"

echo ""
echo "📋 Lambda Function ARNs:"
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `'$FUNCTION_PREFIX'`)].{Name:FunctionName,Arn:FunctionArn}' --output table
