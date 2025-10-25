#!/usr/bin/env python3
"""
Lambda Handler for Integrated Email/SMS API
Wraps the Flask Email/SMS API for AWS Lambda deployment
"""

import os
import sys
import json

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your Email/SMS Flask app
from integrated_email_sms_api import app

def lambda_handler(event, context):
    """
    AWS Lambda handler for Email/SMS API
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        Dict: API Gateway response
    """
    try:
        # Handle API Gateway event
        if 'httpMethod' in event:
            return handle_api_gateway_event(event, context)
        else:
            # Handle other event types
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Unsupported event type'
                })
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Lambda handler error: {str(e)}'
            })
        }

def handle_api_gateway_event(event, context):
    """Handle API Gateway HTTP event"""
    
    # Extract request information
    http_method = event['httpMethod']
    path = event.get('path', '/')
    query_params = event.get('queryStringParameters') or {}
    headers = event.get('headers', {})
    body = event.get('body', '')
    
    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key'
            },
            'body': json.dumps({'message': 'CORS preflight'})
        }
    
    try:
        # Run the Flask app
        with app.test_client() as client:
            if http_method == 'GET':
                response = client.get(path, query_string=query_params, headers=headers)
            elif http_method == 'POST':
                response = client.post(path, data=body, headers=headers, content_type=headers.get('Content-Type', 'application/json'))
            elif http_method == 'PUT':
                response = client.put(path, data=body, headers=headers, content_type=headers.get('Content-Type', 'application/json'))
            elif http_method == 'DELETE':
                response = client.delete(path, headers=headers)
            else:
                response = client.open(method=http_method, path=path, data=body, headers=headers)
            
            # Convert Flask response to API Gateway format
            response_headers = dict(response.headers)
            response_headers['Access-Control-Allow-Origin'] = '*'
            response_headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response_headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
            return {
                'statusCode': response.status_code,
                'headers': response_headers,
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Email/SMS API error: {str(e)}'
            })
        }

if __name__ == '__main__':
    # For local testing
    test_event = {
        'httpMethod': 'GET',
        'path': '/api-status',
        'queryStringParameters': {},
        'headers': {'Content-Type': 'application/json'},
        'body': ''
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))