import os
import urllib.parse
import base64
from typing import Dict, Any
from urllib import request as urlrequest
from urllib.parse import urlencode


class IVRService:
    def __init__(self):
        self.aws_region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION') or 'us-east-1'
        # Optional WebSocket stream URL for real-time media (if you have it)
        self.media_stream_ws = os.getenv('IVR_STREAM_URL')  # e.g., wss://your-host/stream

    def _parse_form_or_json(self, body):
        if not body:
            return {}
        # Try URL-encoded form first (common for Twilio)
        try:
            parsed = urllib.parse.parse_qs(body)
            return {k: v[0] if isinstance(v, list) and v else v for k, v in parsed.items()}
        except Exception:
            pass
        # Fallback: treat as JSON if API Gateway passed raw JSON string (not typical for Twilio)
        try:
            import json
            return json.loads(body)
        except Exception:
            return {}

    def build_twiml_response(self, body) -> str:
        """Return TwiML similar to existing flow in ai_ivr_api.py."""
        params = self._parse_form_or_json(body)
        partner_name = params.get('PartnerName') or 'your organization'
        contact_person = params.get('ContactPerson') or 'the right person'
        program_name = params.get('ProgramName') or 'our program'

        greeting = f"Hello, this is calling from our education services team. Am I speaking with {contact_person}?"
        pitch = (
            f"We're reaching out regarding our {program_name} program specifically designed for institutions like {partner_name}."
        )
        benefit = (
            "This program offers industry-recognized certification with flexible scheduling. "
            "Would you be interested in learning more about how this can benefit your organization?"
        )

        if self.media_stream_ws:
            # Real-time media streaming path (Twilio <Connect><Stream>)
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">{greeting}</Say>
  <Pause length="1"/>
  <Say voice="alice">{pitch}</Say>
  <Pause length="1"/>
  <Say voice="alice">{benefit}</Say>
  <Connect>
    <Stream url="{self.media_stream_ws}" track="both_tracks"/>
  </Connect>
  <Pause length="60"/>
  <Hangup/>
</Response>"""
            return twiml

        # Classic IVR with <Record>, mirroring ai_ivr_api.py
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">{greeting}</Say>
  <Pause length="2"/>
  <Say voice="alice">{pitch}</Say>
  <Pause length="1"/>
  <Say voice="alice">{benefit}</Say>
  <Record maxLength="30" playBeep="true"/>
  <Hangup/>
</Response>"""
        return twiml

    def _parse_json(self, body) -> Dict[str, Any]:
        try:
            import json
            if not body:
                return {}
            if isinstance(body, (dict, list)):
                return body  # already parsed by API Gateway mapping
            return json.loads(body)
        except Exception:
            return {}

    def make_outbound_call(self, body) -> Dict[str, Any]:
        """Initiate an outbound call via Twilio REST API using inline TwiML.

        Required env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
        Optional env: IVR_STATUS_CALLBACK_URL (for call status webhooks)
        """
        data = self._parse_json(body)

        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        status_callback = os.getenv('IVR_STATUS_CALLBACK_URL')

        to_number = (data.get('to') or data.get('phone') or data.get('to_number') or '').strip()
        partner_name = data.get('partner_name') or 'your organization'
        contact_person = data.get('contact_person') or 'the right person'
        program_name = data.get('program_name') or 'our program'

        if not account_sid or not auth_token or not from_number:
            return {'success': False, 'error': 'Missing Twilio configuration in environment'}
        if not to_number:
            return {'success': False, 'error': 'Missing to number'}

        greeting = f"Hello, this is calling from our education services team. Am I speaking with {contact_person}?"
        pitch = (
            f"We're reaching out regarding our {program_name} program specifically designed for institutions like {partner_name}."
        )
        benefit = (
            "This program offers industry-recognized certification with flexible scheduling. "
            "Would you be interested in learning more about how this can benefit your organization?"
        )

        if self.media_stream_ws:
            twiml = f"""
<Response>
  <Say voice="alice">{greeting}</Say>
  <Pause length="1"/>
  <Say voice="alice">{pitch}</Say>
  <Pause length="1"/>
  <Say voice="alice">{benefit}</Say>
  <Connect>
    <Stream url="{self.media_stream_ws}" track="both_tracks"/>
  </Connect>
  <Pause length="60"/>
  <Hangup/>
</Response>""".strip()
        else:
            twiml = f"""
<Response>
  <Say voice="alice">{greeting}</Say>
  <Pause length="2"/>
  <Say voice="alice">{pitch}</Say>
  <Pause length="1"/>
  <Say voice="alice">{benefit}</Say>
  <Record maxLength="30" playBeep="true"/>
  <Hangup/>
</Response>""".strip()

        api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
        payload = {
            'To': to_number,
            'From': from_number,
            'Twiml': twiml
        }
        if status_callback:
            payload['StatusCallback'] = status_callback

        encoded = urlencode(payload).encode('utf-8')
        req = urlrequest.Request(api_url, data=encoded, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        basic_token = base64.b64encode(f"{account_sid}:{auth_token}".encode('utf-8')).decode('ascii')
        req.add_header('Authorization', f'Basic {basic_token}')

        try:
            with urlrequest.urlopen(req) as resp:
                resp_body = resp.read().decode('utf-8')
                import json
                parsed = json.loads(resp_body)
                return {
                    'success': True,
                    'message': 'Call initiated',
                    'call_sid': parsed.get('sid'),
                    'to': to_number,
                    'from': from_number
                }
        except Exception as exc:
            return {'success': False, 'error': str(exc)}


