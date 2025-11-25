#!/usr/bin/env python3
"""
FastAPI Testing Script for AI Telecaller System
Tests all FastAPI endpoints
"""

import requests
import json
import time

def test_endpoint(method, url, data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}
        
        result = {
            "endpoint": url,
            "method": method,
            "status_code": response.status_code,
            "success": response.status_code == expected_status,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
        }
        
        return result
        
    except requests.exceptions.ConnectionError:
        return {
            "endpoint": url,
            "method": method,
            "status_code": "CONNECTION_ERROR",
            "success": False,
            "response": "Could not connect to server"
        }
    except Exception as e:
        return {
            "endpoint": url,
            "method": method,
            "status_code": "ERROR",
            "success": False,
            "response": str(e)
        }

def test_fastapi_main():
    """Test main FastAPI application"""
    print("Testing FastAPI Main Application (Port 8000)")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    results = []
    
    # Test health check
    result = test_endpoint("GET", f"{base_url}/")
    results.append(result)
    print(f"Health Check: {'PASS' if result['success'] else 'FAIL'} - {result['status_code']}")
    
    # Test SMS endpoints
    sms_data = {
        "phone_number": "+1234567890",
        "message": "Test message from FastAPI"
    }
    result = test_endpoint("POST", f"{base_url}/sms/send", sms_data)
    results.append(result)
    print(f"SMS Send: {'PASS' if result['success'] else 'FAIL'} - {result['status_code']}")
    
    # Test Email endpoints
    email_data = {
        "to_email": "test@example.com",
        "subject": "Test Email from FastAPI",
        "body": "This is a test email from the FastAPI system."
    }
    result = test_endpoint("POST", f"{base_url}/email", email_data)
    results.append(result)
    print(f"Email Send: {'PASS' if result['success'] else 'FAIL'} - {result['status_code']}")
    
    # Test Call endpoints
    call_data = {
        "to_number": "+1234567890",
        "system_prompt": "You are calling to discuss educational programs.",
        "call_metadata": {
            "partner_name": "Test Partner",
            "program_name": "Test Program"
        }
    }
    result = test_endpoint("POST", f"{base_url}/call/start", call_data)
    results.append(result)
    print(f"Call Start: {'PASS' if result['success'] else 'FAIL'} - {result['status_code']}")
    
    return results

def test_fastapi_email_sms():
    """Test Email/SMS FastAPI application"""
    print("\nTesting FastAPI Email/SMS Application (Port 8001)")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    results = []
    
    # Test health check
    result = test_endpoint("GET", f"{base_url}/")
    results.append(result)
    print(f"Health Check: {'PASS' if result['success'] else 'FAIL'} - {result['status_code']}")
    
    # Test SMS endpoints
    sms_data = {
        "phone_number": "+1234567890",
        "message": "Test message from FastAPI Email/SMS"
    }
    result = test_endpoint("POST", f"{base_url}/sms/send", sms_data)
    results.append(result)
    print(f"SMS Send: {'PASS' if result['success'] else 'FAIL'} - {result['status_code']}")
    
    # Test Email endpoints
    email_data = {
        "to_email": "test@example.com",
        "subject": "Test Email from FastAPI Email/SMS",
        "body": "This is a test email from the FastAPI Email/SMS system."
    }
    result = test_endpoint("POST", f"{base_url}/email", email_data)
    results.append(result)
    print(f"Email Send: {'PASS' if result['success'] else 'FAIL'} - {result['status_code']}")
    
    return results

def main():
    """Run all FastAPI tests"""
    print("FastAPI Testing Suite for AI Telecaller System")
    print("=" * 60)
    print("Make sure both FastAPI servers are running:")
    print("  - Main API: python fastapi_main.py (port 8000)")
    print("  - Email/SMS API: python fastapi_email_sms.py (port 8001)")
    print("=" * 60)
    print()
    
    all_results = []
    
    # Test main FastAPI app
    main_results = test_fastapi_main()
    all_results.extend(main_results)
    
    # Test email/SMS FastAPI app
    email_sms_results = test_fastapi_email_sms()
    all_results.extend(email_sms_results)
    
    # Summary
    print("\nTest Summary")
    print("=" * 50)
    total_tests = len(all_results)
    successful_tests = sum(1 for r in all_results if r['success'])
    failed_tests = total_tests - successful_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests} PASS")
    print(f"Failed: {failed_tests} FAIL")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\nFailed Tests:")
        print("-" * 30)
        for result in all_results:
            if not result['success']:
                print(f"FAIL {result['method']} {result['endpoint']} - {result['status_code']}")
                if 'response' in result and result['response']:
                    print(f"   Response: {result['response']}")
    
    print("\n" + "=" * 60)
    print("FastAPI Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
