#!/usr/bin/env python
"""Email configuration diagnostic script."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diabetes_web.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail, get_connection
import smtplib

print("=" * 70)
print("EMAIL CONFIGURATION DIAGNOSTIC")
print("=" * 70)

# Check configuration
print("\n[1] Configuration Check:")
print("-" * 70)
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else '⚠️ EMPTY'}")
print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else '⚠️ EMPTY'}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL if settings.DEFAULT_FROM_EMAIL else '⚠️ EMPTY'}")

# Validate configuration
print("\n[2] Configuration Validation:")
print("-" * 70)

issues = []

if not settings.EMAIL_HOST_USER:
    issues.append("❌ EMAIL_HOST_USER is empty! Add to .env: EMAIL_HOST_USER=your-email@gmail.com")

if not settings.EMAIL_HOST_PASSWORD:
    issues.append("❌ EMAIL_HOST_PASSWORD is empty! Add to .env: EMAIL_HOST_PASSWORD=your-16-char-password")

if not settings.DEFAULT_FROM_EMAIL:
    issues.append("❌ DEFAULT_FROM_EMAIL is empty! Add to .env: DEFAULT_FROM_EMAIL=your-email@gmail.com")

if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
    issues.append("⚠️ EMAIL_BACKEND is set to console! Emails will print to console, not send.")
    issues.append("   Change in .env to: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")

if issues:
    print("\n".join(issues))
else:
    print("✅ All configuration values present!")

# Test SMTP connection
print("\n[3] SMTP Connection Test:")
print("-" * 70)

if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
    print("⚠️ Skipping connection test - credentials missing")
else:
    try:
        print(f"Attempting to connect to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
        print("✅ Connected to SMTP server")
        
        print(f"Starting TLS encryption...")
        server.starttls()
        print("✅ TLS connection established")
        
        print(f"Authenticating with {settings.EMAIL_HOST_USER}...")
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✅ Authentication successful!")
        
        server.quit()
        print("✅ SMTP connection test PASSED")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check your Email_HOST_USER and EMAIL_HOST_PASSWORD")
        print("   Make sure you're using the 16-character App Password (not Gmail password)")
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("   Check firewall, network, and Gmail security settings")

# Test email sending
print("\n[4] Django Email Send Test:")
print("-" * 70)

if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
    print("⚠️ Skipping email test - credentials missing")
elif settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
    print("⚠️ Skipping email test - backend is console")
else:
    try:
        print("Attempting to send test email...")
        result = send_mail(
            'Test Email - Diabetes Prediction App',
            'If you see this, email is configured correctly!',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        if result:
            print(f"✅ Email sent successfully (recipients: {result})")
        else:
            print("❌ Email send returned 0 recipients")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 70)
print("DIAGNOSTICS COMPLETE")
print("=" * 70)

# Recommendations
print("\n📋 RECOMMENDED FIXES:")
print("-" * 70)

if not settings.EMAIL_HOST_USER:
    print("1. Update .env file:")
    print("   EMAIL_HOST_USER=your-email@gmail.com")
    
if not settings.EMAIL_HOST_PASSWORD:
    print("2. Generate Gmail App Password:")
    print("   - Go to https://myaccount.google.com/apppasswords")
    print("   - Select 'Mail' and 'Windows Computer'")
    print("   - Copy the 16-character password")
    print("   - Add to .env: EMAIL_HOST_PASSWORD=<paste-password-here>")

if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
    print("3. Update .env to enable SMTP:")
    print("   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")

if not issues:
    print("✅ No issues found! Email should be working.")
