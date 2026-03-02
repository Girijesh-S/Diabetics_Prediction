# Email Configuration Guide for Diabetes Prediction Website

## Overview
This guide explains how to configure the SMTP email backend to send diabetes risk reports to users.

## Current Configuration
The application is already configured to use **Gmail SMTP** for sending emails. The configuration is stored in your `.env` file and `settings.py`.

---

## Step-by-Step Configuration (Gmail)

### Step 1: Enable 2-Step Verification on Google Account
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google," enable **2-Step Verification**
4. Follow Google's prompts to complete verification

### Step 2: Generate Gmail App Password
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select **Mail** and **Windows Computer** (or your device)
3. Google will generate a **16-character password** (spaces included)
4. Copy this password

### Step 3: Update Your .env File
Edit the `.env` file in your project root and update these fields:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-password-with-spaces
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Important:**
- Replace `your-email@gmail.com` with your actual Gmail address
- Replace `your-16-char-password-with-spaces` with the App Password from Step 2 (keep spaces as-is)
- **NEVER commit `.env` to version control** - it contains sensitive credentials

### Step 4: Verify Configuration (Local Testing)
Run the following command in your terminal:

```bash
python manage.py shell
```

Inside the Python shell:
```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email from Diabetes Prediction App',
    'If you see this, email is configured correctly!',
    settings.DEFAULT_FROM_EMAIL,
    ['your-test-email@gmail.com'],
    fail_silently=False,
)
```

You should receive the test email. If successful, the configuration is working!

---

## Troubleshooting Email Issues

### Issue 1: "Authentication failed" or "Invalid credentials"
**Solution:**
- Verify you're using the **16-character App Password**, not your regular Gmail password
- Ensure 2-Step Verification is enabled
- Check that `EMAIL_HOST_USER` matches your Gmail address exactly

### Issue 2: "Connection refused" or timeout
**Solution:**
- Verify `EMAIL_HOST` is `smtp.gmail.com`
- Verify `EMAIL_PORT` is `587`
- Verify `EMAIL_USE_TLS` is `True`
- Check your firewall/network isn't blocking port 587

### Issue 3: "Email field is empty" error when clicking "Email Report"
**Solution:**
- Update your profile with a valid email address
- Click on your profile/account settings
- Add your email address and save

### Issue 4: Email is printing to console instead of sending
**Solution:**
- Check that `EMAIL_BACKEND` is set to `django.core.mail.backends.smtp.EmailBackend` (not `console`)
- If it says "console backend," email won't actually send
- Update `.env` and restart the server

### Issue 5: "Failed to send email" but .env looks correct
**Solution:**
- Check Gmail account security: go to [myaccount.google.com/security](https://myaccount.google.com/security)
- Allow "Less secure app access" if your Gmail settings require it (though App Passwords are more secure)
- Regenerate a new App Password and update `.env`
- Restart the development server

---

## Configuration for Production (Render/Deployment)

### On Render.com
1. In your Render dashboard, go to **Environment** settings
2. Add these environment variables:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```
3. Deploy your application
4. Test by creating a prediction and emailing the report

### On Heroku, AWS, or Other Platforms
Follow the same steps - add the environment variables in your platform's configuration:
- **Heroku**: Under **Settings** > **Config Vars**
- **AWS**: Use AWS Secrets Manager or Environment Variables
- **Azure**: Use Key Vault or App Configuration

---

## Alternative Email Providers

### Using SendGrid
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=sg.your-sendgrid-api-key
DEFAULT_FROM_EMAIL=your-email@example.com
```

### Using AWS SES (Simple Email Service)
```env
EMAIL_BACKEND=django_ses.SESBackend
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SES_REGION_NAME=us-east-1
AWS_SES_REGION_ENDPOINT=email.us-east-1.amazonaws.com
DEFAULT_FROM_EMAIL=your-email@example.com
```

---

## Testing Email in Development

### Test 1: Basic SMTP Connection
```python
python manage.py shell
>>> from django.core.mail import get_connection
>>> conn = get_connection()
>>> conn.open()
True  # If True, SMTP connection works
>>> conn.close()
```

### Test 2: Send Test Email via Admin
1. Navigate to **Admin Panel** → **Email Test**
2. Enter a test recipient email
3. Submit to send a test email

### Test 3: Create Real Prediction and Email Report
1. Go to **Predict** page
2. Fill in values and get a prediction
3. Click **Email Report**
4. Check your email inbox (check spam folder too)

---

## Common Email Field Values for Testing

When testing the prediction system, use realistic values:
- **Age**: 25-75 years
- **Height**: 150-200 cm
- **Weight**: 50-120 kg
- **Glucose**: 50-300 mg/dL
- **Blood Pressure**: 40-200 mmHg
- **Pregnancies**: 0-20 (0 for males)

---

## Logs and Debugging

### Enable Django Email Logging (Local Development)
Add to your `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}
```

Then check your console for detailed email sending logs.

### Check Server Logs on Render
1. Go to your Render app dashboard
2. Click **Logs** tab
3. Search for "email" or "SMTP" errors
4. Check the full error trace

---

## Email Report Features

Once configured, users can:
1. Make a prediction
2. View personalized health advice
3. Download PDF report or Email it
4. Receive HTML formatted email with:
   - Prediction results and risk level
   - All personalized health recommendations
   - Attached PDF report with full details
   - Clinical values and thresholds

---

## Security Best Practices

✅ **DO:**
- Use App Passwords instead of main Gmail password
- Keep `.env` file out of version control
- Use environment variables for production
- Rotate passwords periodically
- Use HTTPS for all connections

❌ **DON'T:**
- Commit `.env` file to Git
- Share email credentials in chat or emails
- Use your main Gmail password
- Disable TLS/SSL encryption
- Store passwords in code

---

## Support

If you're still having issues:
1. Check that 2-Step Verification is enabled
2. Generate a new App Password
3. Verify ALL values in `.env` match exactly (including spaces)
4. Restart the Django development server
5. Check the console for detailed error messages
6. Verify your internet connection and firewall settings

---

**Last Updated: March 2, 2026**
**Configuration Version: 1.0**
