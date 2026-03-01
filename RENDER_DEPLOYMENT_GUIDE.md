# Render Deployment Guide — Diabetes Prediction Website

> Step-by-step guide to deploy this Django + ML application on **Render** with a managed **PostgreSQL** database, including how the local SQLite database transitions to PostgreSQL in production.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [How SQLite → PostgreSQL Works](#2-how-sqlite--postgresql-works)
3. [Prepare the Repository](#3-prepare-the-repository)
4. [Create a PostgreSQL Database on Render](#4-create-a-postgresql-database-on-render)
5. [Create a Web Service on Render](#5-create-a-web-service-on-render)
6. [Configure Environment Variables](#6-configure-environment-variables)
7. [Deploy via render.yaml (Blueprint)](#7-deploy-via-renderyaml-blueprint)
8. [Post-Deployment Steps](#8-post-deployment-steps)
9. [Seed Data on Render](#9-seed-data-on-render)
10. [Custom Domain & HTTPS](#10-custom-domain--https)
11. [Ongoing Maintenance](#11-ongoing-maintenance)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

| Item | Details |
|------|---------|
| **Git** | Code must be in a Git repository (GitHub, GitLab, or Bitbucket) |
| **Render Account** | Free tier available at [render.com](https://render.com) |
| **Python 3.11+** | Render uses the version specified in environment variables |
| **requirements.txt** | Must include `psycopg2-binary`, `gunicorn`, `whitenoise`, `django-environ` |
| **ML Model Artifacts** | `outputs/models/*.pkl` files must be committed to the repository |

### Required Files Already in This Project

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies (already includes `psycopg2-binary` for PostgreSQL) |
| `Procfile` | Tells Render to run `gunicorn diabetes_web.wsgi:application` |
| `build.sh` | Build script: installs deps, collects static files, runs migrations |
| `render.yaml` | Render Blueprint: auto-creates web service + PostgreSQL database |
| `diabetes_web/wsgi.py` | WSGI entry point for Gunicorn |

---

## 2. How SQLite → PostgreSQL Works

This is the most important concept to understand.

### Local Development (your machine)

```
DATABASE_URL not set → env.db() falls back to default
                     → sqlite:///C:/.../db.sqlite3
```

Your local `db.sqlite3` is a file-based database sitting in the project folder. It stores users, predictions, surveys — everything.

### Production on Render

```
DATABASE_URL = postgres://user:pass@host:5432/diabetes
             → env.db() parses this → django.db.backends.postgresql
```

Render creates a managed **PostgreSQL** server and injects the `DATABASE_URL` environment variable into your web service automatically.

### The Magic — `django-environ`

In `settings.py`, this single block handles both environments:

```python
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{(BASE_DIR / "db.sqlite3").as_posix()}'
    )
}

# Auto-add SSL for PostgreSQL (required by Render)
if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}
```

**How it works:**
1. `env.db('DATABASE_URL')` checks if the `DATABASE_URL` environment variable exists
2. **Locally**: It does NOT exist → falls back to `sqlite:///...db.sqlite3`
3. **On Render**: It DOES exist (injected by Render) → parses `postgres://...` URL → uses PostgreSQL engine (`psycopg2`)
4. The `sslmode: require` block ensures encrypted connections to Render's PostgreSQL

### What happens to data?

| Concern | Answer |
|---------|--------|
| **Does local SQLite data transfer to PostgreSQL?** | **No.** The Render PostgreSQL starts empty. You must run migrations and re-seed. |
| **Do Django models need changes?** | **No.** Django ORM abstracts the database. Same models work on both SQLite and PostgreSQL. |
| **Do migrations need to be re-run?** | **Yes.** `build.sh` runs `python manage.py migrate` on every deploy, which creates all tables in PostgreSQL. |
| **Can I export SQLite → PostgreSQL?** | Yes, using `python manage.py dumpdata > data.json` locally, then `python manage.py loaddata data.json` on Render. But re-seeding is simpler. |

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────┐
│               LOCAL DEVELOPMENT                       │
│                                                       │
│  Django App ──→ env.db() ──→ No DATABASE_URL          │
│                             ──→ SQLite (db.sqlite3)   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│               RENDER PRODUCTION                       │
│                                                       │
│  Django App ──→ env.db() ──→ DATABASE_URL exists      │
│                             ──→ PostgreSQL (Render)   │
│                                  ↓                    │
│                           Managed PostgreSQL           │
│                           ├── Auto-backup              │
│                           ├── SSL encrypted            │
│                           └── 1 GB free tier           │
└──────────────────────────────────────────────────────┘
```

---

## 3. Prepare the Repository

### 3.1 Push Code to GitHub

```bash
cd "C:\Users\Girijesh\Desktop\Diabetics Prediction Website"
git init
git add .
git commit -m "Initial commit - Diabetes Prediction Website"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/diabetes-prediction.git
git push -u origin main
```

### 3.2 Ensure These Files Are Committed

```
✅ requirements.txt        (includes psycopg2-binary, gunicorn)
✅ Procfile                 (web: gunicorn diabetes_web.wsgi:application)
✅ build.sh                 (pip install, collectstatic, migrate)
✅ render.yaml              (Render Blueprint)
✅ outputs/models/*.pkl     (ML model artifacts)
✅ locale/**/*.mo           (compiled translations)
✅ data/diabetes.csv        (training dataset)
```

### 3.3 Create/Verify `.gitignore`

Make sure these are NOT committed:

```gitignore
# .gitignore
*.pyc
__pycache__/
db.sqlite3
.env
.venv/
staticfiles/
media/
*.sqlite3
```

> **Important:** `outputs/models/*.pkl` MUST be committed (they are the trained ML model). Do NOT add them to `.gitignore`.

---

## 4. Create a PostgreSQL Database on Render

### Option A: Automatic (via render.yaml — Recommended)

The `render.yaml` file already defines the database:

```yaml
databases:
  - name: diabetes-db
    databaseName: diabetes
    plan: free        # 1 GB, 90-day retention (free tier)
```

When you deploy using the Blueprint, Render auto-creates this database and links the `DATABASE_URL`.

### Option B: Manual

1. Log into [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `diabetes-db`
   - **Database:** `diabetes`
   - **User:** (auto-generated)
   - **Region:** Oregon or Singapore (closest to your users)
   - **Plan:** Free (1 GB storage)
4. Click **"Create Database"**
5. Copy the **Internal Database URL** (starts with `postgres://...`)

---

## 5. Create a Web Service on Render

### Option A: Automatic (via render.yaml — Recommended)

Skip to [Section 7](#7-deploy-via-renderyaml-blueprint).

### Option B: Manual

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `diabetes-predict` |
| **Environment** | Python |
| **Region** | Same region as your database |
| **Branch** | `main` |
| **Build Command** | `chmod +x build.sh && ./build.sh` |
| **Start Command** | `gunicorn diabetes_web.wsgi:application` |
| **Plan** | Free |

4. Click **"Create Web Service"**

---

## 6. Configure Environment Variables

In the Render Web Service dashboard → **"Environment"** tab, add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | *(auto-linked if using render.yaml)* | `fromDatabase` directive auto-fills this |
| `SECRET_KEY` | *(auto-generated if using render.yaml)* | Or set manually: a long random string |
| `PYTHON_VERSION` | `3.11.0` | Python version for Render |
| `DEBUG` | `False` | **Never True in production** |
| `ALLOWED_HOSTS` | `.onrender.com` | Or your custom domain |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | For real email delivery |
| `EMAIL_HOST` | `smtp.gmail.com` | Gmail SMTP |
| `EMAIL_PORT` | `587` | TLS port |
| `EMAIL_USE_TLS` | `True` | Encrypt email |
| `EMAIL_HOST_USER` | `your_email@gmail.com` | Gmail address |
| `EMAIL_HOST_PASSWORD` | `xxxx xxxx xxxx xxxx` | Gmail App Password (not regular password) |
| `DEFAULT_FROM_EMAIL` | `your_email@gmail.com` | From address on emails |

### How to Get a Gmail App Password

1. Go to [myaccount.google.com → Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. Go to **App passwords** (search "App passwords" in Google Account settings)
4. Generate a new app password for "Mail" → "Other (Django)"
5. Copy the 16-character password (e.g., `yego tbou ykke bgqd`)
6. Use this as `EMAIL_HOST_PASSWORD`

---

## 7. Deploy via render.yaml (Blueprint)

This is the **easiest method**. The `render.yaml` in the project root defines everything:

### Step-by-Step

1. Push all code to GitHub (including `render.yaml`)

2. Go to [Render Dashboard](https://dashboard.render.com)

3. Click **"New +"** → **"Blueprint"**

4. Connect your GitHub repository

5. Render reads `render.yaml` and shows:
   - **Web Service:** `diabetes-predict`
   - **Database:** `diabetes-db`

6. Click **"Apply"**

7. Wait 3–5 minutes for the first build:
   - Render installs Python 3.11
   - Runs `build.sh` (installs deps, collectstatic, migrate)
   - Starts Gunicorn

8. Your site is live at: `https://diabetes-predict.onrender.com`

### What render.yaml Does

```yaml
services:
  - type: web
    name: diabetes-predict
    env: python
    buildCommand: chmod +x build.sh && ./build.sh   # Install + migrate
    startCommand: gunicorn diabetes_web.wsgi:application  # Production server
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: diabetes-db          # Auto-links PostgreSQL
          property: connectionString  # Injects the full postgres:// URL
      - key: SECRET_KEY
        generateValue: true           # Render generates a secure key
      # ... other env vars ...

databases:
  - name: diabetes-db
    databaseName: diabetes
    plan: free                        # 1 GB free tier
```

---

## 8. Post-Deployment Steps

### 8.1 Create Superuser (Admin Account)

After the first successful deploy, go to the Render Web Service → **"Shell"** tab, then run:

```bash
python manage.py createsuperuser
```

Enter:
- **Username:** `HariKrish` (or your preferred admin name)
- **Email:** `admin@diabetespredict.com`
- **Password:** `Hari123` (or a secure password)

> **Note:** The Shell tab is available on paid plans. For free plans, you can add a one-time management command to `build.sh`:

Add this line **temporarily** to `build.sh`, deploy once, then remove it:

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='HariKrish').exists():
    User.objects.create_superuser('HariKrish', 'admin@diabetespredict.com', 'Hari123')
    print('Superuser created')
else:
    print('Superuser already exists')
"
```

### 8.2 Seed Survey Data (375 Records)

Similarly, run (in Shell or via `build.sh`):

```bash
python manage.py seed_survey
```

This creates 375 survey records with unique users, realistic Indian names, IST timestamps, and correct gender-pregnancy mapping.

### 8.3 Verify Deployment

Open your browser:

| URL | Test |
|-----|------|
| `https://diabetes-predict.onrender.com/` | Home page loads |
| `https://diabetes-predict.onrender.com/predict/` | Prediction form works |
| `https://diabetes-predict.onrender.com/admin/` | Django admin login |
| `https://diabetes-predict.onrender.com/admin-dashboard/` | Custom admin dashboard |
| `https://diabetes-predict.onrender.com/health/` | Translation & email check |

---

## 9. Seed Data on Render

### Recommended: One-Time Build Script

Modify `build.sh` for the initial deploy to include seeding:

```bash
#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# One-time superuser creation (remove after first deploy)
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='HariKrish').exists():
    User.objects.create_superuser('HariKrish', 'admin@diabetespredict.com', 'Hari123')
    print('Created superuser: HariKrish')
if not User.objects.filter(username='Rishi').exists():
    User.objects.create_superuser('Rishi', 'rishi@diabetespredict.com', 'Rishi123')
    print('Created superuser: Rishi')
"

# One-time seed (remove after first deploy)
python manage.py seed_survey
```

After the first successful deploy, **remove the superuser and seed_survey lines** and re-deploy (otherwise it runs on every deploy).

### Alternative: Export from SQLite, Import into PostgreSQL

```bash
# On your LOCAL machine:
python manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 2 > data_dump.json

# Commit and push data_dump.json

# On Render Shell (or in build.sh):
python manage.py loaddata data_dump.json
```

> **Warning:** This transfers all users (including survey_user_0001–0375). Password hashes are preserved, so logins still work.

---

## 10. Custom Domain & HTTPS

1. In Render Dashboard → Web Service → **"Settings"** → **"Custom Domains"**
2. Add your domain (e.g., `diabetespredict.com`)
3. Update DNS records as shown by Render (CNAME or A record)
4. Render automatically provisions an SSL certificate (Let's Encrypt)
5. Update `ALLOWED_HOSTS` env var: `.onrender.com,diabetespredict.com`

---

## 11. Ongoing Maintenance

### Deploying Updates

```bash
git add .
git commit -m "Feature: added new feature"
git push origin main
# Render auto-deploys on push (if auto-deploy is enabled)
```

### Monitoring

| Feature | Location |
|---------|----------|
| **Logs** | Render Dashboard → Web Service → "Logs" tab |
| **Metrics** | CPU, memory, response time visible in dashboard |
| **Database** | Render Dashboard → Database → "Info" tab (size, connections) |

### Database Backups

- **Free tier:** Render takes daily snapshots (retained for 1 day)
- **Paid tier:** 7–30 day retention with point-in-time recovery
- **Manual backup:**
  ```bash
  # In Render Shell:
  python manage.py dumpdata --indent 2 > backup.json
  ```

### Free Tier Limitations

| Resource | Limit |
|----------|-------|
| **Web Service** | Spins down after 15 min of inactivity; 750 free hours/month |
| **PostgreSQL** | 1 GB storage; auto-deleted after 90 days of inactivity |
| **Bandwidth** | 100 GB/month |

> **Cold Start:** On the free tier, the first request after idle takes ~30 seconds as the service spins up. Subsequent requests are fast.

---

## 12. Troubleshooting

### Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: psycopg2` | Missing PostgreSQL driver | Ensure `psycopg2-binary` is in `requirements.txt` |
| `OperationalError: SSL required` | Connecting to Render PostgreSQL without SSL | The `sslmode: require` block in `settings.py` handles this |
| `DisallowedHost` | Domain not in `ALLOWED_HOSTS` | Add `.onrender.com` to the env var |
| `Static files 404` | WhiteNoise not serving files | Ensure `whitenoise` is in `MIDDLEWARE` and `collectstatic` runs in `build.sh` |
| `Model not found` | `outputs/models/*.pkl` not committed | Commit and push the `.pkl` files |
| `Application error (502)` | Build or startup crash | Check "Logs" tab on Render for the full traceback |
| `Email not sending` | SMTP not configured | Verify `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` env vars |

### Checking Logs

```
Render Dashboard → Web Service → "Logs" tab
```

Look for:
- `Applying prediction.0001_initial... OK` → Migrations ran successfully
- `Booting worker with pid: ...` → Gunicorn started
- Tracebacks → Application errors

### Connecting to Production Database Locally

If you need to inspect the production PostgreSQL from your local machine:

1. Copy the **External Database URL** from Render Dashboard → Database → "Info"
2. Set it locally:
   ```bash
   set DATABASE_URL=postgres://user:password@host:5432/diabetes
   python manage.py dbshell
   ```

---

## Quick Reference

```
Local:  python manage.py runserver           → SQLite (db.sqlite3)
Render: gunicorn diabetes_web.wsgi:application → PostgreSQL (Render managed)

The switch is 100% automatic via DATABASE_URL.
No code changes needed between local and production.
```

---

*Last updated: March 2026*
