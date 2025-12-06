# Create OTP Lambda Deployment Package
# This script creates a ZIP file ready for AWS Lambda deployment

Write-Host "📦 Creating OTP Lambda Deployment Package" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "handler.py")) {
    Write-Host "❌ Error: Please run this script from the otp-deployment directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "Expected files: handler.py, otp_service.py" -ForegroundColor Yellow
    exit 1
}

# Create deployment package
Write-Host "🔍 Checking source files..." -ForegroundColor Yellow

$requiredFiles = @(
    "handler.py",
    "otp_service.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        exit 1
    }
}

# Create ZIP file
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow

# Remove existing package if it exists
if (Test-Path "otp-lambda-package.zip") {
    Remove-Item "otp-lambda-package.zip" -Force
    Write-Host "🗑️  Removed existing package" -ForegroundColor Yellow
}

# Create ZIP with the correct structure
try {
    # Create ZIP file with files at root level
    Compress-Archive -Path "handler.py", "otp_service.py" -DestinationPath "otp-lambda-package.zip" -Force
    
    Write-Host "✅ Deployment package created: otp-lambda-package.zip" -ForegroundColor Green
    
    # Show package contents
    Write-Host "📋 Package contents:" -ForegroundColor Cyan
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead("$(Get-Location)\otp-lambda-package.zip")
    $zip.Entries | ForEach-Object { Write-Host "  - $($_.FullName)" -ForegroundColor White }
    $zip.Dispose()
    
    Write-Host ""
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Go to AWS Lambda Console: https://console.aws.amazon.com/lambda/" -ForegroundColor White
    Write-Host "2. Create a new Lambda function (Python 3.12)" -ForegroundColor White
    Write-Host "3. Upload the otp-lambda-package.zip file" -ForegroundColor White
    Write-Host "4. Configure the function (512MB memory, 30s timeout)" -ForegroundColor White
    Write-Host "5. Set up API Gateway to expose the endpoints" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 For detailed instructions, see:" -ForegroundColor Cyan
    Write-Host "  - ZIP_DEPLOYMENT.md" -ForegroundColor White
    Write-Host "  - AWS_CONSOLE_DEPLOYMENT.md" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error creating package: $($_.Exception.Message)" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host ""
Write-Host "🎉 Package creation completed successfully!" -ForegroundColor Green
