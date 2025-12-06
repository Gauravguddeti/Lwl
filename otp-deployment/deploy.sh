#!/bin/bash
# OTP API Deployment Script for Linux/Mac
# This script deploys the OTP API service to AWS Lambda

STAGE="dev"
REMOVE=false
LOGS=false
TEST=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stage)
            STAGE="$2"
            shift 2
            ;;
        --remove)
            REMOVE=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --stage STAGE    Deployment stage (default: dev)"
            echo "  --remove         Remove the deployed service"
            echo "  --logs           Show CloudWatch logs"
            echo "  --test           Run local tests"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo "🚀 OTP API Deployment Script"
echo "============================="

# Check if serverless is installed
if ! command -v serverless &> /dev/null; then
    echo "❌ Serverless Framework not found. Installing..."
    npm install -g serverless
    npm install
fi

# Check if AWS CLI is configured
echo "🔍 Checking AWS CLI configuration..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi
echo "✅ AWS CLI configured"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ "$REMOVE" = true ]; then
    echo "🗑️  Removing OTP API service..."
    serverless remove --stage $STAGE
    echo "✅ Service removed successfully"
    exit 0
fi

if [ "$LOGS" = true ]; then
    echo "📋 Fetching logs..."
    serverless logs -f otpHandler --stage $STAGE
    exit 0
fi

if [ "$TEST" = true ]; then
    echo "🧪 Running local tests..."
    python src/handler.py
    exit 0
fi

# Deploy the service
echo "🚀 Deploying OTP API service to stage: $STAGE"
serverless deploy --stage $STAGE

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Test your endpoints using the provided test scripts"
    echo "2. Check CloudWatch logs for any issues"
    echo "3. Configure your IVR system to use the API endpoints"
    echo ""
    echo "🔗 Useful Commands:"
    echo "  View logs: ./deploy.sh --logs"
    echo "  Remove service: ./deploy.sh --remove"
    echo "  Test locally: ./deploy.sh --test"
else
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi
