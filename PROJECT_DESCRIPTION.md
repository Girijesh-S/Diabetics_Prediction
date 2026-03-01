# An Intelligent Web-Based Diabetes Prediction System Using Stacking Ensemble Learning with Automated Feature Engineering

## A Conference-Ready Project Description

---

## 1. Abstract

This project presents an end-to-end intelligent web application for early diabetes risk prediction, built using a **Stacking Ensemble Learning** approach with automated feature engineering. The system leverages the Pima Indians Diabetes Dataset (768 samples, 8 clinical features) and constructs **80 engineered features** from the original 8, achieving a classification accuracy of **89%**, a ROC-AUC of **93.86%**, and a 10-Fold Cross-Validation score of **84.50% ± 3.69%**. The application is developed using the Django web framework (Python), supports **multilingual interfaces** (English, Tamil, Hindi), generates **colour-coded PDF health reports** with personalised dietary recommendations, and is deployable on cloud platforms (Render) with PostgreSQL integration. A built-in survey module and admin analytics dashboard support post-prediction feedback collection and population-level health monitoring.

---

## 2. Keywords

Diabetes Prediction, Stacking Ensemble, Feature Engineering, Machine Learning, Django, Web Application, Pima Indians Dataset, XGBoost, LightGBM, Random Forest, SMOTE, Multilingual Healthcare, PDF Report Generation, Cloud Deployment

---

## 3. Introduction & Motivation

Diabetes mellitus is a chronic metabolic disorder affecting over 537 million adults worldwide (IDF, 2021). Early detection and lifestyle intervention can significantly delay or prevent the onset of Type 2 diabetes. However, access to predictive healthcare tools remains limited, especially in multilingual populations.

This project addresses this gap by providing:

1. **An accessible web-based prediction tool** requiring only 6 user inputs (instead of the full 8 clinical parameters).
2. **Automated imputation** of hard-to-measure values (Insulin, Diabetes Pedigree Function, Skin Thickness) using trained regression estimators.
3. **Extensive feature engineering** (80 features from 8 base features) for improved classification.
4. **Multilingual support** (English, Tamil, Hindi) to serve diverse populations.
5. **Actionable health reports** with colour-coded clinical indicators and region-specific dietary plans.

---

## 4. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│    HTML/CSS/Bootstrap 5 │ Crispy Forms │ Multilingual (i18n)    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP
┌──────────────────────────────▼──────────────────────────────────┐
│                     DJANGO WEB SERVER                           │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Views   │  │   Forms   │  │  Models  │  │  ML Service   │  │
│  │(1380 LOC)│  │ (103 LOC) │  │ (57 LOC) │  │  (252 LOC)    │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────┬───────┘  │
│                                                      │          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────▼───────┐  │
│  │  PDF Engine  │  │ Email (SMTP) │  │  Trained ML Models    │  │
│  │ (ReportLab)  │  │  (Gmail)     │  │  (Stacking Ensemble)  │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│              DATABASE LAYER                                      │
│   Local: SQLite3  │  Production: PostgreSQL (Render)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Complete Directory Structure & Module Descriptions

Below is the complete project directory tree with detailed descriptions of every file and folder.

```
Diabetics Prediction Website/
│
├── manage.py
├── diabetes_model.py
├── run_notebook.py
├── compile_translations.py
├── run_server.bat
├── build.sh
├── Procfile
├── render.yaml
├── requirements.txt
├── db.sqlite3
├── README.md
├── training_output.txt
├── Diabetics_Prediction.ipynb
├── RENDER_DEPLOYMENT_GUIDE.md
├── PROJECT_DESCRIPTION.md          ← This file
│
├── data/
│   └── diabetes.csv
│
├── outputs/
│   └── models/
│       ├── best_model.pkl
│       ├── scaler.pkl
│       ├── meta.pkl
│       ├── estimators.pkl
│       └── pop_defaults.pkl
│
├── diabetes_web/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── __pycache__/
│
├── prediction/
│   ├── __init__.py
│   ├── admin.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── ml_service.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   └── __pycache__/
│
├── templates/
│   ├── base.html
│   └── prediction/
│       ├── home.html
│       ├── predict.html
│       ├── predict_result.html
│       ├── dashboard.html
│       ├── health.html
│       ├── history.html
│       ├── login.html
│       ├── register.html
│       ├── train_info.html
│       ├── password_reset.html
│       ├── password_reset_done.html
│       ├── password_reset_confirm.html
│       └── emails/
│           └── password_reset_email.html
│
├── locale/
│   ├── hi/
│   │   └── LC_MESSAGES/
│   │       ├── django.po
│   │       └── django.mo
│   └── ta/
│       └── LC_MESSAGES/
│           ├── django.po
│           └── django.mo
│
└── __pycache__/
```

