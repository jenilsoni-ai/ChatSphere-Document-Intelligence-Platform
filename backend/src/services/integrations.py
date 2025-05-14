import aiohttp
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class SlackIntegrationHandler:
    """Handler for Slack integrations"""
    
    def __init__(self):
        self.session = None
        self._bot_token = None
        self._signing_secret = None
        self._chatbot_settings = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def set_credentials(self, bot_token: str, signing_secret: str, chatbot_settings: Optional[Dict[str, Any]] = None):
        """Set bot credentials and chatbot settings"""
        self._bot_token = bot_token
        self._signing_secret = signing_secret
        self._chatbot_settings = chatbot_settings
    
    async def verify_request_signature(self, timestamp: str, signature: str, body: str) -> bool:
        """Verify Slack request signature"""
        if not self._signing_secret:
            logger.error("Signing secret not configured")
            return False
            
        # Create base string
        base_string = f"v0:{timestamp}:{body}"
        
        # Create signature
        signature_bytes = base_string.encode('utf-8')
        slack_signing_secret = self._signing_secret.encode('utf-8')
        
        import hmac
        import hashlib
        
        # Calculate expected signature
        hex_hash = hmac.new(slack_signing_secret, signature_bytes, hashlib.sha256).hexdigest()
        calculated_signature = f"v0={hex_hash}"
        
        return hmac.compare_digest(calculated_signature, signature)
    
    async def handle_event(self, event_data: dict) -> Optional[dict]:
        """Handle Slack events"""
        try:
            event_type = event_data.get("type")
            
            if event_type == "url_verification":
                # Handle URL verification challenge
                return {"challenge": event_data.get("challenge")}
                
            elif event_type == "event_callback":
                event = event_data.get("event", {})
                
                if event.get("type") == "message" and not event.get("bot_id"):
                    # Handle user message
                    return await self._handle_message_event(event)
                    
            return None
            
        except Exception as e:
            logger.error(f"Error handling Slack event: {str(e)}")
            return None
    
    async def _handle_message_event(self, event: dict) -> Optional[dict]:
        """Handle message events from Slack"""
        try:
            channel = event.get("channel")
            text = event.get("text", "").strip()
            user = event.get("user")
            thread_ts = event.get("thread_ts", event.get("ts"))
            
            if not text or not channel:
                return None
            
            # Get bot response using LLM
            from ..services.llm import LLMService
            from ..models.chatbot import ChatbotSettings
            
            llm = LLMService()
            
            # Create settings from stored configuration
            settings = None
            if self._chatbot_settings:
                settings = ChatbotSettings(**self._chatbot_settings)
            else:
                # Use default settings
                settings = ChatbotSettings()
                settings.role = "AI assistant"
                settings.instructions = "You are a helpful AI assistant. Provide clear and concise responses."
            
            response = await llm.generate_response(
                message=text,
                chat_history=[],  # Could implement thread history here
                settings=settings,
                context=None
            )
            
            # Send response back to Slack
            await self._send_bot_message(channel, response, thread_ts)
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Error handling message event: {str(e)}")
            return None
    
    async def _send_bot_message(self, channel: str, text: str, thread_ts: Optional[str] = None) -> bool:
        """Send message using bot token"""
        if not self._bot_token:
            logger.error("Bot token not configured")
            return False
            
        try:
            session = await self._get_session()
            
            payload = {
                "channel": channel,
                "text": text
            }
            
            if thread_ts:
                payload["thread_ts"] = thread_ts
            
            headers = {
                "Authorization": f"Bearer {self._bot_token}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=headers
            ) as response:
                data = await response.json()
                return data.get("ok", False)
                
        except Exception as e:
            logger.error(f"Error sending bot message: {str(e)}")
            return False
    
    async def validate_webhook(self, webhook_url: str) -> bool:
        """
        Validate a Slack webhook URL by sending a test message
        Returns True if successful, False otherwise
        """
        try:
            session = await self._get_session()
            
            test_message = {
                "text": "🔄 Testing webhook connection...",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*ChatSphere Integration Test*\nThis is a test message to verify the webhook configuration."
                        }
                    }
                ]
            }
            
            async with session.post(webhook_url, json=test_message) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error validating Slack webhook: {str(e)}")
            return False
    
    async def send_message(self, webhook_url: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a message to Slack
        Returns True if successful, False otherwise
        """
        try:
            session = await self._get_session()
            
            # Format the message with metadata if provided
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                }
            ]
            
            if metadata:
                # Add metadata as context
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*From:* {metadata.get('source', 'Unknown')}"
                        }
                    ]
                })
            
            payload = {
                "text": message,  # Fallback text
                "blocks": blocks
            }
            
            async with session.post(webhook_url, json=payload) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return False
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

class DiscordIntegrationHandler:
    """Handler for Discord integrations"""
    
    def __init__(self):
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def validate_webhook(self, webhook_url: str) -> bool:
        """
        Validate a Discord webhook URL by sending a test message
        Returns True if successful, False otherwise
        """
        try:
            session = await self._get_session()
            
            test_message = {
                "content": "🔄 Testing webhook connection...",
                "embeds": [{
                    "title": "ChatSphere Integration Test",
                    "description": "This is a test message to verify the webhook configuration.",
                    "color": 0x007AFF  # Blue color
                }]
            }
            
            async with session.post(webhook_url, json=test_message) as response:
                return response.status == 204  # Discord returns 204 on success
                
        except Exception as e:
            logger.error(f"Error validating Discord webhook: {str(e)}")
            return False
    
    async def send_message(self, webhook_url: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a message to Discord
        Returns True if successful, False otherwise
        """
        try:
            session = await self._get_session()
            
            # Create embed with message and metadata
            embed = {
                "description": message,
                "color": 0x007AFF  # Blue color
            }
            
            if metadata:
                embed["fields"] = [{
                    "name": "Source",
                    "value": metadata.get("source", "Unknown"),
                    "inline": True
                }]
            
            payload = {
                "content": None,  # No plain text content
                "embeds": [embed]
            }
            
            async with session.post(webhook_url, json=payload) as response:
                success = response.status == 204  # Discord returns 204 on success
                if not success:
                    error_text = await response.text()
                    logger.error(f"Error sending Discord message. Status: {response.status}, Response: {error_text}")
                return success
                
        except Exception as e:
            logger.error(f"Error sending Discord message: {str(e)}")
            return False
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

class WebsiteIntegrationHandler:
    """Handler for Website integrations with custom domains"""
    
    def __init__(self):
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def generate_verification_token(self, domain: str) -> str:
        """Generate a unique verification token for DNS verification"""
        return f"chatsphere-verify-{uuid.uuid4().hex[:8]}"
    
    def get_verification_record(self, domain: str, token: str) -> Dict[str, str]:
        """Get the DNS TXT record details for domain verification"""
        return {
            "type": "TXT",
            "name": f"_chatsphere-verify.{domain}",
            "value": token,
            "instructions": f"Add a TXT record to your domain with:\nName: _chatsphere-verify\nValue: {token}"
        }
    
    async def verify_domain(self, domain: str, token: str) -> bool:
        """
        Verify domain ownership by checking DNS TXT record
        Returns True if verified, False otherwise
        """
        try:
            import dns.resolver
            
            # Remove protocol if present
            domain = domain.replace("https://", "").replace("http://", "").strip("/")
            
            # Try to resolve the TXT record
            try:
                answers = dns.resolver.resolve(f"_chatsphere-verify.{domain}", "TXT")
                
                # Check if our verification token is in any of the TXT records
                for rdata in answers:
                    for txt_string in rdata.strings:
                        if txt_string.decode() == token:
                            return True
                
                logger.warning(f"Verification token not found in DNS records for {domain}")
                return False
                
            except dns.resolver.NXDOMAIN:
                logger.warning(f"Verification DNS record not found for {domain}")
                return False
            except dns.resolver.NoAnswer:
                logger.warning(f"No TXT records found for {domain}")
                return False
            except Exception as e:
                logger.error(f"DNS resolution error for {domain}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying domain {domain}: {str(e)}")
            return False
    
    async def setup_domain(self, domain: str) -> Dict[str, Any]:
        """
        Get the required DNS records for setting up the custom domain
        Returns the DNS records that need to be added
        """
        # Remove protocol if present
        domain = domain.replace("https://", "").replace("http://", "").strip("/")
        
        # Generate CNAME record details
        return {
            "records": [
                {
                    "type": "CNAME",
                    "name": domain,
                    "value": "chatsphere.app",
                    "instructions": f"Add a CNAME record to your domain with:\nName: {domain}\nValue: chatsphere.app"
                }
            ],
            "instructions": "Add these DNS records to your domain to complete the setup."
        }
    
    async def check_domain_setup(self, domain: str) -> bool:
        """
        Check if the domain is properly set up with CNAME record
        Returns True if setup is correct, False otherwise
        """
        try:
            import dns.resolver
            
            # Remove protocol if present
            domain = domain.replace("https://", "").replace("http://", "").strip("/")
            
            try:
                # Try to resolve the CNAME record
                answers = dns.resolver.resolve(domain, "CNAME")
                
                # Check if it points to our domain
                for rdata in answers:
                    if str(rdata.target).rstrip(".") == "chatsphere.app":
                        return True
                
                logger.warning(f"Domain {domain} CNAME record does not point to chatsphere.app")
                return False
                
            except dns.resolver.NXDOMAIN:
                logger.warning(f"Domain {domain} not found")
                return False
            except dns.resolver.NoAnswer:
                logger.warning(f"No CNAME record found for {domain}")
                return False
            except Exception as e:
                logger.error(f"DNS resolution error for {domain}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking domain setup for {domain}: {str(e)}")
            return False
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Create global instances
slack_handler = SlackIntegrationHandler()
discord_handler = DiscordIntegrationHandler()
website_handler = WebsiteIntegrationHandler() 