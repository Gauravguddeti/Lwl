"""
Web Dashboard for AI Telecaller System
Provides interface to view partners, events and initiate calls
"""

import logging
from flask import render_template, request, jsonify, redirect, url_for
from app.services.database_service import DatabaseService
from app.services.twilio_service import TwilioService
from app.config.settings import AppConfig

logger = logging.getLogger(__name__)

class DashboardHandler:
    """Handle web dashboard routes and functionality"""
    
    def __init__(self):
        self.config = AppConfig()
        self.db_service = DatabaseService()
        self.twilio_service = TwilioService()
    
    def dashboard_home(self):
        """Main dashboard page with partners and events"""
        try:
            # Get all partners from database
            partners_data = self.db_service.get_all_partners()
            
            # Get recent call logs
            recent_calls = self._get_recent_calls()
            
            # Get system status
            system_status = self._get_system_status()
            
            return render_template('dashboard.html', 
                                 partners=partners_data,
                                 recent_calls=recent_calls,
                                 system_status=system_status)
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def partner_details(self, partner_id):
        """Get detailed view of a specific partner"""
        try:
            partner = self.db_service.get_partner_by_id(partner_id)
            events = self.db_service.get_events_by_partner(partner_id)
            call_history = self.db_service.get_call_history_by_partner(partner_id)
            
            return render_template('partner_details.html',
                                 partner=partner,
                                 events=events,
                                 call_history=call_history)
        except Exception as e:
            logger.error(f"Partner details error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def initiate_call(self):
        """Initiate a call to a specific number"""
        try:
            data = request.get_json()
            phone_number = data.get('phone_number')
            partner_id = data.get('partner_id')
            event_id = data.get('event_id')
            
            if not phone_number:
                return jsonify({'error': 'Phone number is required'}), 400
            
            # Make the call using Twilio
            call_result = self.twilio_service.make_call(
                to_number=phone_number,
                partner_id=partner_id,
                event_id=event_id
            )
            
            if call_result:
                # Log the call in database
                self.db_service.log_call_attempt(
                    partner_id=partner_id,
                    event_id=event_id,
                    phone_number=phone_number,
                    call_sid=call_result.get('call_sid'),
                    status='initiated'
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Call initiated to {phone_number}',
                    'call_sid': call_result.get('call_sid')
                })
            else:
                return jsonify({'error': 'Failed to initiate call'}), 500
                
        except Exception as e:
            logger.error(f"Call initiation error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def bulk_call(self):
        """Initiate bulk calls to multiple partners"""
        try:
            data = request.get_json()
            partner_ids = data.get('partner_ids', [])
            event_id = data.get('event_id')
            
            results = []
            for partner_id in partner_ids:
                partner = self.db_service.get_partner_by_id(partner_id)
                if partner and partner.get('phone'):
                    call_result = self.twilio_service.make_call(
                        to_number=partner['phone'],
                        partner_id=partner_id,
                        event_id=event_id
                    )
                    results.append({
                        'partner_id': partner_id,
                        'phone': partner['phone'],
                        'status': 'success' if call_result else 'failed',
                        'call_sid': call_result.get('call_sid') if call_result else None
                    })
            
            return jsonify({
                'success': True,
                'results': results,
                'total_calls': len(results)
            })
            
        except Exception as e:
            logger.error(f"Bulk call error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_partners_api(self):
        """API endpoint to get partners data"""
        try:
            partners = self.db_service.get_all_partners()
            return jsonify(partners)
        except Exception as e:
            logger.error(f"Get partners API error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_events_api(self):
        """API endpoint to get events data"""
        try:
            events = self.db_service.get_all_events()
            return jsonify(events)
        except Exception as e:
            logger.error(f"Get events API error: {e}")
            return jsonify({'error': str(e)}), 500
    
    def _get_recent_calls(self):
        """Get recent call logs"""
        try:
            # This would get recent calls from your call logs
            return self.db_service.get_recent_calls(limit=10)
        except Exception as e:
            logger.warning(f"Could not get recent calls: {e}")
            return []
    
    def _get_system_status(self):
        """Get current system status"""
        return {
            'status': 'online',
            'twilio_connected': self.twilio_service.test_connection(),
            'database_connected': self.db_service.test_connection(),
            'total_partners': len(self.db_service.get_all_partners() or []),
            'total_events': len(self.db_service.get_all_events() or [])
        }
