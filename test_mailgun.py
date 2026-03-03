#!/usr/bin/env python
"""Test Mailgun SMTP configuration."""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diabetes_web.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
import smtplib

print("\n" + "="*70)
print("MAILGUN SMTP CONFIGURATION TEST")
print("="*70 + "\n")

# Check settings
print("[1] Configuration Check:")
print("-" * 70)
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else '(empty)'}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"EMAIL_TIMEOUT: {settings.EMAIL_TIMEOUT}")
print()

# Validate
print("[2] Configuration Validation:")
print("-" * 70)

if not settings.EMAIL_HOST_USER:
    print("❌ EMAIL_HOST_USER is empty!")
    sys.exit(1)

if not settings.EMAIL_HOST_PASSWORD:
    print("❌ EMAIL_HOST_PASSWORD is empty!")
    sys.exit(1)

if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
    print("⚠️  WARNING: EMAIL_BACKEND is set to CONSOLE (not SMTP)")
    print("   This means emails won't actually be sent.")
    sys.exit(1)

print("✅ All configuration values present!")
print()

# Test SMTP connection
print("[3] Direct SMTP Connection Test:")
print("-" * 70)

try:
    smtp_conn = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT)
    print(f"✅ Connected to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    
    smtp_conn.starttls()
    print("✅ TLS connection established")
    
    smtp_conn.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    print(f"✅ Authentication successful with {settings.EMAIL_HOST_USER}")
    
    smtp_conn.quit()
    print("✅ SMTP connection test PASSED")
    print()
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Authentication failed: {e}")
    print("   Check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
    sys.exit(1)
except smtplib.SMTPException as e:
    print(f"❌ SMTP error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Connection error: {e}")
    sys.exit(1)

# Test Django email send
print("[4] Django Email Send Test:")
print("-" * 70)

try:
    subject = "Test Email from Diabetes Prediction App"
    message = "This is a test email from your Mailgun configuration."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient = settings.EMAIL_HOST_USER  # Send to your own email
    
    result = send_mail(
        subject,
        message,
        from_email,
        [recipient],
        fail_silently=False,
    )
    
    if result == 1:
        print(f"✅ Email sent successfully to {recipient}")
        print()
        print("📋 Next steps:")
        print(f"   1. Check your email ({recipient}) for the test message")
        print(f"   2. Check Mailgun logs: https://app.mailgun.com/app/logs")
        print(f"   3. Verify sender address: {from_email}")
    else:
        print(f"⚠️  send_mail() returned {result} (expected 1)")
        
except Exception as e:
    print(f"❌ Error sending email: {type(e).__name__}: {e}")
    sys.exit(1)

print()
print("="*70)
print("TEST COMPLETE")
print("="*70 + "\n")
