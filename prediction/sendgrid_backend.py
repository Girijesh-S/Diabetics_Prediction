"""
Custom Django email backend using SendGrid's API.
More reliable than SMTP for cloud deployments like Render.
"""

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
import logging

logger = logging.getLogger(__name__)


class SendgridBackend(BaseEmailBackend):
    """
    Email backend using SendGrid's REST API.
    
    Configuration:
    - SENDGRID_API_KEY: Your SendGrid API key (from https://app.sendgrid.com/settings/api_keys)
    - DEFAULT_FROM_EMAIL: Sender email address (must be verified in SendGrid)
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_url = "https://api.sendgrid.com/v3/mail/send"
        self.api_key = settings.SENDGRID_API_KEY
        self.fail_silently = fail_silently
        
        if not self.api_key:
            logger.error("SENDGRID_API_KEY is not set in settings")
    
    def send_messages(self, email_messages):
        """Send one or more EmailMessage objects and return the number sent."""
        if not email_messages:
            return 0
        
        msg_count = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                msg_count += 1
        
        return msg_count
    
    def _send(self, message):
        """
        Send a single EmailMessage using SendGrid API.
        Returns True if successful, False otherwise.
        """
        if not self.api_key:
            error_msg = "SENDGRID_API_KEY is not configured"
            logger.error(error_msg)
            if not self.fail_silently:
                raise Exception(error_msg)
            return False
        
        try:
            # Build SendGrid email structure
            email_data = {
                "personalizations": [
                    {
                        "to": [{"email": recipient} for recipient in message.to],
                        "subject": message.subject,
                    }
                ],
                "from": {"email": message.from_email},
                "content": [
                    {
                        "type": "text/plain" if message.content_subtype == "plain" else "text/html",
                        "value": message.body,
                    }
                ],
            }
            
            # Add CC recipients if any
            if message.cc:
                email_data["personalizations"][0]["cc"] = [
                    {"email": cc} for cc in message.cc
                ]
            
            # Add BCC recipients if any
            if message.bcc:
                email_data["personalizations"][0]["bcc"] = [
                    {"email": bcc} for bcc in message.bcc
                ]
            
            # Add reply-to if set
            if message.reply_to:
                email_data["reply_to"] = {
                    "email": message.reply_to[0]
                }
            
            # Handle attachments
            if message.attachments:
                attachments = []
                for attachment in message.attachments:
                    if isinstance(attachment, tuple):
                        filename, content, mimetype = attachment
                        import base64
                        attachments.append({
                            "filename": filename,
                            "type": mimetype,
                            "disposition": "attachment",
                            "content": base64.b64encode(content).decode() if isinstance(content, bytes) else content,
                        })
                if attachments:
                    email_data["attachments"] = attachments
            
            # Send request to SendGrid
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(
                self.api_url,
                json=email_data,
                headers=headers,
                timeout=30
            )
            
            # Check if request was successful (202 is expected for SendGrid)
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {message.to}")
                return True
            else:
                error_msg = f"SendGrid API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                if not self.fail_silently:
                    raise Exception(error_msg)
                return False
        
        except requests.exceptions.Timeout:
            error_msg = "SendGrid API request timed out"
            logger.error(error_msg)
            if not self.fail_silently:
                raise Exception(error_msg)
            return False
        
        except requests.exceptions.RequestException as e:
            error_msg = f"SendGrid API request failed: {str(e)}"
            logger.error(error_msg)
            if not self.fail_silently:
                raise Exception(error_msg)
            return False
        
        except Exception as e:
            error_msg = f"Error sending email via SendGrid: {str(e)}"
            logger.error(error_msg)
            if not self.fail_silently:
                raise
            return False