---

### 5.1 Root-Level Files

| File | Lines | Purpose |
|------|-------|---------|
| **`manage.py`** | ~22 | Django's command-line utility for administrative tasks (runserver, migrate, makemigrations, createsuperuser, etc.). Entry point for all Django management commands. |
| **`diabetes_model.py`** | 925 | **Core training pipeline.** Implements the complete machine learning workflow: data loading, preprocessing (zero-imputation correction), SMOTE oversampling, 80-feature engineering, regression estimator training (Insulin, DPF, SkinThickness), stacking ensemble construction (Random Forest + XGBoost + LightGBM base learners → Logistic Regression meta-learner), Optuna-style threshold optimisation, model persistence, and evaluation. |
| **`run_notebook.py`** | ~15 | Utility script to programmatically execute the Jupyter notebook (`Diabetics_Prediction.ipynb`) using `nbconvert` and capture outputs. |
| **`compile_translations.py`** | ~12 | Script to compile `.po` translation files into binary `.mo` files for all supported locales (Hindi, Tamil). |
| **`run_server.bat`** | ~3 | Windows batch file to start the Django development server (`python manage.py runserver`). |
| **`build.sh`** | 5 | **Render build script.** Executed during deployment: installs pip dependencies, collects static files, and runs database migrations. |
| **`Procfile`** | 1 | **Render process declaration.** Specifies the production server command: `web: gunicorn diabetes_web.wsgi:application`. |
| **`render.yaml`** | 41 | **Render Blueprint (Infrastructure-as-Code).** Declares the web service configuration, PostgreSQL database provisioning, environment variables (SECRET_KEY, DATABASE_URL, SMTP credentials), build/start commands, and health check settings. |
| **`requirements.txt`** | 16 | Python dependency manifest listing all required packages (Django, scikit-learn, xgboost, lightgbm, reportlab, gunicorn, etc.). |
| **`db.sqlite3`** | Binary | **Local development database.** Stores user accounts, predictions, and survey responses during local development. Automatically replaced by PostgreSQL in production. |
| **`training_output.txt`** | ~50 | Captured console output from the training pipeline showing all model evaluation metrics, cross-validation scores, and threshold optimisation results. |
| **`Diabetics_Prediction.ipynb`** | ~cells | Jupyter Notebook containing an interactive version of the training and evaluation pipeline with visualisations (confusion matrix, ROC curve, feature importance). |
| **`README.md`** | ~30 | Project overview and basic setup instructions. |

---

### 5.2 `data/` — Dataset Directory

| File | Description |
|------|-------------|
| **`diabetes.csv`** | The **Pima Indians Diabetes Dataset** (National Institute of Diabetes and Digestive and Kidney Diseases). Contains **768 records** with **8 clinical features** and 1 binary outcome variable. |

**Dataset Schema:**

| # | Feature | Type | Description | Range |
|---|---------|------|-------------|-------|
| 1 | Pregnancies | int | Number of times pregnant | 0–17 |
| 2 | Glucose | int | Plasma glucose concentration (2-hour OGTT, mg/dL) | 0–199 |
| 3 | BloodPressure | int | Diastolic blood pressure (mm Hg) | 0–122 |
| 4 | SkinThickness | int | Triceps skin fold thickness (mm) | 0–99 |
| 5 | Insulin | int | 2-Hour serum insulin (μU/mL) | 0–846 |
| 6 | BMI | float | Body mass index (kg/m²) | 0–67.1 |
| 7 | DiabetesPedigreeFunction | float | Diabetes pedigree function (genetic score) | 0.078–2.42 |
| 8 | Age | int | Age in years | 21–81 |
| 9 | Outcome | int | Class label (0 = Non-diabetic, 1 = Diabetic) | 0 or 1 |

**Class Distribution:** 500 Non-diabetic (65.1%) / 268 Diabetic (34.9%) — addressed via SMOTE oversampling.

---

### 5.3 `outputs/models/` — Trained Model Artifacts

