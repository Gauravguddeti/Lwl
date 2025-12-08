#!/usr/bin/env python3
"""
Local OTP API Test
Test the OTP API handler locally without deploying
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handler import lambda_handler

def test_local():
    """Test the OTP handler locally"""
    print("🧪 Local OTP API Test")
    print("=" * 30)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    test_event = {
        'httpMethod': 'GET',
        'path': '/otp/status'
    }
    
    response = lambda_handler(test_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test 2: Send OTP
    print("\n2. Testing Send OTP...")
    test_otp_event = {
        'httpMethod': 'POST',
        'path': '/otp/send',
        'body': json.dumps({
            'mobile': '+1234567890',
            'purpose': 'login',
            'sender_id': 'EDUOTP'
        })
    }
    
    response = lambda_handler(test_otp_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test 3: Verify OTP
    print("\n3. Testing Verify OTP...")
    test_verify_event = {
        'httpMethod': 'POST',
        'path': '/otp/verify',
        'body': json.dumps({
            'otp_id': 'otp_1234567890',
            'otp_code': '123456',
            'mobile': '+1234567890'
        })
    }
    
    response = lambda_handler(test_verify_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test 4: Validation Error
    print("\n4. Testing Validation Error...")
    test_invalid_event = {
        'httpMethod': 'POST',
        'path': '/otp/send',
        'body': json.dumps({
            'mobile': '',  # Invalid empty mobile
            'purpose': 'login'
        })
    }
    
    response = lambda_handler(test_invalid_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    print("\n✅ Local testing completed!")
    print("Note: This tests the handler logic. For actual OTP sending, deploy to AWS.")

if __name__ == "__main__":
    test_local()
