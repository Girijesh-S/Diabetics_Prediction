#!/usr/bin/env python
"""Test script to verify email functionality has been removed."""
import os
import django
from django.urls import reverse, NoReverseMatch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diabetes_web.settings')
django.setup()

print("\n" + "="*60)
print("TESTING EMAIL FUNCTIONALITY REMOVAL")
print("="*60)

# Test 1: Check if password reset routes are removed
print("\n[TEST 1] Password Reset Routes:")
password_routes = ['password_reset', 'password_reset_done', 'password_reset_confirm']
for route in password_routes:
    try:
        reverse(f'prediction:{route}')
        print(f"  ❌ {route}: FOUND (FAILED - should be removed)")
    except NoReverseMatch:
        print(f"  ✓ {route}: NOT FOUND (SUCCESS)")

# Test 2: Check if email_report route is removed
print("\n[TEST 2] Email Report Route:")
try:
    reverse('prediction:email_report')
    print(f"  ❌ email_report: FOUND (FAILED - should be removed)")
except NoReverseMatch:
    print(f"  ✓ email_report: NOT FOUND (SUCCESS)")

# Test 3: Check if PDF report route still exists
print("\n[TEST 3] PDF Report Route (should still exist):")
try:
    reverse('prediction:pdf_report', kwargs={'pk': 1})
    print(f"  ✓ pdf_report: FOUND (SUCCESS)")
except NoReverseMatch:
    print(f"  ❌ pdf_report: NOT FOUND (FAILED - should exist)")

# Test 4: Test key routes still work
print("\n[TEST 4] Key Routes (should still work):")
key_routes = ['home', 'register', 'login', 'logout', 'predict', 'history', 'dashboard']
for route in key_routes:
    try:
        reverse(f'prediction:{route}')
        print(f"  ✓ {route}: OK")
    except NoReverseMatch:
        print(f"  ❌ {route}: FAILED")

# Test 5: Check if email_report view is removed
print("\n[TEST 5] Email Report Function:")
try:
    from prediction import views
    if hasattr(views, 'email_report'):
        print(f"  ❌ email_report function: FOUND (should be removed)")
    else:
        print(f"  ✓ email_report function: NOT FOUND (SUCCESS)")
except Exception as e:
    print(f"  ❌ Error checking for email_report: {e}")

# Test 6: Check registration form email field
print("\n[TEST 6] Registration Form Email Field:")
try:
    from prediction.forms import RegisterForm
    form = RegisterForm()
    if 'email' in form.fields:
        email_field = form.fields['email']
        if email_field.required:
            print(f"  ❌ Email field is REQUIRED (should be optional)")
        else:
            print(f"  ✓ Email field is OPTIONAL (SUCCESS)")
    else:
        print(f"  ❌ Email field not found in form")
except Exception as e:
    print(f"  ❌ Error checking registration form: {e}")

print("\n" + "="*60)
print("EMAIL REMOVAL TEST COMPLETE")
print("="*60 + "\n")
