import os
import re
import boto3
from botocore.exceptions import ClientError


class MailService:
    def __init__(self):
        self.aws_region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION') or 'us-east-1'
        self.ses = boto3.client('ses', region_name=self.aws_region)
        self.default_sender = os.getenv('EMAIL_SENDER') or os.getenv('SES_SENDER') or 'no-reply@example.com'

    def _validate_email(self, email: str) -> bool:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ''))

    def _normalize_recipients(self, recipients):
        if not recipients:
            return []
        if isinstance(recipients, str):
            recipients = [recipients]
        return [e for e in recipients if self._validate_email(e)]

    def send_email(self, data: dict) -> dict:
        # Accept multiple common input keys for compatibility with existing handlers
        to_single = data.get('to_email') or data.get('toAddress') or data.get('to_address')
        to_addresses = self._normalize_recipients(
            data.get('to_addresses') or data.get('to') or to_single or []
        )
        cc_addresses = self._normalize_recipients(data.get('cc'))
        bcc_addresses = self._normalize_recipients(data.get('bcc'))
        subject = (data.get('subject') or '').strip()
        body_text = (data.get('body_text') or data.get('text') or data.get('body') or '').strip()
        body_html = (data.get('body_html') or data.get('html') or '').strip()
        sender = (
            data.get('sender_email')
            or data.get('from_email')
            or data.get('from_address')
            or data.get('sender')
            or self.default_sender
        ).strip()

        if not to_addresses:
            return {'success': False, 'error': 'Missing or invalid to_addresses'}
        if not self._validate_email(sender):
            return {'success': False, 'error': 'Invalid sender email'}
        if not subject:
            return {'success': False, 'error': 'Missing subject'}
        if not body_text and not body_html:
            return {'success': False, 'error': 'Provide body_text or body_html'}

        destination = {'ToAddresses': to_addresses}
        if cc_addresses:
            destination['CcAddresses'] = cc_addresses
        if bcc_addresses:
            destination['BccAddresses'] = bcc_addresses

        message = {
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {}
        }
        if body_text:
            message['Body']['Text'] = {'Data': body_text, 'Charset': 'UTF-8'}
        if body_html:
            message['Body']['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}

        try:
            response = self.ses.send_email(
                Source=sender,
                Destination=destination,
                Message=message
            )
            message_id = response.get('MessageId')
            return {
                'success': True,
                'message': 'Email sent successfully',
                'message_id': message_id,
                'to_addresses': to_addresses,
                'sender': sender
            }
        except ClientError as e:
            return {'success': False, 'error': str(e)}

    def send_bulk_email(self, data: dict) -> dict:
        recipients_list = data.get('recipients') or []
        if not isinstance(recipients_list, list) or not recipients_list:
            return {'success': False, 'error': 'recipients must be a non-empty list'}

        results = []
        success_count = 0
        for item in recipients_list:
            item = item or {}
            result = self.send_email(item)
            results.append(result)
            if result.get('success'):
                success_count += 1

        return {
            'success': success_count == len(results),
            'sent': success_count,
            'total': len(results),
            'results': results
        }


