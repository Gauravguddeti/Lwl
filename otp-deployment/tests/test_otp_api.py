#!/usr/bin/env python3
"""
OTP API Test Suite
Tests for the deployed OTP API Lambda function
"""

import requests
import json
import time
import os
from typing import Dict, Any

class OTPTestSuite:
    """Comprehensive test suite for OTP API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_health_check(self):
        """Test service health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/otp/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('status') == 'operational':
                    self.log_test("Health Check", True, "Service is operational")
                    return True
                else:
                    self.log_test("Health Check", False, f"Service not operational: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_send_otp_validation(self):
        """Test send OTP validation"""
        test_cases = [
            {
                'name': 'Missing mobile',
                'data': {'purpose': 'login'},
                'should_fail': True
            },
            {
                'name': 'Empty mobile',
                'data': {'mobile': '', 'purpose': 'login'},
                'should_fail': True
            },
            {
                'name': 'Invalid mobile format',
                'data': {'mobile': '123', 'purpose': 'login'},
                'should_fail': True
            },
            {
                'name': 'Invalid purpose',
                'data': {'mobile': '+1234567890', 'purpose': 'invalid'},
                'should_fail': True
            },
            {
                'name': 'Valid request',
                'data': {'mobile': '+1234567890', 'purpose': 'login', 'sender_id': 'EDUOTP'},
                'should_fail': False
            }
        ]
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/otp/send",
                    json=test_case['data'],
                    timeout=10
                )
                
                data = response.json()
                success = data.get('success', False)
                
                if test_case['should_fail']:
                    if not success and response.status_code == 400:
                        self.log_test(f"Send OTP Validation: {test_case['name']}", True, "Correctly rejected invalid input")
                    else:
                        self.log_test(f"Send OTP Validation: {test_case['name']}", False, "Should have failed but got success")
                else:
                    if success or response.status_code == 200:
                        self.log_test(f"Send OTP Validation: {test_case['name']}", True, "Correctly accepted valid input")
                    else:
                        self.log_test(f"Send OTP Validation: {test_case['name']}", False, f"Should have succeeded but got error: {data.get('error')}")
                        
            except Exception as e:
                self.log_test(f"Send OTP Validation: {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_verify_otp_validation(self):
        """Test verify OTP validation"""
        test_cases = [
            {
                'name': 'Missing otp_id',
                'data': {'otp_code': '123456'},
                'should_fail': True
            },
            {
                'name': 'Missing otp_code',
                'data': {'otp_id': 'otp_1234567890'},
                'should_fail': True
            },
            {
                'name': 'Invalid otp_code format',
                'data': {'otp_id': 'otp_1234567890', 'otp_code': '12345'},
                'should_fail': True
            },
            {
                'name': 'Valid verification request',
                'data': {'otp_id': 'otp_1234567890', 'otp_code': '123456', 'mobile': '+1234567890'},
                'should_fail': False
            }
        ]
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/otp/verify",
                    json=test_case['data'],
                    timeout=10
                )
                
                data = response.json()
                success = data.get('success', False)
                
                if test_case['should_fail']:
                    if not success and response.status_code == 400:
                        self.log_test(f"Verify OTP Validation: {test_case['name']}", True, "Correctly rejected invalid input")
                    else:
                        self.log_test(f"Verify OTP Validation: {test_case['name']}", False, "Should have failed but got success")
                else:
                    if success or response.status_code == 200:
                        self.log_test(f"Verify OTP Validation: {test_case['name']}", True, "Correctly accepted valid input")
                    else:
                        self.log_test(f"Verify OTP Validation: {test_case['name']}", False, f"Should have succeeded but got error: {data.get('error')}")
                        
            except Exception as e:
                self.log_test(f"Verify OTP Validation: {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_cors_headers(self):
        """Test CORS headers"""
        try:
            response = requests.options(f"{self.base_url}/otp/status", timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Headers',
                'Access-Control-Allow-Methods'
            }
            
            missing_headers = []
            for header in cors_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if not missing_headers:
                self.log_test("CORS Headers", True, "All required CORS headers present")
            else:
                self.log_test("CORS Headers", False, f"Missing headers: {missing_headers}")
                
        except Exception as e:
            self.log_test("CORS Headers", False, f"Exception: {str(e)}")
    
    def test_endpoints_availability(self):
        """Test all endpoints are available"""
        endpoints = [
            ('GET', '/otp/status'),
            ('POST', '/otp/send'),
            ('POST', '/otp/verify'),
            ('OPTIONS', '/otp/status')
        ]
        
        for method, endpoint in endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == 'POST':
                    response = requests.post(f"{self.base_url}{endpoint}", json={}, timeout=10)
                elif method == 'OPTIONS':
                    response = requests.options(f"{self.base_url}{endpoint}", timeout=10)
                
                # Any response (even 400/500) means endpoint exists
                if response.status_code in [200, 400, 405, 500]:
                    self.log_test(f"Endpoint: {method} {endpoint}", True, f"HTTP {response.status_code}")
                else:
                    self.log_test(f"Endpoint: {method} {endpoint}", False, f"Unexpected HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Endpoint: {method} {endpoint}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting OTP API Test Suite")
        print("=" * 50)
        
        # Run tests
        self.test_health_check()
        self.test_send_otp_validation()
        self.test_verify_otp_validation()
        self.test_cors_headers()
        self.test_endpoints_availability()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! Your OTP API is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        
        return passed == total

def main():
    """Main test function"""
    # Get API URL from environment or use default
    api_url = os.getenv('OTP_API_URL', 'https://your-api-gateway-url.amazonaws.com/dev')
    
    print(f"Testing OTP API at: {api_url}")
    print("Note: Update OTP_API_URL environment variable with your actual API Gateway URL")
    print()
    
    # Run tests
    test_suite = OTPTestSuite(api_url)
    success = test_suite.run_all_tests()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