These serialised pickle files are produced by `diabetes_model.py` and consumed by `prediction/ml_service.py` at prediction time.

| File | Description |
|------|-------------|
| **`best_model.pkl`** | The trained **Stacking Classifier** (StackingClassifier from scikit-learn). Contains the full ensemble: 3 base learners (Random Forest, XGBoost, LightGBM) and the Logistic Regression meta-learner, along with the optimised probability threshold (0.5494). |
| **`scaler.pkl`** | Fitted **StandardScaler** used to normalise 80 engineered features to zero mean and unit variance before ensemble inference. |
| **`meta.pkl`** | Metadata dictionary storing feature names (ordered list of 80 feature columns), optimal threshold value, and training configuration. |
| **`estimators.pkl`** | Dictionary of **3 trained regression models** used to impute missing clinical values at prediction time — Insulin Estimator (R² = 0.93), DPF Estimator (R² = 0.87), SkinThickness Estimator (R² = 0.90). |
| **`pop_defaults.pkl`** | **Population-level default values** (median/mean) for each of the 8 original features; used as fallback imputation values when regression estimation is not applicable. |

---

### 5.4 `diabetes_web/` — Django Project Configuration

This is the Django project package (created by `django-admin startproject`).

| File | Lines | Description |
|------|-------|-------------|
| **`settings.py`** | 115 | **Central configuration.** Defines installed apps (`prediction`, `crispy_forms`, `crispy_bootstrap5`), middleware stack (including `WhiteNoiseMiddleware` for static files and `LocaleMiddleware` for i18n), database configuration (`env.db()` for automatic SQLite↔PostgreSQL switching via `DATABASE_URL` environment variable), internationalisation settings (LANGUAGE_CODE, LANGUAGES, LOCALE_PATHS), email backend configuration (SMTP via Gmail), static/media file paths, and authentication redirects. |
| **`urls.py`** | ~20 | **Root URL configuration.** Maps the `/admin/` path to Django's built-in admin, includes `prediction/urls.py` for all application routes, sets the `i18n/` path for language switching, and includes `django.contrib.auth.urls` for authentication. |
| **`wsgi.py`** | ~16 | **WSGI entry point.** Exposes the `application` callable used by Gunicorn in production to serve the Django application. |

---

### 5.5 `prediction/` — Core Application Package

This is the primary Django app containing all business logic.

#### 5.5.1 `prediction/__init__.py`
Empty file marking `prediction/` as a Python package.

#### 5.5.2 `prediction/models.py` (57 lines) — Database Models

Defines two Django ORM models:

**`Prediction` Model:**
| Field | Type | Description |
|-------|------|-------------|
| `user` | ForeignKey(User) | Authenticated user who made the prediction (CASCADE delete) |
| `pregnancies` | IntegerField | Number of pregnancies (input) |
| `glucose` | FloatField | Plasma glucose level (input) |
| `blood_pressure` | FloatField | Diastolic blood pressure (input) |
| `skin_thickness` | FloatField | Estimated skin thickness (computed) |
| `insulin` | FloatField | Estimated insulin level (computed) |
| `bmi` | FloatField | Calculated BMI (from weight/height) |
| `dpf` | FloatField | Estimated Diabetes Pedigree Function (computed) |
| `age` | IntegerField | Age in years (input) |
| `result` | CharField | Prediction outcome ("Positive" / "Negative") |
| `probability` | FloatField | Prediction confidence probability (0.0–1.0) |
| `predicted_at` | DateTimeField | Timestamp of prediction (auto_now_add) |

**`SurveyResponse` Model:**
| Field | Type | Description |
|-------|------|-------------|
| `user` | ForeignKey(User) | Survey respondent |
| `age_group` | CharField | Age bracket of respondent |
| `gender` | CharField | Gender identity |
| `family_history` | CharField | Family diabetes history (Yes/No) |
| `exercise_frequency` | CharField | Weekly exercise frequency |
| `diet_type` | CharField | Dietary classification |
| `smoking` | CharField | Smoking status |
| `alcohol` | CharField | Alcohol consumption level |
| `stress_level` | CharField | Perceived stress level |
| `submitted_at` | DateTimeField | Submission timestamp |

Both models cascade on user deletion, enabling GDPR-compliant user data removal.

#### 5.5.3 `prediction/forms.py` (103 lines) — Form Definitions

