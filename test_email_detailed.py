import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diabetes_web.settings')
django.setup()

import smtplib
from django.conf import settings
import ssl

print("Detailed Gmail SMTP Test")
print("="*70)
print(f"HOST: {settings.EMAIL_HOST}")
print(f"PORT: {settings.EMAIL_PORT}")
print(f"USER: {settings.EMAIL_HOST_USER}")
print(f"USE_TLS: {settings.EMAIL_USE_TLS}")
print("="*70)

try:
    # Test SMTP connection directly
    print("\n1. Testing SMTP connection...")
    context = ssl.create_default_context()
    
    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30) as server:
        print("   ✅ Connected to SMTP server")
        
        # Start TLS
        server.starttls(context=context)
        print("   ✅ TLS started")
        
        # Login
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("   ✅ Login successful")
        
        # Send email
        from_addr = settings.DEFAULT_FROM_EMAIL
        to_addr = 'girijeshkumar2003@gmail.com'
        
        message = f"""Subject: Gmail SMTP Direct Test

This is a direct SMTP test email.
If you see this, Gmail SMTP is working correctly!"""
        
        server.sendmail(from_addr, to_addr, message)
        print(f"   ✅ Email sent directly via SMTP")
        print(f"      From: {from_addr}")
        print(f"      To: {to_addr}")

except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Check your inbox and SPAM folder for the email!")
print("="*70)
