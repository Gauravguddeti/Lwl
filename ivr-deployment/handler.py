#!/usr/bin/env python3
import json
import logging

from ivr_service import IVRService


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _json_response(status: int, body: dict) -> dict:
    return {
        'statusCode': status,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }


def _xml_response(status: int, xml_body: str) -> dict:
    return {
        'statusCode': status,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'text/xml'
        },
        'body': xml_body
    }


def lambda_handler(event, context):
    try:
        service = IVRService()

        http_method = (event or {}).get('httpMethod', 'POST')
        path = (event or {}).get('path', '/ivr/voice')

        if http_method == 'OPTIONS':
            return _json_response(200, {'ok': True})

        if http_method == 'GET':
            if 'status' in path or 'health' in path:
                return _json_response(200, {
                    'success': True,
                    'service': 'ivr',
                    'mode': 'twiML-webhook',
                    'region': service.aws_region
                })
            return _json_response(404, {'success': False, 'error': 'Use GET /ivr/status'})

        if http_method == 'POST':
            # Outbound call initiation
            if 'make-call' in path:
                body_value = event.get('body')
                result = service.make_outbound_call(body_value)
                return _json_response(200 if result.get('success') else 400, result)

            # Twilio voice webhook → return TwiML
            if 'voice' in path or 'ivr' in path:
                # Pass raw form/body to service; Twilio may send form-encoded via API Gateway mapping
                body_value = event.get('body')
                twiml = service.build_twiml_response(body_value)
                return _xml_response(200, twiml)

            return _json_response(404, {'success': False, 'error': 'Endpoint not found'})

        return _json_response(405, {'success': False, 'error': f'Method {http_method} not allowed'})

    except Exception as exc:
        logger.exception('IVR Lambda error')
        return _json_response(500, {'success': False, 'error': f'Internal server error: {exc}'})


def test_handler():
    status_event = {'httpMethod': 'GET', 'path': '/ivr/status'}
    print(lambda_handler(status_event, None))

    voice_event = {'httpMethod': 'POST', 'path': '/ivr/voice', 'body': ''}
    res = lambda_handler(voice_event, None)
    print(res['statusCode'], res['headers'].get('Content-Type'))
    print(res['body'])


if __name__ == '__main__':
    test_handler()