| Form | Fields | Description |
|------|--------|-------------|
| **`RegisterForm`** | username, email, password1, password2 | User registration form extending `UserCreationForm` with Bootstrap styling via `crispy_forms`. |
| **`PredictionForm`** | pregnancies, glucose, blood_pressure, weight_kg, height_cm, age | **6-field simplified input form.** Users provide only these values; BMI is auto-calculated from weight/height, and Insulin, DPF, and SkinThickness are auto-estimated by regression models. |
| **`SurveyForm`** | 8 fields (age_group through stress_level) | Post-prediction lifestyle survey with dropdown choices for epidemiological data collection. |

**Design Decision:** The prediction form collects only **6 inputs** instead of the dataset's 8 features. This is a deliberate UX choice — Insulin levels, Diabetes Pedigree Function, and Skin Thickness are difficult for patients to obtain without clinical testing. These values are estimated using trained regression models (see §5.3).

#### 5.5.4 `prediction/ml_service.py` (252 lines) — Machine Learning Service

This module bridges the trained ML models and the web application. It exposes a single public function:

```python
def predict_diabetes(pregnancies, glucose, blood_pressure, weight_kg, height_cm, age)
    → dict  # {result, probability, bmi, insulin, dpf, skin_thickness}
```

**Internal Pipeline:**

1. **BMI Calculation:** BMI = weight_kg / (height_cm / 100)²
2. **Male Pregnancy Override:** If pregnancies = 0 and context suggests male user, pregnancies forced to 0.
3. **Regression Estimation:** Uses `estimators.pkl` to predict:
   - Insulin from [Glucose, BMI, Age, BloodPressure] → R² = 0.93
   - DiabetesPedigreeFunction from [Age, BMI, Glucose] → R² = 0.87
   - SkinThickness from [BMI, Age] → R² = 0.90
4. **Feature Engineering:** `engineer_features()` generates **80 features** including:
   - Polynomial interactions (pairwise products)
   - Ratio features (Glucose/Insulin, BMI/Age, etc.)
   - Logarithmic transforms (log1p of all base features)
   - Binned categorical encodings (Age bins, BMI bins, Glucose bins)
   - Domain-specific composites (Glucose × BMI, Insulin Resistance proxy)
5. **Scaling:** StandardScaler normalisation of all 80 features.
6. **Prediction:** Stacking ensemble outputs probability; compared against optimised threshold (0.5494).
7. **Result:** Returns structured dictionary with prediction, probability, and all estimated values.

#### 5.5.5 `prediction/views.py` (1380 lines) — View Functions

The largest module, containing all HTTP request handlers:

| View Function | Method | URL | Description |
|---------------|--------|-----|-------------|
| `home_view` | GET | `/` | Landing page with project overview and navigation. |
| `register_view` | GET/POST | `/register/` | User registration with form validation. |
| `login_view` | GET/POST | `/login/` | User authentication. |
| `logout_view` | POST | `/logout/` | Session termination. |
| `predict_view` | GET/POST | `/predict/` | **Core prediction page.** Accepts 6 inputs, calls `predict_diabetes()`, stores result, renders prediction result with clinical indicators. |
| `predict_result_view` | GET | `/predict/result/<id>/` | Displays a specific historical prediction result. |
| `history_view` | GET | `/history/` | User's prediction history with pagination. |
| `health_view` | GET | `/health/` | Static health education content. |
| `survey_view` | GET/POST | `/survey/` | Post-prediction lifestyle survey. |
| `dashboard_view` | GET | `/dashboard/` | User's personal health dashboard with charts. |
| `train_info_view` | GET | `/train-info/` | Displays model training metrics and methodology. |
| `download_report` | GET | `/predict/result/<id>/download/` | Generates and streams a **PDF health report** with colour-coded clinical values. |
| `email_report` | POST | `/predict/result/<id>/email/` | Sends the PDF report via email with matching textual advice. |
| `admin_dashboard_view` | GET | `/admin-dashboard/` | **Admin analytics dashboard** showing total predictions, surveys, registered users, and survey trends with charts. |
| `admin_users_view` | GET | `/admin-dashboard/users/` | List of all registered users with prediction/survey counts. |
| `admin_user_history_view` | GET | `/admin-dashboard/users/<username>/` | Detailed prediction history for a specific user. |
| `admin_delete_user` | POST | `/admin-dashboard/users/<username>/delete/` | Admin-only user deletion with cascade (removes all predictions and surveys). |

