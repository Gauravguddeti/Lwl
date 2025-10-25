"""
Ngrok Manager for tunnel management
Handles ngrok tunnel creation and webhook URL management
"""

import logging
import subprocess
import requests
import time
import os

logger = logging.getLogger(__name__)

class NgrokManager:
    """Manage ngrok tunnels for webhook endpoints"""
    
    def __init__(self, auth_token=None, port=5000):
        self.auth_token = auth_token
        self.port = port
        self.tunnel_url = None
        self.process = None
    
    def start_tunnel(self):
        """Start ngrok tunnel and return webhook URL"""
        try:
            # Configure ngrok auth token if provided
            if self.auth_token:
                subprocess.run(['ngrok', 'config', 'add-authtoken', self.auth_token], 
                             check=True, capture_output=True)
                logger.info("✅ Ngrok auth token configured")
            
            # Start ngrok tunnel
            logger.info(f"🌐 Starting ngrok tunnel on port {self.port}...")
            self.process = subprocess.Popen([
                'ngrok', 'http', str(self.port), '--log=stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for tunnel to be ready with retries
            max_retries = 10
            for attempt in range(max_retries):
                time.sleep(2)  # Wait 2 seconds between attempts
                tunnel_url = self._get_tunnel_url()
                if tunnel_url:
                    self.tunnel_url = tunnel_url
                    logger.info(f"✅ Ngrok tunnel active: {tunnel_url}")
                    return tunnel_url
                logger.info(f"⏳ Waiting for ngrok tunnel... (attempt {attempt + 1}/{max_retries})")
            
            logger.error("❌ Failed to get ngrok tunnel URL after all retries")
            return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Ngrok auth token configuration failed: {e}")
            return None
        except FileNotFoundError:
            logger.error("❌ Ngrok not found. Please install ngrok first.")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to start ngrok tunnel: {e}")
            return None
    
    def _get_tunnel_url(self):
        """Get tunnel URL from ngrok local API"""
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                for tunnel in tunnels:
                    if tunnel.get('config', {}).get('addr') == f'http://localhost:{self.port}':
                        public_url = tunnel.get('public_url', '')
                        # Ensure HTTPS
                        if public_url.startswith('http://'):
                            public_url = public_url.replace('http://', 'https://')
                        return public_url
                        
            return None
        except requests.exceptions.ConnectionError:
            # Ngrok API not ready yet
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get tunnel URL: {e}")
            return None
    
    def stop_tunnel(self):
        """Stop ngrok tunnel"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait()
                logger.info("✅ Ngrok tunnel stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping ngrok tunnel: {e}")
    
    def get_tunnel_url(self):
        """Get current tunnel URL"""
        return self.tunnel_url
