@echo off
echo 📦 Creating OTP Lambda Deployment Package
echo =========================================

REM Check if we're in the right directory
if not exist "handler.py" (
    echo ❌ Error: Please run this script from the otp-deployment directory
    echo Current directory: %CD%
    echo Expected files: handler.py, otp_service.py
    pause
    exit /b 1
)

echo 🔍 Checking source files...

REM Check required files
if not exist "handler.py" (
    echo ❌ Missing: handler.py
    pause
    exit /b 1
) else (
    echo ✅ Found: handler.py
)

if not exist "otp_service.py" (
    echo ❌ Missing: otp_service.py
    pause
    exit /b 1
) else (
    echo ✅ Found: otp_service.py
)

echo 📦 Creating deployment package...

REM Remove existing package if it exists
if exist "otp-lambda-package.zip" (
    del "otp-lambda-package.zip"
    echo 🗑️  Removed existing package
)

REM Create ZIP file
powershell -command "Compress-Archive -Path 'handler.py', 'otp_service.py' -DestinationPath 'otp-lambda-package.zip' -Force"

if exist "otp-lambda-package.zip" (
    echo ✅ Deployment package created: otp-lambda-package.zip
    echo.
    echo 📋 Package contents:
    powershell -command "Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip = [System.IO.Compression.ZipFile]::OpenRead('otp-lambda-package.zip'); $zip.Entries | ForEach-Object { Write-Host '  - ' $_.FullName }; $zip.Dispose()"
    echo.
    echo 🚀 Next Steps:
    echo 1. Go to AWS Lambda Console: https://console.aws.amazon.com/lambda/
    echo 2. Create a new Lambda function (Python 3.12)
    echo 3. Upload the otp-lambda-package.zip file
    echo 4. Configure the function (512MB memory, 30s timeout)
    echo 5. Set up API Gateway to expose the endpoints
    echo.
    echo 📖 For detailed instructions, see:
    echo   - ZIP_DEPLOYMENT.md
    echo   - AWS_CONSOLE_DEPLOYMENT.md
    echo   - NO_CLI_DEPLOYMENT.md
) else (
    echo ❌ Error creating package
    pause
    exit /b 1
)

echo.
echo 🎉 Package creation completed successfully!
pause