**Key Sub-Functions within views.py:**

| Function | Description |
|----------|-------------|
| `build_pdf_bytes(pred, user, include_dashboard, advice)` | Generates a multi-page PDF report using ReportLab. Includes a **3-zone colour-coded clinical table** (Normal=green, Moderate=amber, High/Risk=red) for Glucose, Blood Pressure, BMI, Insulin, and DPF. Also includes personalised dietary recommendations and an Indian diet plan. |
| `get_personalized_advice(pred)` | Generates a list of 6–10 personalised health recommendations based on the user's prediction values and clinical thresholds. |
| `_get_indian_diet_plan()` | Returns a structured Indian-diet meal plan (breakfast, lunch, dinner, snacks) tailored for diabetic/pre-diabetic individuals. |

#### 5.5.6 `prediction/admin.py` (26 lines) — Django Admin Configuration

Registers `Prediction` and `SurveyResponse` models with the Django admin interface with custom list displays, filters, and search fields for administrative data management.

#### 5.5.7 `prediction/context_processors.py` — Template Context

Injects global context variables (e.g., `LANGUAGES`, current language) into all templates for multilingual UI rendering.

#### 5.5.8 `prediction/urls.py` — URL Routing

Maps all URL patterns to their corresponding view functions. Uses Django's `path()` with named URLs for reverse resolution in templates.

#### 5.5.9 `prediction/migrations/` — Database Migrations

| File | Description |
|------|-------------|
| `0001_initial.py` | Creates the `Prediction` and `SurveyResponse` tables with all fields, foreign keys, and indexes. |

---

### 5.6 `templates/` — HTML Templates

All templates extend `base.html` and use Django's template language with Bootstrap 5 for responsive design.

| Template | Lines | Description |
|----------|-------|-------------|
| **`base.html`** | 146 | **Master template.** Defines the HTML skeleton, navigation bar (with language switcher dropdown for EN/TA/HI), Bootstrap 5 CDN imports, message alerts, and footer. All other templates extend this via `{% extends "base.html" %}`. |
| **`home.html`** | 95 | Landing page with hero section, feature highlights, and call-to-action buttons. |
| **`predict.html`** | 104 | Prediction input form rendered with `crispy_forms` providing 6 input fields with Bootstrap styling and validation. |
| **`predict_result.html`** | 73 | Prediction result display with risk level (Positive/Negative), probability percentage, estimated clinical values, PDF download button, and email report button. |
| **`dashboard.html`** | — | User's personal health dashboard with prediction trend charts. |
| **`health.html`** | — | Static health education content about diabetes prevention and management. |
| **`history.html`** | — | Paginated table of user's past predictions with links to detailed results. |
| **`login.html`** | — | Login form with "Forgot Password?" link. |
| **`register.html`** | — | Registration form with username, email, password fields. |
| **`train_info.html`** | — | Displays model training methodology, accuracy metrics, and feature importance visualisation. |
| **`password_reset.html`** | — | Email input for password reset request. |
| **`password_reset_done.html`** | — | Confirmation message after reset email is sent. |
| **`password_reset_confirm.html`** | — | New password entry form (accessed via email link). |
| **`emails/password_reset_email.html`** | — | HTML email template for password reset links. |

**Admin Templates (in `prediction/`):**

| Template | Lines | Description |
|----------|-------|-------------|
| **`admin_dashboard.html`** | 190 | Admin analytics page with 4 stat cards (Total Predictions, Total Surveys, Average Risk Score, Registered Users), survey breakdown charts (gender, age group, exercise, diet), and recent activity tables. |
| **`admin_users.html`** | — | User management table with prediction/survey counts per user and delete functionality (Bootstrap modal confirmation). |
| **`admin_user_history.html`** | — | Individual user's prediction history for admin review. |

---

### 5.7 `locale/` — Internationalisation (i18n)

The application supports **3 languages**:

| Code | Language | Status |
|------|----------|--------|
| `en` | English | Default (strings in source code) |
| `hi` | Hindi (हिन्दी) | Translated via `.po` files |
| `ta` | Tamil (தமிழ்) | Translated via `.po` files |

**File Structure per Locale:**
- `django.po` — Human-readable translation file (GNU gettext PO format) containing `msgid` (English) → `msgstr` (translated) pairs.
- `django.mo` — Compiled binary translation file used by Django at runtime for fast string lookup.

