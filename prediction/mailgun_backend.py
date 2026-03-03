"""
Custom Django email backend using Mailgun's HTTP API.
More reliable than SMTP, especially on hosted platforms like Render.

HOW TO GET MAILGUN API KEY:
1. Go to https://mailgun.com/app/dashboard
2. Login with your Mailgun account
3. Find your domain (e.g., sandbox0f8ba03a66144746879546f692acd231.mailgun.org)
4. Click on "Settings" → "API Security"
5. Copy the "Mailgun API Key" (starts with "key-")
6. Set EMAIL_HOST_PASSWORD to this API key in your .env and Render environment

AUTHENTICATION:
- Username: api (always this literal string)
- Password: Your Mailgun API key (not the SMTP password)
"""

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
import logging

logger = logging.getLogger(__name__)


class MailgunEmailBackend(BaseEmailBackend):
    """
    Email backend using Mailgun's REST API.
    
    Configuration:
    - EMAIL_HOST: Your Mailgun domain (e.g., sandbox0f8ba03a66144746879546f692acd231.mailgun.org)
    - EMAIL_HOST_USER: Your full Mailgun email (e.g., dbp@sandbox...)
    - EMAIL_HOST_PASSWORD: Your Mailgun API key (from dashboard, not SMTP password)
    - DEFAULT_FROM_EMAIL: Sender email address
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_url = f"https://api.mailgun.net/v3/{settings.EMAIL_HOST}/messages"
        self.api_key = settings.EMAIL_HOST_PASSWORD
        self.fail_silently = fail_silently
        
        # Log a warning if API key looks like SMTP password (not starting with "key-")
        if not self.api_key.startswith('key-'):
            logger.warning(
                "Mailgun API key does not match expected format (should start with 'key-'). "
                "Make sure you're using the actual API key from Mailgun dashboard, not the SMTP password. "
                "Get your API key from: https://mailgun.com/app/dashboard → Domain → Settings → API Security"
            )
    
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
        Send a single EmailMessage using Mailgun API.
        Returns True if successful, False otherwise.
        """
        try:
            # Prepare the data for Mailgun API
            data = {
                'from': message.from_email,
                'to': message.to,
                'subject': message.subject,
                'text': message.body if not message.content_subtype == 'html' else None,
                'html': message.body if message.content_subtype == 'html' else None,
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Handle attachments
            files = []
            if message.attachments:
                for attachment in message.attachments:
                    if isinstance(attachment, tuple):
                        filename, content, mimetype = attachment
                        files.append(('attachment', (filename, content, mimetype)))
                    else:
                        # If it's just a file object
                        files.append(('attachment', attachment))
            
            # Send request to Mailgun
            response = requests.post(
                self.api_url,
                auth=('api', self.api_key),
                data=data,
                files=files if files else None,
                timeout=30
            )
            
            # Check if request was successful
            if response.status_code in [200, 201]:
                logger.info(f"Email sent successfully to {message.to}")
                return True
            else:
                error_msg = f"Mailgun API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                if not self.fail_silently:
                    raise Exception(error_msg)
                else:
                    print(f"Warning: {error_msg}")
                    return False
        
        except requests.exceptions.Timeout:
            error_msg = "Mailgun API request timed out"
            logger.error(error_msg)
            if not self.fail_silently:
                raise Exception(error_msg)
            else:
                print(f"Warning: {error_msg}")
                return False
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Mailgun API request failed: {str(e)}"
            logger.error(error_msg)
            if not self.fail_silently:
                raise Exception(error_msg)
            else:
                print(f"Warning: {error_msg}")
                return False
        
        except Exception as e:
            error_msg = f"Error sending email via Mailgun: {str(e)}"
            logger.error(error_msg)
            if not self.fail_silently:
                raise
            else:
                print(f"Warning: {error_msg}")
                return False
