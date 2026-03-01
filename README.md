# Diabetes Prediction Web Application

A full-featured web application for diabetes risk assessment using a stacking ensemble ML model (91%+ accuracy).

## Features

- **User Authentication** - Register, Login, Password Reset
- **Prediction Interface** - Form with all clinical parameters (Pregnancies, Glucose, Blood Pressure, BMI, Age, etc.)
- **History Tracking** - Save predictions with timestamps (requires login)
- **Dashboard** - Visualize prediction history with charts
- **PDF Reports** - Download detailed prediction reports
- **Speech Input** - Voice-to-text for form filling (Chrome/Edge)
- **Personalized Advice** - Health tips based on risk level (Low/Medium/High)
- **Multi-language UI** - English, Tamil, Hindi
- **Email Notifications** - Password reset via email (configure SMTP)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Model Files (First Time Only)

Run the Jupyter notebook to train and save the model:

```bash
python run_notebook.py
```

Or open `Diabetics_Prediction.ipynb` in Jupyter and run all cells.

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Start the Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**

## Tech Stack

- **Backend:** Django 4.2
- **Database:** SQLite (dev) / PostgreSQL (production)
- **ML:** scikit-learn, XGBoost, LightGBM
- **UI:** Bootstrap 5
- **PDF:** ReportLab