Translation coverage includes: navigation labels, form fields, prediction results, risk levels, health advice, error messages, admin dashboard labels, and dietary recommendations.

---

## 6. Machine Learning Methodology

### 6.1 Training Pipeline (`diabetes_model.py` — 925 lines)

```
Raw Data (768 × 9)
       │
       ▼
Zero-Value Imputation (Glucose, BP, SkinThickness, Insulin, BMI)
       │
       ▼
Regression Estimator Training
  ├── Insulin Estimator      → R² = 0.93
  ├── DPF Estimator          → R² = 0.87
  └── SkinThickness Estimator → R² = 0.90
       │
       ▼
Feature Engineering (8 → 80 features)
  ├── Polynomial Interactions
  ├── Ratio Features
  ├── Log Transforms
  ├── Binned Categories
  └── Domain Composites
       │
       ▼
SMOTE Oversampling (balance 65:35 → 50:50)
       │
       ▼
StandardScaler Normalisation
       │
       ▼
Stacking Ensemble Construction
  ├── Base Learner 1: Random Forest (n_estimators=200)
  ├── Base Learner 2: XGBoost (learning_rate=0.1)
  ├── Base Learner 3: LightGBM (num_leaves=31)
  └── Meta Learner: Logistic Regression (C=1.0)
       │
       ▼
Threshold Optimisation (Youden's J → optimal = 0.5494)
       │
       ▼
Model Serialisation (5 .pkl files → outputs/models/)
```

### 6.2 Feature Engineering Details

From the original **8 clinical features**, the system generates **80 engineered features**:

| Category | Count | Examples |
|----------|-------|---------|
| Original Features | 8 | Glucose, BMI, Age, etc. |
| Polynomial Interactions | ~28 | Glucose×BMI, Age×BP, Insulin×Glucose |
| Ratio Features | ~12 | Glucose/Insulin, BMI/Age, BP/Age |
| Logarithmic Transforms | 8 | log1p(Glucose), log1p(Insulin), etc. |
| Binned Encodings | ~12 | AgeBin (young/middle/senior), BMIBin, GlucoseBin |
| Domain Composites | ~12 | HOMA-IR proxy, Glucose-BMI index, Insulin resistance score |
| **Total** | **80** | — |

### 6.3 Stacking Ensemble Architecture

```
Input (80 features)
       │
       ├──→ Random Forest ──→ P(diabetes | RF)   ──┐
       ├──→ XGBoost       ──→ P(diabetes | XGB)  ──┼──→ Logistic Regression ──→ Final P(diabetes)
       └──→ LightGBM      ──→ P(diabetes | LGBM) ──┘          (Meta-Learner)
```

The stacking approach combines the strengths of:
- **Random Forest:** Robust to noise, handles feature interactions natively.
- **XGBoost:** Excellent gradient-boosted performance with regularisation.
- **LightGBM:** Fast training with histogram-based splits, handles categorical features.
- **Logistic Regression (Meta):** Learns optimal weighting of base learner predictions.

### 6.4 Evaluation Metrics

