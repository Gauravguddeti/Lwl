#!/usr/bin/env python3
import json
import logging
import os

from mail_service import MailService


logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Content-Type': 'application/json'
}


def create_response(status_code: int, body: dict) -> dict:
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }


def lambda_handler(event, context):
    try:
        mail_service = MailService()

        http_method = (event or {}).get('httpMethod', 'POST')
        path = (event or {}).get('path', '/email/send')

        if http_method == 'OPTIONS':
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

        if http_method == 'GET':
            if 'status' in path:
                return create_response(200, {
                    'success': True,
                    'service': 'email',
                    'region': mail_service.aws_region
                })
            return create_response(404, {
                'success': False,
                'error': 'Endpoint not found. Use GET /email/status.'
            })

        if http_method == 'POST':
            body_value = event.get('body', '{}')
            mail_data = json.loads(body_value) if isinstance(body_value, str) else (body_value or {})

            if 'bulk' in path:
                result = mail_service.send_bulk_email(mail_data)
            else:
                result = mail_service.send_email(mail_data)

            return create_response(200 if result.get('success') else 400, result)

        return create_response(405, {
            'success': False,
            'error': f'Method {http_method} not allowed. Use GET, POST, OPTIONS.'
        })

    except json.JSONDecodeError:
        return create_response(400, {'success': False, 'error': 'Invalid JSON in request body'})
    except Exception as exc:
        logger.exception('Unhandled error')
        return create_response(500, {'success': False, 'error': f'Internal server error: {exc}'})


def test_handler():
    status_event = {'httpMethod': 'GET', 'path': '/email/status'}
    print(lambda_handler(status_event, None))

    send_event = {
        'httpMethod': 'POST',
        'path': '/email/send',
        'body': json.dumps({
            'to_addresses': ['test@example.com'],
            'subject': 'Test Email',
            'body_text': 'Hello from Lambda email service.'
        })
    }
    print(lambda_handler(send_event, None))

    bulk_event = {
        'httpMethod': 'POST',
        'path': '/email/bulk',
        'body': json.dumps({
            'recipients': [
                {'to_addresses': ['a@example.com'], 'subject': 'Hi A', 'body_text': 'Hello A'},
                {'to_addresses': ['b@example.com'], 'subject': 'Hi B', 'body_text': 'Hello B'}
            ]
        })
    }
    print(lambda_handler(bulk_event, None))


if __name__ == '__main__':
    test_handler()


