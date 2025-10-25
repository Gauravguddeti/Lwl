#!/usr/bin/env python3
"""
Quick Test Script for Email & SMS API Package
Tests the services before deployment
"""

import os
import sys
from pathlib import Path

# Add package to path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir))

def test_configuration():
    """Test configuration loading"""
    print("🔧 Testing Configuration...")
    try:
        from config.settings import config
        
        # Get validation results
        validation = config.validate_environment()
        
        print(f"   Configuration Valid: {validation['valid']}")
        if validation['errors']:
            print(f"   ❌ Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"   ⚠️  Warnings: {validation['warnings']}")
        
        print(f"   Services Status: {validation['services']}")
        return validation['valid']
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_email_service():
    """Test email service initialization"""
    print("\n📧 Testing Email Service...")
    try:
        from services.email_service import EmailService
        
        email_service = EmailService()
        print("   ✅ Email service initialized successfully")
        
        # Test configuration
        config = email_service.get_service_status()
        print(f"   Service Status: {config}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Email service test failed: {e}")
        return False

def test_sms_service():
    """Test SMS service initialization"""
    print("\n📱 Testing SMS Service...")
    try:
        from services.sms_service import SMSService
        
        sms_service = SMSService()
        print("   ✅ SMS service initialized successfully")
        
        # Test SMS service functionality
        print("   SMS service ready for sending messages")
        
        return True
        
    except Exception as e:
        print(f"   ❌ SMS service test failed: {e}")
        return False

def test_templated_email_service():
    """Test templated email service"""
    print("\n📄 Testing Templated Email Service...")
    try:
        from services.templated_email_service import TemplatedEmailService
        
        templated_service = TemplatedEmailService()
        print("   ✅ Templated email service initialized successfully")
        
        # Test template creation
        templates = templated_service.create_templates()
        print(f"   Available templates: {list(templates.keys())}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Templated email service test failed: {e}")
        return False

def test_api_handlers():
    """Test API handler imports"""
    print("\n🚀 Testing API Handlers...")
    try:
        # Test email handler
        from api.email_handler import lambda_handler as email_handler
        print("   ✅ Email API handler imported successfully")
        
        # Test SMS handler  
        from api.sms_handler import lambda_handler as sms_handler
        print("   ✅ SMS API handler imported successfully")
        
        # Test templated email handler
        from api.templated_email_handler import lambda_handler as templated_handler
        print("   ✅ Templated Email API handler imported successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API handlers test failed: {e}")
        return False

def test_deployment_files():
    """Test deployment configuration files"""
    print("\n⚙️  Testing Deployment Files...")
    
    files_to_check = [
        'serverless.yml',
        'requirements.txt', 
        'package.json',
        '.env.template',
        'integration_docs/README.md',
        'integration_docs/QUICK_START.md'
    ]
    
    missing_files = []
    for file_path in files_to_check:
        full_path = package_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
        return False
    
    print("   ✅ All deployment files present")
    return True

def run_integration_test():
    """Run a basic integration test"""
    print("\n🧪 Running Integration Test...")
    
    # Create a mock event for testing
    test_event = {
        'httpMethod': 'GET',
        'path': '/email/status',
        'headers': {},
        'body': None
    }
    
    test_context = type('Context', (), {'aws_request_id': 'test-request-id'})()
    
    try:
        from api.email_handler import lambda_handler
        
        # Test email status endpoint
        response = lambda_handler(test_event, test_context)
        
        if response['statusCode'] == 200:
            print("   ✅ Email API status endpoint working")
            return True
        else:
            print(f"   ❌ Email API returned status {response['statusCode']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Email & SMS API Package - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Email Service", test_email_service),
        ("SMS Service", test_sms_service), 
        ("Templated Email Service", test_templated_email_service),
        ("API Handlers", test_api_handlers),
        ("Deployment Files", test_deployment_files),
        ("Integration Test", run_integration_test)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Package is ready for deployment.")
        print("\nNext steps:")
        print("1. Copy .env.template to .env and configure your settings")
        print("2. Run 'npm run deploy' to deploy to AWS")
        print("3. Share the API endpoints with your friend for IVR integration")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)