| Metric | Value |
|--------|-------|
| **Accuracy** | 89.00% |
| **Precision** | 89.00% |
| **Recall (Sensitivity)** | 89.00% |
| **ROC-AUC** | 93.86% |
| **10-Fold Cross-Validation** | 84.50% ± 3.69% |
| **Optimised Threshold** | 0.5494 (Youden's J statistic) |

The threshold of **0.5494** (instead of the default 0.50) was determined by maximising Youden's J statistic (Sensitivity + Specificity − 1) on the validation set, providing a balanced trade-off between false positives and false negatives in a clinical context.

---

## 7. Key Technical Features

### 7.1 Automated Clinical Value Estimation

Users input only **6 values** (Pregnancies, Glucose, Blood Pressure, Weight, Height, Age). The system automatically estimates:

| Estimated Parameter | Input Features Used | Model | R² Score |
|---------------------|---------------------|-------|----------|
| Insulin (μU/mL) | Glucose, BMI, Age, BP | Regression | 0.93 |
| Diabetes Pedigree Function | Age, BMI, Glucose | Regression | 0.87 |
| Skin Thickness (mm) | BMI, Age | Regression | 0.90 |

This significantly lowers the barrier to use — patients do not need expensive lab tests to receive a preliminary risk assessment.

### 7.2 Colour-Coded PDF Health Reports

The `build_pdf_bytes()` function generates multi-page PDF reports using ReportLab with:

- **3-zone clinical colour coding:**
  - 🟢 **Green (Normal):** Value within healthy range
  - 🟡 **Amber (Moderate/Borderline):** Value requires attention
  - 🔴 **Red (High Risk):** Value indicates clinical concern

| Clinical Parameter | Normal | Moderate | High |
|-------------------|--------|----------|------|
| Glucose (mg/dL) | < 100 | 100–125 | ≥ 126 |
| Blood Pressure (mm Hg) | < 80 | 80–89 | ≥ 90 |
| BMI (kg/m²) | 18.5–24.9 | 25.0–29.9 | ≥ 30.0 |
| Insulin (μU/mL) | < 166 | — | ≥ 166 |
| DPF | < 0.5 | 0.5–1.0 | > 1.0 |

- **Personalised dietary recommendations** (Indian diet plan)
- **8–10 tailored health advice items** based on individual results
- **Unified advice** — PDF and email reports contain identical recommendations

### 7.3 Multilingual Interface

The application uses Django's `i18n` (internationalisation) framework:

- All user-facing strings wrapped in `{% trans %}` template tags or `gettext()` function calls.
- Language switcher dropdown in the navigation bar (base.html).
- URLs prefixed with language code via `i18n_patterns`.
- Compiled binary `.mo` files for production-speed translations.

### 7.4 Admin Analytics Dashboard

Superuser-accessible dashboard providing:

- **4 Stat Cards:** Total Predictions, Total Surveys, Average Risk Score, Registered Users
- **Survey Analytics Charts:** Gender distribution, age group breakdown, exercise frequency, dietary patterns
- **User Management:** List all users, view individual histories, delete accounts (with cascade)
- **Recent Activity:** Latest predictions and survey submissions

### 7.5 Email Integration

- SMTP-based email delivery via Gmail
- Sends PDF health reports as attachments
- Password reset functionality with HTML email templates
- Advice text in email body matches PDF content exactly

---

## 8. Technology Stack

| Layer | Technology | Version/Details |
|-------|-----------|-----------------|
| **Language** | Python | 3.11 |
| **Web Framework** | Django | 4.2.28 |
| **ML Libraries** | scikit-learn, XGBoost, LightGBM | Latest stable |
| **Data Processing** | pandas, NumPy | Latest stable |
| **Oversampling** | imbalanced-learn (SMOTE) | Latest stable |
| **PDF Generation** | ReportLab | Latest stable |
| **CSS Framework** | Bootstrap 5 | 5.x (CDN) |
| **Form Rendering** | django-crispy-forms + crispy-bootstrap5 | Latest stable |
| **Static Files** | WhiteNoise | Production-grade static serving |
| **WSGI Server** | Gunicorn | Production HTTP server |
| **Database (Dev)** | SQLite 3 | File-based, zero-config |
| **Database (Prod)** | PostgreSQL | Render managed, SSL required |
| **Environment Config** | django-environ | DATABASE_URL-based switching |
| **Database Adapter** | psycopg2-binary | PostgreSQL driver |
| **Cloud Platform** | Render | Web service + managed PostgreSQL |
| **i18n** | Django i18n + GNU gettext | .po/.mo translation files |
| **Email** | Django SMTP backend | Gmail SMTP (TLS, port 587) |

---

## 9. Deployment Architecture

```
┌─────────────────────────────────────────┐
│              RENDER CLOUD               │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │    Web Service                  │    │
│  │    (diabetes-predict)           │    │
│  │                                 │    │
│  │  Gunicorn → Django WSGI         │    │
│  │  WhiteNoise (Static Files)      │    │
│  │  ML Models (outputs/models/)    │    │
│  │                                 │    │
│  │  ENV: DATABASE_URL, SECRET_KEY  │    │
│  │       SMTP credentials          │    │
│  └───────────────┬─────────────────┘    │
│                  │ Internal Network     │
│  ┌───────────────▼─────────────────┐    │
│  │    PostgreSQL Database          │    │
│  │    (diabetes-db)                │    │
│  │                                 │    │
│  │  Tables: auth_user,             │    │
│  │    prediction_prediction,       │    │
│  │    prediction_surveyresponse    │    │
│  │                                 │    │
│  │  SSL: Required                  │    │
│  │  Plan: Free tier available      │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

The `DATABASE_URL` environment variable is auto-injected by Render from the provisioned PostgreSQL instance. Django's `env.db()` call in `settings.py` parses this URL and configures the appropriate database backend, with `sslmode=require` for encrypted connections.

---

## 10. Software Metrics Summary

| Metric | Value |
|--------|-------|
| **Total Python Source Lines** | ~2,770 |
| **Total HTML Template Lines** | ~1,000+ |
| **Core Modules** | 8 Python files |
| **Templates** | 16 HTML files |
| **Database Models** | 2 (Prediction, SurveyResponse) |
| **API Endpoints / Views** | 16 URL-mapped views |
| **Supported Languages** | 3 (English, Tamil, Hindi) |
| **ML Features (Engineered)** | 80 |
| **ML Base Learners** | 3 (RF, XGB, LGBM) |
| **Trained Model Artifacts** | 5 (.pkl files) |
| **Classification Accuracy** | 89% |
| **ROC-AUC Score** | 93.86% |

---

## 11. Running the Application

### 11.1 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (for admin dashboard)
python manage.py createsuperuser

# Train ML models (if not already trained)
python diabetes_model.py

# Compile translations
python compile_translations.py

# Start development server
python manage.py runserver
```

### 11.2 Production Deployment (Render)

Refer to **RENDER_DEPLOYMENT_GUIDE.md** for comprehensive deployment instructions including:
- Render Blueprint setup via `render.yaml`
- PostgreSQL provisioning and DATABASE_URL configuration
- Environment variable configuration
- Build and start command configuration
- SSL and security settings

---

## 12. Security Considerations

| Feature | Implementation |
|---------|---------------|
| **Authentication** | Django's built-in auth system with hashed passwords (PBKDF2) |
| **CSRF Protection** | Django middleware, all forms include `{% csrf_token %}` |
| **SQL Injection Prevention** | Django ORM parameterised queries |
| **XSS Prevention** | Django's auto-escaping in templates |
| **Session Security** | Server-side sessions, secure cookies in production |
| **Password Reset** | Time-limited, single-use tokens via email |
| **Admin Access Control** | `@login_required` + `is_superuser` checks |
| **Data Cascade** | User deletion removes all associated predictions and surveys |
| **Database SSL** | `sslmode=require` enforced for PostgreSQL connections |
| **Secret Key** | Environment variable, auto-generated on Render |

---

## 13. Future Enhancements

1. **Expanded Dataset:** Incorporate additional diabetes datasets (e.g., Kaggle's Diabetes Health Indicators) for improved generalisation.
2. **Deep Learning Models:** Experiment with neural network architectures (MLP, TabNet) alongside the stacking ensemble.
3. **Real-Time Model Retraining:** Implement online learning from accumulated user predictions (with consent).
4. **Mobile Application:** Develop a companion mobile app using Django REST Framework + React Native.
5. **Explainable AI (XAI):** Integrate SHAP or LIME explanations for individual predictions.
6. **Additional Languages:** Extend i18n support to more Indian languages (Telugu, Kannada, Malayalam).
7. **Wearable Integration:** Accept real-time glucose data from CGM devices.
8. **Federated Learning:** Enable multi-institution model training without data sharing.

---

## 14. References

1. Smith, J.W., Everhart, J.E., Dickson, W.C., Knowler, W.C., & Johannes, R.S. (1988). Using the ADAP learning algorithm to forecast the onset of diabetes mellitus. *Proceedings of the Annual Symposium on Computer Application in Medical Care*, 261–265.
2. Wolpert, D.H. (1992). Stacked generalization. *Neural Networks*, 5(2), 241–259.
3. Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of the 22nd ACM SIGKDD*, 785–794.
4. Ke, G., et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems*, 30.
5. Chawla, N.V., et al. (2002). SMOTE: Synthetic Minority Over-sampling Technique. *JAIR*, 16, 321–357.
6. International Diabetes Federation. (2021). *IDF Diabetes Atlas*, 10th Edition.

---

## 15. Authors & Acknowledgements

*[To be filled by the authors]*

**Dataset:** Pima Indians Diabetes Dataset — National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK), sourced via the UCI Machine Learning Repository.

**Framework:** Django Software Foundation. **ML Libraries:** scikit-learn, XGBoost (DMLC), LightGBM (Microsoft).

---

*Document generated for conference paper publication. Last updated: 2025.*
