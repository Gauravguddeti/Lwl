# OTP API Deployment Script for Windows PowerShell
# This script deploys the OTP API service to AWS Lambda

param(
    [string]$Stage = "dev",
    [switch]$Remove = $false,
    [switch]$Logs = $false,
    [switch]$Test = $false
)

Write-Host "🚀 OTP API Deployment Script" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

# Check if serverless is installed
if (-not (Get-Command "serverless" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Serverless Framework not found. Installing..." -ForegroundColor Red
    npm install -g serverless
    npm install
}

# Check if AWS CLI is configured
Write-Host "🔍 Checking AWS CLI configuration..." -ForegroundColor Yellow
$awsConfig = aws sts get-caller-identity 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ AWS CLI not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}
Write-Host "✅ AWS CLI configured" -ForegroundColor Green

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm install

if ($Remove) {
    Write-Host "🗑️  Removing OTP API service..." -ForegroundColor Yellow
    serverless remove --stage $Stage
    Write-Host "✅ Service removed successfully" -ForegroundColor Green
    exit 0
}

if ($Logs) {
    Write-Host "📋 Fetching logs..." -ForegroundColor Yellow
    serverless logs -f otpHandler --stage $Stage
    exit 0
}

if ($Test) {
    Write-Host "🧪 Running local tests..." -ForegroundColor Yellow
    python src/handler.py
    exit 0
}

# Deploy the service
Write-Host "🚀 Deploying OTP API service to stage: $Stage" -ForegroundColor Yellow
serverless deploy --stage $Stage

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Test your endpoints using the provided test scripts" -ForegroundColor White
    Write-Host "2. Check CloudWatch logs for any issues" -ForegroundColor White
    Write-Host "3. Configure your IVR system to use the API endpoints" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 Useful Commands:" -ForegroundColor Cyan
    Write-Host "  View logs: .\deploy.ps1 -Logs" -ForegroundColor White
    Write-Host "  Remove service: .\deploy.ps1 -Remove" -ForegroundColor White
    Write-Host "  Test locally: .\deploy.ps1 -Test" -ForegroundColor White
} else {
    Write-Host "❌ Deployment failed. Check the error messages above." -ForegroundColor Red
    exit 1
}
