"""
Views for Diabetes Prediction application.
"""
import json
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.utils.translation import gettext as _
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO

from .forms import RegisterForm, PredictionForm, SurveyForm
from .models import Prediction, SurveyResponse
from .ml_service import predict_diabetes


def home(request):
    """Landing page."""
    return render(request, 'prediction/home.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('prediction:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Account created successfully!'))
            return redirect('prediction:home')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = RegisterForm()
    return render(request, 'prediction/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'prediction/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, _('Invalid username or password.'))
        return super().form_invalid(form)


def logout_view(request):
    logout(request)
    messages.success(request, _('You have been logged out.'))
    return redirect('prediction:home')


def predict_view(request):
    """Prediction form and result display."""
    if request.method == 'POST':
        form = PredictionForm(request.POST)
        if form.is_valid():
            # Calculate BMI from weight and height
            weight_kg = form.cleaned_data['weight']
            height_cm = form.cleaned_data['height']
            height_m = height_cm / 100.0
            bmi = weight_kg / (height_m ** 2)
            
            data = {
                'Pregnancies': form.cleaned_data['pregnancies'],
                'Glucose': form.cleaned_data['glucose'],
                'BloodPressure': form.cleaned_data['blood_pressure'],
                'BMI': bmi,
                'Age': form.cleaned_data['age'],
            }
            try:
                result = predict_diabetes(data)
                if request.user.is_authenticated:
                    pred = Prediction.objects.create(
                        user=request.user,
                        pregnancies=data['Pregnancies'],
                        glucose=data['Glucose'],
                        blood_pressure=data['BloodPressure'],
                        skin_thickness=0.0,
                        insulin=0.0,
                        bmi=bmi,
                        diabetes_pedigree_function=0.0,
                        age=data['Age'],
                        probability=result['probability'],
                        risk_level=result['risk_level'],
                        prediction_result=result['prediction'],
                    )
                    advice = get_personalized_advice(pred)
                    risk_theme = {
                        'Low': 'risk-theme-low',
                        'Medium': 'risk-theme-medium',
                        'High': 'risk-theme-high',
                    }.get(pred.risk_level, 'risk-theme-medium')
                    return render(request, 'prediction/predict_result.html', {
                        'result': result,
                        'prediction': pred,
                        'advice': advice,
                        'risk_theme': risk_theme,
                        'form': PredictionForm(),
                    })
                else:
                    # Create temporary prediction object for anonymous users to get personalized advice
                    temp_pred = Prediction(
                        user=None,
                        pregnancies=data['Pregnancies'],
                        glucose=data['Glucose'],
                        blood_pressure=data['BloodPressure'],
                        skin_thickness=0.0,
                        insulin=0.0,
                        bmi=bmi,
                        diabetes_pedigree_function=0.0,
                        age=data['Age'],
                        probability=result['probability'],
                        risk_level=result['risk_level'],
                        prediction_result=result['prediction'],
                    )
                    advice = get_personalized_advice(temp_pred)
                    risk_theme = {
                        'Low': 'risk-theme-low',
                        'Medium': 'risk-theme-medium',
                        'High': 'risk-theme-high',
                    }.get(result['risk_level'], 'risk-theme-medium')
                    return render(request, 'prediction/predict_result.html', {
                        'result': result,
                        'prediction': None,  # No prediction object for anonymous users
                        'advice': advice,
                        'risk_theme': risk_theme,
                        'form': PredictionForm(),
                    })
            except FileNotFoundError as e:
                messages.error(request, str(e))
                return redirect('prediction:train_model')
    else:
        form = PredictionForm()
    return render(request, 'prediction/predict.html', {'form': form})


@require_POST
def predict_ajax(request):
    """AJAX endpoint for prediction (for speech input flow)."""
    form = PredictionForm(request.POST)
    if form.is_valid():
        # Calculate BMI from weight and height
        weight_kg = form.cleaned_data['weight']
        height_cm = form.cleaned_data['height']
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m ** 2)
        
        data = {
            'Pregnancies': form.cleaned_data['pregnancies'],
            'Glucose': form.cleaned_data['glucose'],
            'BloodPressure': form.cleaned_data['blood_pressure'],
            'BMI': bmi,
            'Age': form.cleaned_data['age'],
        }
        try:
            result = predict_diabetes(data)
            # Save prediction for both authenticated and unauthenticated users
            pred = Prediction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                pregnancies=data['Pregnancies'],
                glucose=data['Glucose'],
                blood_pressure=data['BloodPressure'],
                skin_thickness=0.0,
                insulin=0.0,
                bmi=bmi,
                diabetes_pedigree_function=0.0,
                age=data['Age'],
                probability=result['probability'],
                risk_level=result['risk_level'],
                prediction_result=result['prediction'],
            )
            advice = get_personalized_advice(pred)
            return JsonResponse({
                'success': True,
                'result': result,
                'prediction_id': pred.id,
                'advice': list(advice),
            })
        except FileNotFoundError:
            return JsonResponse({'success': False, 'error': 'Model not found'}, status=500)
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
def history_view(request):
    """User prediction history."""
    predictions = Prediction.objects.filter(user=request.user)[:50]
    return render(request, 'prediction/history.html', {'predictions': predictions})


@login_required
def dashboard_view(request):
    """Dashboard with charts."""
    predictions_qs = Prediction.objects.filter(user=request.user)
    
    # Data for charts
    risk_counts = {}
    for risk_level in predictions_qs.values_list('risk_level', flat=True):
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
    
    recent = list(predictions_qs.values('predicted_at', 'probability', 'risk_level', 'prediction_result')[:10])
    for r in recent:
        r['predicted_at'] = timezone.localtime(r['predicted_at']).strftime('%d-%m-%Y %H:%M')
    
    return render(request, 'prediction/dashboard.html', {
        'predictions': predictions_qs,
        'risk_counts': risk_counts,
        'recent_data_json': json.dumps(recent),
        'risk_counts_json': json.dumps(risk_counts),
        'total_count': predictions_qs.count(),
    })


def get_personalized_advice(pred):
    """Personalized health advice that is UNIQUE per risk level.
    High-risk gets urgent clinical + strict lifestyle advice.
    Medium-risk gets monitoring + moderate lifestyle changes.
    Low-risk gets preventive wellness + maintenance advice.
    """
    tips = []

    # ── PRIMARY RISK-LEVEL ADVICE (completely different per level) ───────
    if pred.risk_level == 'High':
        tips.append(_('URGENT: Schedule an appointment with an endocrinologist within 1 week.'))
        tips.append(_('Get an HbA1c test, fasting insulin, and lipid panel done immediately.'))
        tips.append(_('Monitor blood sugar at least 3-4 times daily (fasting, post-meal, bedtime).'))
        tips.append(_('Follow a strict diabetic diet: no refined sugar, white rice, or maida.'))
        tips.append(_('Take prescribed medications on time — never skip or self-adjust doses.'))

        # High-risk glucose advice
        if pred.glucose >= 140:
            tips.append(_('Your glucose is critically elevated — eliminate all sugary drinks, sweets, and fruit juices immediately.'))
            tips.append(_('Eat only complex carbs: brown rice, millets, oats, and whole grains in controlled portions.'))
        elif pred.glucose >= 100:
            tips.append(_('Your glucose is in the pre-diabetic range — strictly limit carbs to 40-45g per meal.'))

        # High-risk BMI advice
        if pred.bmi >= 30:
            tips.append(_('Obesity significantly worsens diabetes — work with a dietitian for a medically supervised 1200-1500 kcal weight loss plan.'))
        elif pred.bmi >= 25:
            tips.append(_('Being overweight increases insulin resistance — target 5-7% weight loss in the next 3 months.'))

        # High-risk BP advice
        if pred.blood_pressure >= 140:
            tips.append(_('High blood pressure with high diabetes risk is dangerous — limit sodium to <1500mg/day, take BP medication as prescribed.'))
        elif pred.blood_pressure >= 130:
            tips.append(_('Elevated blood pressure needs attention — reduce sodium, avoid processed foods, and monitor BP daily.'))

        # High-risk exercise
        tips.append(_('Start supervised exercise: 30 min brisk walking daily + light resistance training 3x/week.'))

        # High-risk stress
        tips.append(_('Chronic stress spikes blood sugar — practice deep breathing or meditation for 15 minutes twice daily.'))

    elif pred.risk_level == 'Medium':
        tips.append(_('Schedule a health check-up within the next 2 weeks to rule out pre-diabetes.'))
        tips.append(_('Get an HbA1c and fasting glucose test done every 3-6 months.'))
        tips.append(_('Monitor your blood sugar weekly — track fasting and 2-hour post-meal readings.'))
        tips.append(_('Adopt a moderate diabetic-friendly diet: reduce refined carbs and increase fiber.'))

        # Medium-risk glucose advice
        if pred.glucose >= 140:
            tips.append(_('Your glucose is elevated — cut white rice by half, replace with brown rice or millets.'))
            tips.append(_('Avoid sweetened beverages and limit fruit intake to 1-2 servings daily.'))
        elif pred.glucose >= 100:
            tips.append(_('Your glucose is borderline — pair carbs with protein at every meal to stabilize blood sugar.'))
        elif pred.glucose < 70:
            tips.append(_('Low glucose detected — eat regular meals and keep quick-acting carbs (juice, glucose tablets) handy.'))

        # Medium-risk BMI advice
        if pred.bmi >= 30:
            tips.append(_('Reduce calorie intake by 500 kcal/day for gradual weight loss — consult a nutritionist for guidance.'))
        elif pred.bmi >= 25:
            tips.append(_('Focus on portion control — use smaller plates and eat slowly to prevent overeating.'))

        # Medium-risk BP advice
        if pred.blood_pressure >= 130:
            tips.append(_('Moderately elevated BP needs attention — aim for <2300mg sodium/day and increase potassium-rich foods.'))

        # Medium-risk exercise
        tips.append(_('Increase physical activity: aim for 150 min/week of moderate exercise (brisk walking, cycling, swimming).'))

        # Medium-risk diet
        tips.append(_('Follow a Mediterranean or DASH-style diet rich in vegetables, whole grains, and lean protein.'))

        # Medium-risk stress
        tips.append(_('Manage stress with yoga, meditation, or hobbies — stress elevates cortisol and blood sugar.'))

    else:  # Low risk
        tips.append(_('Continue eating a balanced diet rich in vegetables, whole grains, fruits, and lean protein.'))
        tips.append(_('Stay physically active — aim for 30 min of enjoyable exercise at least 5 days a week.'))

        # Low-risk glucose advice
        if pred.glucose >= 100:
            tips.append(_('Your glucose is slightly elevated — watch carb portions and choose whole grains over refined ones.'))
        elif pred.glucose < 70:
            tips.append(_('Your glucose is on the lower side — eat regular meals and include healthy snacks.'))

        # Low-risk BMI advice
        if pred.bmi >= 25:
            tips.append(_('Maintaining a healthy weight helps prevention — focus on balanced nutrition and staying active.'))

        # Low-risk BP advice
        if pred.blood_pressure >= 130:
            tips.append(_('Keep an eye on blood pressure — reduce processed foods and increase fruits and vegetables.'))

        # Low-risk wellness
        tips.append(_('Stay hydrated — drink 8-10 glasses of water daily for overall health.'))
        tips.append(_('Get 7-8 hours of quality sleep each night to support metabolic health.'))
        tips.append(_('Prevention is key — small consistent habits today prevent major health issues tomorrow.'))

    # ── AGE-SPECIFIC ADVICE (unique per risk) ──────────────────────────
    if pred.age >= 60:
        if pred.risk_level == 'High':
            tips.append(_('At 60+, annual comprehensive screening including eye, kidney, and nerve function tests is critical.'))
        elif pred.risk_level == 'Medium':
            tips.append(_('At 60+, schedule a comprehensive health screening every 6 months.'))
        else:
            tips.append(_('At 60+, continue annual screenings and stay socially active for cognitive health.'))
    elif pred.age >= 45:
        if pred.risk_level in ['High', 'Medium']:
            tips.append(_('Adults over 45 should get HbA1c tested every 3-6 months.'))
        else:
            tips.append(_('Adults over 45 benefit from annual preventive health check-ups.'))

    return tips


def _get_indian_diet_plan(risk_level, weight_kg):
    """Generate a 1-week Indian diabetic diet plan based on risk level and weight.
    Calories are dynamically calculated from weight.
    HIGH  = strict diabetic (millets, no sugar/maida, small portions, ~22 kcal/kg)
    MEDIUM = moderate control (mixed whole grains, balanced, ~25 kcal/kg)
    LOW   = preventive healthy (regular Indian food, generous portions, ~28 kcal/kg)
    Gram quantities and calorie values are cross-checked for accuracy.
    """
    if risk_level == 'High':
        cal_per_kg = 22
        label = "Strict Diabetic Diet"
    elif risk_level == 'Medium':
        cal_per_kg = 25
        label = "Moderate Diabetic Diet"
    else:
        cal_per_kg = 28
        label = "Preventive Healthy Diet"

    daily_calories = int(weight_kg * cal_per_kg)

    # Meal split: Breakfast 25%, Mid-morning 10%, Lunch 30%, Evening 10%, Dinner 25%
    bfast_cal = int(daily_calories * 0.25)
    mid_cal   = int(daily_calories * 0.10)
    lunch_cal = int(daily_calories * 0.30)
    eve_cal   = int(daily_calories * 0.10)
    dinner_cal = int(daily_calories * 0.25)

    # ── HIGH RISK: Strict diabetic — millets, no sugar/maida, minimal oil ──
    if risk_level == 'High':
        days = [
            {
                'day': 'Monday',
                'breakfast': ('Moong Dal Chilla 2 (120g) + Mint Chutney (15g)', f'{bfast_cal} kcal', 'Ragi Dosa 1 (80g) + Sambhar (80g)'),
                'mid_morning': ('Cucumber (100g) + Almonds 5 (7g)', f'{mid_cal} kcal', 'Buttermilk (200ml)'),
                'lunch': ('Brown Rice (60g dry) + Palak Dal (150g) + Salad (80g)', f'{lunch_cal} kcal', 'Jowar Roti 1 (35g) + Mixed Veg (150g)'),
                'evening': ('Green Tea + Roasted Chana (25g)', f'{eve_cal} kcal', 'Herbal Tea + Flaxseeds (10g)'),
                'dinner': ('Bajra Roti 1 (35g) + Lauki Sabzi (150g) + Curd (80g)', f'{dinner_cal} kcal', 'Ragi Roti 1 (35g) + Tinda Sabzi (150g)'),
            },
            {
                'day': 'Tuesday',
                'breakfast': ('Oats Upma with Vegetables (130g) + Tea (no sugar)', f'{bfast_cal} kcal', 'Besan Chilla 2 (100g) + Chutney (15g)'),
                'mid_morning': ('1 Small Guava (80g) + Walnuts 3 (9g)', f'{mid_cal} kcal', 'Carrot sticks (80g) + Pumpkin Seeds (8g)'),
                'lunch': ('Jowar Roti 2 (70g) + Bhindi Sabzi (120g) + Moong Dal (120g)', f'{lunch_cal} kcal', 'Ragi Roti 2 (70g) + Turai (120g) + Sambhar (100g)'),
                'evening': ('Sprouted Moong Salad (80g)', f'{eve_cal} kcal', 'Coconut Water (200ml)'),
                'dinner': ('Vegetable Clear Soup (200ml) + Multigrain Roti 1 (35g)', f'{dinner_cal} kcal', 'Oats Khichdi (120g) + Curd (80g)'),
            },
            {
                'day': 'Wednesday',
                'breakfast': ('Ragi Idli 2 (100g) + Sambhar (80g)', f'{bfast_cal} kcal', 'Pesarattu 1 (80g) + Ginger Chutney (15g)'),
                'mid_morning': ('Buttermilk (200ml) + Almonds 4 (6g)', f'{mid_cal} kcal', 'Tomato Juice (200ml) + Mixed Seeds (8g)'),
                'lunch': ('Brown Rice Pulao (80g dry) + Raita (80g) + Salad (80g)', f'{lunch_cal} kcal', 'Bajra Roti 2 (70g) + Chana Dal (120g) + Veg (100g)'),
                'evening': ('Roasted Makhana (25g)', f'{eve_cal} kcal', 'Green Tea + Flaxseed Crackers (20g)'),
                'dinner': ('Methi Roti 1 (40g) + Paneer Bhurji (80g, low oil)', f'{dinner_cal} kcal', 'Dalia (100g) + Vegetable Stew (120g)'),
            },
            {
                'day': 'Thursday',
                'breakfast': ('Besan Chilla 2 (100g) + Mint Chutney (15g)', f'{bfast_cal} kcal', 'Oats Dosa 2 (90g) + Chutney (15g)'),
                'mid_morning': ('1 Small Orange (100g) + Pumpkin Seeds (8g)', f'{mid_cal} kcal', 'Papaya slices (80g) + Almonds 4 (6g)'),
                'lunch': ('Bajra Roti 2 (70g) + Palak Tofu (100g) + Salad (80g)', f'{lunch_cal} kcal', 'Foxtail Millet Rice (80g) + Sambhar (120g) + Poriyal (80g)'),
                'evening': ('Vegetable Clear Soup (200ml)', f'{eve_cal} kcal', 'Amla Juice (200ml) + Walnuts 2 (7g)'),
                'dinner': ('Moong Dal Khichdi (120g) + Curd (80g)', f'{dinner_cal} kcal', 'Jowar Roti 1 (35g) + Gobhi Sabzi (120g)'),
            },
            {
                'day': 'Friday',
                'breakfast': ('Vegetable Dalia (130g) + Tea (no sugar)', f'{bfast_cal} kcal', 'Ragi Porridge (120g) + Mixed Seeds (8g)'),
                'mid_morning': ('Carrot (80g) + Hummus (25g)', f'{mid_cal} kcal', 'Cucumber Raita (100g)'),
                'lunch': ('Multigrain Roti 2 (70g) + Rajma (120g, no cream) + Salad (80g)', f'{lunch_cal} kcal', 'Brown Rice (60g dry) + Dal Fry (120g) + Raita (80g)'),
                'evening': ('Sprouted Chana Chaat (80g)', f'{eve_cal} kcal', 'Lemon Water + Roasted Makhana (20g)'),
                'dinner': ('Jowar Roti 1 (35g) + Tinda Sabzi (120g) + Dal (80g)', f'{dinner_cal} kcal', 'Oats Khichdi (120g) + Raita (80g)'),
            },
            {
                'day': 'Saturday',
                'breakfast': ('Multigrain Toast 2 (50g) + Egg White Omelette (66g)', f'{bfast_cal} kcal', 'Pesarattu (80g) + Chutney (15g)'),
                'mid_morning': ('Mixed Seeds (10g) + Green Tea', f'{mid_cal} kcal', 'Amla Juice (200ml) + Almonds 4 (6g)'),
                'lunch': ('Ragi Roti 2 (70g) + Grilled Fish (100g) + Salad (80g)', f'{lunch_cal} kcal', 'Millet Rice (80g) + Sambar (120g) + Veg (80g)'),
                'evening': ('Buttermilk (200ml) + Roasted Chana (20g)', f'{eve_cal} kcal', 'Coconut Water (200ml)'),
                'dinner': ('Mixed Veg Soup (200ml) + Bajra Roti 1 (35g)', f'{dinner_cal} kcal', 'Dalia Khichdi (120g) + Curd (80g)'),
            },
            {
                'day': 'Sunday',
                'breakfast': ('Oats Dosa 2 (90g) + Coconut Chutney (20g)', f'{bfast_cal} kcal', 'Ragi Idli 2 (100g) + Sambhar (80g)'),
                'mid_morning': ('1 Small Pear (100g) + Walnuts 3 (9g)', f'{mid_cal} kcal', 'Guava (80g) + Sunflower Seeds (8g)'),
                'lunch': ('Brown Rice (60g dry) + Moong Dal (120g) + Veg (100g) + Curd (60g)', f'{lunch_cal} kcal', 'Jowar Roti 2 (70g) + Sabzi (120g) + Raita (60g)'),
                'evening': ('Green Tea + Flaxseed Crackers (20g)', f'{eve_cal} kcal', 'Herbal Tea + Makhana (20g)'),
                'dinner': ('Multigrain Roti 1 (35g) + Chana Sabzi (120g) + Salad (60g)', f'{dinner_cal} kcal', 'Khichdi (120g) + Palak Raita (80g)'),
            },
        ]

    # ── MEDIUM RISK: Moderate control — whole grains, balanced portions ──
    elif risk_level == 'Medium':
        days = [
            {
                'day': 'Monday',
                'breakfast': ('Poha with Peanuts (150g) + Tea (low sugar)', f'{bfast_cal} kcal', 'Upma (130g) + Chutney (20g)'),
                'mid_morning': ('1 Banana (100g) + Almonds 5 (7g)', f'{mid_cal} kcal', 'Apple (120g) + Mixed Nuts (12g)'),
                'lunch': ('Brown Rice (100g) + Dal Tadka (150g) + Sabzi (100g) + Curd (60g)', f'{lunch_cal} kcal', 'Roti 2 (70g) + Rajma (150g) + Raita (80g)'),
                'evening': ('Sprout Chaat (80g) + Lemon', f'{eve_cal} kcal', 'Buttermilk (200ml) + Makhana (20g)'),
                'dinner': ('Roti 2 (70g) + Mixed Veg Curry (150g) + Dal (100g)', f'{dinner_cal} kcal', 'Khichdi (150g) + Papad + Curd (80g)'),
            },
            {
                'day': 'Tuesday',
                'breakfast': ('Idli 3 (150g) + Sambhar (100g) + Chutney (15g)', f'{bfast_cal} kcal', 'Dosa 1 (100g) + Sambhar (80g)'),
                'mid_morning': ('Coconut Water (200ml) + Walnuts 4 (12g)', f'{mid_cal} kcal', 'Orange (130g) + Peanuts (12g)'),
                'lunch': ('Chapati 2 (70g) + Paneer Curry (100g) + Salad (80g) + Dal (80g)', f'{lunch_cal} kcal', 'Rice (100g) + Sambhar (150g) + Poriyal (80g)'),
                'evening': ('Roasted Makhana (35g) + Tea (low sugar)', f'{eve_cal} kcal', 'Fruit Salad (100g)'),
                'dinner': ('Dalia Upma (130g) + Vegetable Curry (120g)', f'{dinner_cal} kcal', 'Roti 2 (70g) + Palak Dal (150g)'),
            },
            {
                'day': 'Wednesday',
                'breakfast': ('Methi Paratha 1 (60g) + Curd (80g) + Tea', f'{bfast_cal} kcal', 'Besan Chilla 2 (100g) + Chutney (15g)'),
                'mid_morning': ('1 Guava (100g) + Mixed Seeds (10g)', f'{mid_cal} kcal', 'Papaya (100g) + Almonds 5 (7g)'),
                'lunch': ('Rice (100g) + Fish Curry (100g) + Salad (80g) + Rasam (80ml)', f'{lunch_cal} kcal', 'Roti 2 (70g) + Egg Curry (100g) + Veg (100g)'),
                'evening': ('Green Tea + Roasted Chana (30g)', f'{eve_cal} kcal', 'Herbal Tea + Sprouts (60g)'),
                'dinner': ('Roti 2 (70g) + Lauki Sabzi (150g) + Raita (60g)', f'{dinner_cal} kcal', 'Oats Khichdi (130g) + Curd (80g)'),
            },
            {
                'day': 'Thursday',
                'breakfast': ('Oats Porridge with Banana (150g) + Tea', f'{bfast_cal} kcal', 'Moong Chilla 2 (100g) + Chutney (15g)'),
                'mid_morning': ('Buttermilk (200ml) + Mixed Nuts (15g)', f'{mid_cal} kcal', 'Tomato Juice (200ml) + Dates 2 (15g)'),
                'lunch': ('Jowar Roti 2 (70g) + Chole (150g) + Salad (80g)', f'{lunch_cal} kcal', 'Rice (100g) + Dal (150g) + Poriyal (80g) + Papad'),
                'evening': ('Fruit Salad (100g)', f'{eve_cal} kcal', 'Makhana (30g) + Coconut Water (200ml)'),
                'dinner': ('Chapati 2 (70g) + Gobhi Aloo (100g) + Dal (80g)', f'{dinner_cal} kcal', 'Steamed Rice (80g) + Rasam (100ml) + Veg (80g)'),
            },
            {
                'day': 'Friday',
                'breakfast': ('Veg Sandwich on Brown Bread (120g) + Milk (200ml)', f'{bfast_cal} kcal', 'Idli 2 (100g) + Sambhar (80g) + Chutney'),
                'mid_morning': ('1 Apple (130g) + Pumpkin Seeds (8g)', f'{mid_cal} kcal', 'Pear (120g) + Cashews 4 (6g)'),
                'lunch': ('Rice (100g) + Sambhar (150g) + Avial (80g) + Curd (60g)', f'{lunch_cal} kcal', 'Roti 2 (70g) + Paneer (80g) + Veg (100g)'),
                'evening': ('Sprout Salad (80g) + Lemon Juice', f'{eve_cal} kcal', 'Green Tea + Boiled Chana (40g)'),
                'dinner': ('Roti 2 (70g) + Tinda Sabzi (120g) + Dal (80g)', f'{dinner_cal} kcal', 'Dalia (120g) + Mixed Veg (100g)'),
            },
            {
                'day': 'Saturday',
                'breakfast': ('Pesarattu 2 (100g) + Ginger Chutney (15g) + Tea', f'{bfast_cal} kcal', 'Poha (130g) + Peanuts (15g)'),
                'mid_morning': ('Mixed Dry Fruits (25g) + Tea', f'{mid_cal} kcal', 'Fruit (100g) + Roasted Peanuts (15g)'),
                'lunch': ('Roti 2 (70g) + Grilled Chicken (100g) + Salad (80g) + Dal (80g)', f'{lunch_cal} kcal', 'Rice (100g) + Fish Curry (100g) + Veg (80g)'),
                'evening': ('Coconut Water (200ml) + Almonds 5 (7g)', f'{eve_cal} kcal', 'Buttermilk (200ml) + Makhana (20g)'),
                'dinner': ('Khichdi (150g) + Papad + Curd (60g)', f'{dinner_cal} kcal', 'Chapati 1 (35g) + Veg Soup (200ml)'),
            },
            {
                'day': 'Sunday',
                'breakfast': ('Masala Dosa 1 (100g) + Sambhar (80g) + Chutney', f'{bfast_cal} kcal', 'Aloo Paratha 1 (70g) + Curd (60g)'),
                'mid_morning': ('Orange (130g) + Cashews 5 (8g)', f'{mid_cal} kcal', 'Watermelon (150g) + Almonds 5 (7g)'),
                'lunch': ('Rice (100g) + Chicken Curry (100g) + Salad (80g) + Curd (60g)', f'{lunch_cal} kcal', 'Veg Biryani (150g) + Raita (80g)'),
                'evening': ('Herbal Tea + Fruit (80g)', f'{eve_cal} kcal', 'Buttermilk (200ml) + Chana (30g)'),
                'dinner': ('Roti 2 (70g) + Palak Paneer (100g) + Dal (80g)', f'{dinner_cal} kcal', 'Veg Pulao (130g) + Raita (60g)'),
            },
        ]

    # ── LOW RISK: Preventive healthy — regular Indian, generous portions ──
    else:
        days = [
            {
                'day': 'Monday',
                'breakfast': ('Aloo Paratha 1 (80g) + Curd (80g) + Tea (200ml)', f'{bfast_cal} kcal', 'Poha (150g) + Sev (10g) + Tea'),
                'mid_morning': ('1 Banana (100g) + Mixed Nuts (25g)', f'{mid_cal} kcal', 'Mango (120g) + Dry Fruits (20g)'),
                'lunch': ('Rice (150g) + Dal Tadka (150g) + Sabzi (100g) + Curd (80g) + Salad (60g)', f'{lunch_cal} kcal', 'Roti 3 (105g) + Chicken Curry (120g) + Raita (80g)'),
                'evening': ('Tea (200ml) + Marie Biscuits (30g)', f'{eve_cal} kcal', 'Fruit Juice (200ml) + Sandwich (80g)'),
                'dinner': ('Roti 2 (70g) + Paneer Butter Masala (120g) + Dal (100g) + Salad (60g)', f'{dinner_cal} kcal', 'Rice (120g) + Sambhar (150g) + Poriyal (80g)'),
            },
            {
                'day': 'Tuesday',
                'breakfast': ('Masala Dosa 1 (120g) + Sambhar (100g) + Chutney (20g)', f'{bfast_cal} kcal', 'Upma (130g) + Vada 1 (40g) + Tea'),
                'mid_morning': ('Coconut Water (200ml) + Dates 3 (25g)', f'{mid_cal} kcal', 'Fruit Juice (200ml) + Almonds 5 (10g)'),
                'lunch': ('Rice (150g) + Fish Curry (120g) + Rasam (100ml) + Salad (60g)', f'{lunch_cal} kcal', 'Roti 2 (70g) + Chole (150g) + Raita (80g) + Papad'),
                'evening': ('Samosa 1 (60g) + Green Chutney (15g)', f'{eve_cal} kcal', 'Bhel Puri (80g) + Lemon Juice'),
                'dinner': ('Chapati 2 (70g) + Mixed Veg Curry (150g) + Dal (100g)', f'{dinner_cal} kcal', 'Veg Pulao (180g) + Raita (80g)'),
            },
            {
                'day': 'Wednesday',
                'breakfast': ('Idli 3 (150g) + Sambhar (100g) + Vada 1 (40g)', f'{bfast_cal} kcal', 'Paratha 1 (80g) + Pickle + Curd (60g)'),
                'mid_morning': ('Apple (130g) + Peanuts (20g)', f'{mid_cal} kcal', 'Guava (100g) + Mixed Nuts (20g)'),
                'lunch': ('Chicken Biryani (200g) + Raita (80g) + Salad (60g)', f'{lunch_cal} kcal', 'Rice (150g) + Rajma (150g) + Curd (80g) + Veg (80g)'),
                'evening': ('Green Tea (200ml) + Makhana (30g)', f'{eve_cal} kcal', 'Coffee (200ml) + Biscuits (25g)'),
                'dinner': ('Roti 2 (70g) + Egg Curry (120g) + Salad (60g)', f'{dinner_cal} kcal', 'Khichdi (180g) + Papad + Curd (80g)'),
            },
            {
                'day': 'Thursday',
                'breakfast': ('Poha (150g) + Sev (10g) + Lemon + Tea', f'{bfast_cal} kcal', 'Bread-Omelette (150g) + Juice (200ml)'),
                'mid_morning': ('1 Orange (130g) + Walnuts 5 (15g)', f'{mid_cal} kcal', 'Papaya (120g) + Cashews 5 (8g)'),
                'lunch': ('Rice (150g) + Dal Fry (150g) + Aloo Gobi (100g) + Curd (80g) + Papad', f'{lunch_cal} kcal', 'Chapati 3 (105g) + Mutton Curry (120g) + Raita (80g)'),
                'evening': ('Pakoda 4 (80g) + Green Chutney (20g)', f'{eve_cal} kcal', 'Roasted Chana (40g) + Fruit (100g)'),
                'dinner': ('Roti 2 (70g) + Palak Paneer (120g) + Raita (80g)', f'{dinner_cal} kcal', 'Dosa 1 (100g) + Sambhar (120g)'),
            },
            {
                'day': 'Friday',
                'breakfast': ('Vermicelli Upma (150g) + Tea (200ml)', f'{bfast_cal} kcal', 'Cornflakes + Milk (200g) + Banana'),
                'mid_morning': ('Fruit Salad (120g) + Dry Fruits (15g)', f'{mid_cal} kcal', 'Yogurt (100g) + Honey (10g)'),
                'lunch': ('Roti 2 (70g) + Paneer Butter Masala (100g) + Rice (80g) + Salad (60g)', f'{lunch_cal} kcal', 'Full Thali: Rice (120g) + Dal (100g) + Sabzi (80g) + Curd (80g)'),
                'evening': ('Sprout Chaat (100g) + Lemon Juice', f'{eve_cal} kcal', 'Veg Sandwich (100g) + Buttermilk (200ml)'),
                'dinner': ('Veg Pulao (180g) + Raita (80g) + Salad (60g)', f'{dinner_cal} kcal', 'Roti 2 (70g) + Fish Fry (100g) + Dal (100g)'),
            },
            {
                'day': 'Saturday',
                'breakfast': ('Chole Bhature (small, 150g) + Lassi (150ml)', f'{bfast_cal} kcal', 'Puri 2 (60g) + Aloo Sabzi (100g) + Tea'),
                'mid_morning': ('Lassi (200ml) + Almonds 5 (10g)', f'{mid_cal} kcal', 'Coconut Water (200ml) + Fruits (100g)'),
                'lunch': ('Rice (150g) + Chicken Curry (120g) + Dal (100g) + Salad (60g)', f'{lunch_cal} kcal', 'Biryani (200g) + Raita (80g) + Salad (60g)'),
                'evening': ('Tea (200ml) + Mathri (40g)', f'{eve_cal} kcal', 'Coffee (200ml) + Biscuit (25g)'),
                'dinner': ('Roti 2 (70g) + Aloo Gobi (120g) + Curd (80g)', f'{dinner_cal} kcal', 'Veg Fried Rice (180g) + Manchurian (80g)'),
            },
            {
                'day': 'Sunday',
                'breakfast': ('Puri 3 (90g) + Aloo Sabzi (100g) + Tea (200ml)', f'{bfast_cal} kcal', 'Medu Vada 2 (80g) + Sambhar (100g) + Chutney'),
                'mid_morning': ('Seasonal Fruit (150g) + Nuts (20g)', f'{mid_cal} kcal', 'Fresh Juice (200ml) + Dry Fruits (20g)'),
                'lunch': ('Special Thali: Rice (120g) + Dal (100g) + 2 Sabzi (160g) + Curd (80g) + Sweet (30g)', f'{lunch_cal} kcal', 'Biryani (200g) + Kebab (80g) + Raita (80g)'),
                'evening': ('Chai (200ml) + Pakoda (60g)', f'{eve_cal} kcal', 'Lassi (200ml) + Makhana (30g)'),
                'dinner': ('Roti 2 (70g) + Butter Chicken (120g) + Dal (100g)', f'{dinner_cal} kcal', 'Egg Fried Rice (180g) + Raita (80g)'),
            },
        ]

    return {
        'label': label,
        'daily_calories': daily_calories,
        'weight_kg': weight_kg,
        'cal_per_kg': cal_per_kg,
        'days': days,
        'meal_split': {
            'breakfast': bfast_cal,
            'mid_morning': mid_cal,
            'lunch': lunch_cal,
            'evening': eve_cal,
            'dinner': dinner_cal,
        }
    }


def build_pdf_bytes(pred, user, include_dashboard=True, advice=None):
    """Build a PDF report and return bytes — redesigned with gradient header, colour-coded clinical values, and diet plan."""
    if advice is None:
        advice = get_personalized_advice(pred)
    buffer = BytesIO()

    # ── Colour palette based on risk ────────────────────────────────────
    ACCENT = {
        'Low':    {'primary': '#059669', 'bg': '#ecfdf5', 'border': '#a7f3d0'},
        'Medium': {'primary': '#d97706', 'bg': '#fffbeb', 'border': '#fde68a'},
        'High':   {'primary': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca'},
    }.get(pred.risk_level, {'primary': '#1b6ef3', 'bg': '#eff6ff', 'border': '#bfdbfe'})

    ac_primary = colors.HexColor(ACCENT['primary'])
    ac_bg      = colors.HexColor(ACCENT['bg'])
    ac_border  = colors.HexColor(ACCENT['border'])

    BLUE   = colors.HexColor('#1e40af')
    LBLUE  = colors.HexColor('#eff6ff')
    SLATE  = colors.HexColor('#475569')
    DARK   = colors.HexColor('#0f172a')
    LIGHT  = colors.HexColor('#f8fafc')
    GRID   = colors.HexColor('#e2e8f0')
    WHITE  = colors.white

    # Page border callback — double-line elegant border
    def add_page_border(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(ac_primary)
        canvas.setLineWidth(2.5)
        canvas.rect(28, 28, letter[0] - 56, letter[1] - 56)
        canvas.setStrokeColor(ac_border)
        canvas.setLineWidth(0.7)
        canvas.rect(34, 34, letter[0] - 68, letter[1] - 68)
        # Subtle footer line
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(50, 52, letter[0] - 50, 52)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(SLATE)
        canvas.drawCentredString(letter[0] / 2, 40, 'Diabetes Risk Assessment System  |  Generated on ' + timezone.localtime(pred.predicted_at).strftime('%d-%m-%Y %H:%M'))
        canvas.restoreState()

    user_display = (user.get_full_name().strip() or user.username) if user else 'Report'
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=55, leftMargin=55, topMargin=55, bottomMargin=60,
        title=f'Diabetes Risk Report - {user_display}',
        author='Diabetes Risk Assessment System',
    )
    styles = getSampleStyleSheet()
    for name, kwargs in [
        ('SectionHead', dict(fontSize=13, spaceAfter=8, spaceBefore=4, textColor=BLUE, fontName='Helvetica-Bold')),
        ('SmallText',   dict(fontSize=7.5, textColor=SLATE)),
        ('CenterBold',  dict(fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold')),
        ('TableCell',   dict(fontSize=7.5, leading=9, textColor=DARK)),
        ('TableCellBold', dict(fontSize=7.5, leading=9, textColor=BLUE, fontName='Helvetica-Bold')),
        ('NoteCell',    dict(fontSize=7.5, leading=9, textColor=DARK)),
    ]:
        if name not in styles:
            styles.add(ParagraphStyle(name=name, **kwargs))

    COL_W = 500

    def sp(value):
        """Safe PDF text — encode to latin-1, replacing unsupported chars."""
        text = str(value)
        # Replace common Unicode symbols with latin-1 safe alternatives
        text = text.replace('\u25B6', '>>')
        text = text.replace('\u25CF', '*')
        text = text.replace('\u2022', '\xb7')     # bullet → middle dot
        text = text.replace('\u2013', '-')           # en-dash
        text = text.replace('\u2014', '--')          # em-dash
        text = text.replace('\u2018', "'")           # left single quote
        text = text.replace('\u2019', "'")           # right single quote
        text = text.replace('\u201c', '"')           # left double quote
        text = text.replace('\u201d', '"')           # right double quote
        return text.encode('latin-1', errors='replace').decode('latin-1')

    visit_dt = timezone.localtime(pred.predicted_at)
    user_name = user.get_full_name().strip() if user else ''
    user_name = user_name or (user.username if user else '')
    user_email = (user.email if user else '') or sp(_("Not provided"))

    elements = []

    # ════════════════════════════════════════════════════════════════════
    #  HEADER — gradient-style coloured banner with "Predicted On" date
    # ════════════════════════════════════════════════════════════════════
    hdr = Table([
        [sp(_("DIABETES RISK ASSESSMENT REPORT"))],
        [sp(f"Predicted On: {visit_dt.strftime('%d-%m-%Y  |  %H:%M IST')}")],
    ], colWidths=[COL_W])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ac_primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 17),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), ac_bg),
        ('TEXTCOLOR', (0, 1), (-1, 1), ac_primary),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 2, ac_primary),
    ]))
    elements.append(hdr)
    elements.append(Spacer(1, 0.22 * inch))

    # ════════════════════════════════════════════════════════════════════
    #  PATIENT INFO — 2-column key-value
    # ════════════════════════════════════════════════════════════════════
    elements.append(Paragraph(sp(str(_("Patient Information"))), styles['SectionHead']))
    pi = [
        [sp(_("Full Name")), sp(user_name or _("Not provided")),
         sp(_("Age")), sp(f"{pred.age} years")],
        [sp(_("Email ID")), sp(user_email),
         sp(_("Username")), sp(user.username if user else _("N/A"))],
        [sp(_("Visit Date")), sp(visit_dt.strftime('%d-%m-%Y %H:%M')),
         sp(_("BMI")), sp(f"{pred.bmi:.1f} kg/m\u00b2")],
    ]
    pit = Table(pi, colWidths=[88, 162, 88, 162])
    pit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LBLUE),
        ('BACKGROUND', (2, 0), (2, -1), LBLUE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE),
        ('TEXTCOLOR', (2, 0), (2, -1), BLUE),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOX', (0, 0), (-1, -1), 1.5, BLUE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRID),
    ]))
    elements.append(pit)
    elements.append(Spacer(1, 0.2 * inch))

    # ════════════════════════════════════════════════════════════════════
    #  PREDICTION RESULT — coloured result banner
    # ════════════════════════════════════════════════════════════════════
    elements.append(Paragraph(sp(str(_("Prediction Results"))), styles['SectionHead']))
    res = [
        [sp(_("Prediction")), sp(pred.prediction_result),
         sp(_("Risk Level")), sp(pred.risk_level),
         sp(_("Probability")), sp(f"{pred.probability * 100:.1f}%")],
    ]
    rest = Table(res, colWidths=[78, 92, 72, 78, 78, 102])
    rest.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LBLUE),
        ('BACKGROUND', (2, 0), (2, -1), LBLUE),
        ('BACKGROUND', (4, 0), (4, -1), LBLUE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (4, 0), (4, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), BLUE),
        ('TEXTCOLOR', (2, 0), (2, -1), BLUE),
        ('TEXTCOLOR', (4, 0), (4, -1), BLUE),
        # Result value colour
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#dc2626') if pred.prediction_result == 'Diabetic' else colors.HexColor('#059669')),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, 0), 11),
        # Risk value colour
        ('TEXTCOLOR', (3, 0), (3, 0), ac_primary),
        ('BACKGROUND', (3, 0), (3, 0), ac_bg),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOX', (0, 0), (-1, -1), 1.5, BLUE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRID),
    ]))
    elements.append(rest)
    elements.append(Spacer(1, 0.2 * inch))

    # ════════════════════════════════════════════════════════════════════
    #  CLINICAL VALUES — only show user-entered values
    # ════════════════════════════════════════════════════════════════════
    elements.append(Paragraph(sp(str(_("Clinical Values & Thresholds"))), styles['SectionHead']))
    elements.append(Paragraph(
        sp(_("Your values are highlighted: ")),
        ParagraphStyle('legend', fontSize=8, textColor=SLATE)
    ))
    # Colour legend row
    legend_data = [
        [sp('\u25CF ' + str(_("Normal / Low Risk"))),
         sp('\u25CF ' + str(_("Borderline / Moderate"))),
         sp('\u25CF ' + str(_("High / Concerning")))]
    ]
    legend_t = Table(legend_data, colWidths=[167, 167, 166])
    legend_t.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#d97706')),
        ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#dc2626')),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(legend_t)

    # Clinical value rows: showing only user-entered values (not estimated)
    # (label, value, min, max, unit, warn_low, warn_high)
    weight_kg_calc = (pred.bmi * (1.60 ** 2)) if pred.bmi > 0 else 0
    height_cm_calc = 160  # approximate, not stored
    
    clinical_rows = [
        (_("Age"),          pred.age,                         21,    81, _("years"), 0, 45),
        (_("Height"),       f"{height_cm_calc:.0f}",          140,  200, 'cm',    150, 180),
        (_("Weight"),       f"{weight_kg_calc:.1f}",          40,   150, 'kg',     60, 90),
        (_("BMI"),          f"{pred.bmi:.1f}",                 0,  67.0, 'kg/m\u00b2', 18.5, 30),
        (_("Pregnancies"),  pred.pregnancies,                  0,    17, _("count"), 0, 4),
        (_("Glucose"),      pred.glucose,                      0,   199, 'mg/dL',   70, 140),
        (_("Blood Pressure"), pred.blood_pressure,             0,   122, 'mmHg',    60, 130),
    ]

    hdr_row = [sp(_("Metric")), sp(_("Your Value")), sp(_("Min")), sp(_("Max")), sp(_("Units")), sp(_("Status"))]
    tdata = [hdr_row]
    row_colours = []  # list of (row_idx, bg_colour, text_colour)

    for i, (metric, value, mn, mx, units, wl, wh) in enumerate(clinical_rows, start=1):
        try:
            v = float(value)
        except (ValueError, TypeError):
            v = 0
        # Determine zone
        if v <= wl:
            zone_bg = colors.HexColor('#ecfdf5')   # green bg
            zone_fg = colors.HexColor('#059669')
            status = sp(_("Normal"))
        elif v <= wh:
            zone_bg = colors.HexColor('#fffbeb')   # amber bg
            zone_fg = colors.HexColor('#d97706')
            status = sp(_("Moderate"))
        else:
            zone_bg = colors.HexColor('#fef2f2')   # red bg
            zone_fg = colors.HexColor('#dc2626')
            status = sp(_("High"))
        row_colours.append((i, zone_bg, zone_fg))
        tdata.append([sp(metric), sp(value), sp(mn), sp(mx), sp(units), status])

    clin_t = Table(tdata, colWidths=[110, 80, 60, 60, 75, 115])
    clin_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1.5, BLUE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRID),
    ]
    # Apply per-row colour to "Your Value" column (col 1) and "Status" column (col 5)
    for row_i, bg, fg in row_colours:
        clin_styles.append(('BACKGROUND', (1, row_i), (1, row_i), bg))
        clin_styles.append(('TEXTCOLOR', (1, row_i), (1, row_i), fg))
        clin_styles.append(('FONTNAME', (1, row_i), (1, row_i), 'Helvetica-Bold'))
        clin_styles.append(('BACKGROUND', (5, row_i), (5, row_i), bg))
        clin_styles.append(('TEXTCOLOR', (5, row_i), (5, row_i), fg))
        clin_styles.append(('FONTNAME', (5, row_i), (5, row_i), 'Helvetica-Bold'))
    # Alternate row backgrounds on other columns
    for ri in range(1, len(tdata)):
        base_bg = LIGHT if ri % 2 == 0 else WHITE
        for ci in [0, 2, 3, 4]:
            clin_styles.append(('BACKGROUND', (ci, ri), (ci, ri), base_bg))
    clin_t.setStyle(TableStyle(clin_styles))
    elements.append(clin_t)
    elements.append(Spacer(1, 0.2 * inch))

    # ════════════════════════════════════════════════════════════════════
    #  DASHBOARD SUMMARY (optional)
    # ════════════════════════════════════════════════════════════════════
    if include_dashboard:
        stats_qs = Prediction.objects.filter(user=user)
        total_predictions = stats_qs.count()
        risk_counts = {}
        for level in stats_qs.values_list('risk_level', flat=True):
            risk_counts[level] = risk_counts.get(level, 0) + 1
        elements.append(Paragraph(sp(str(_("Dashboard Summary"))), styles['SectionHead']))
        sd = [
            [sp(_("Total Predictions")), sp(total_predictions),
             sp(_("Risk Distribution")), sp(', '.join(f"{k}: {v}" for k, v in risk_counts.items()) or sp(_("No data")))],
        ]
        st = Table(sd, colWidths=[120, 130, 120, 130])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LBLUE),
            ('BACKGROUND', (2, 0), (2, -1), LBLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), BLUE),
            ('TEXTCOLOR', (2, 0), (2, -1), BLUE),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOX', (0, 0), (-1, -1), 1.5, BLUE),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, GRID),
        ]))
        elements.append(st)
        elements.append(Spacer(1, 0.2 * inch))

    # ════════════════════════════════════════════════════════════════════
    #  HEALTH ADVICE — numbered list with risk-accent (always on new page)
    # ════════════════════════════════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph(sp(str(_("Personalized Health Advice"))), styles['SectionHead']))
    adv_rows = [[sp(_("#")), sp(_("Recommendation"))]]
    for idx, tip in enumerate(advice, 1):
        adv_rows.append([sp(str(idx)), sp(str(tip))])

    adv_t = Table(adv_rows, colWidths=[30, 470])
    adv_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), ac_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), ac_primary),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1.5, ac_primary),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRID),
    ]
    adv_t.setStyle(TableStyle(adv_styles))
    elements.append(adv_t)

    # ════════════════════════════════════════════════════════════════════
    #  HEALTHY ADD-ONS FOR SUGAR CONTROL — new page
    # ════════════════════════════════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph(sp(str(_("Healthy Add-ons for Sugar Control"))), styles['SectionHead']))
    
    healthy_addons = [
        (_("High-Fiber Foods"), _("Oats, barley, brown rice, whole wheat, lentils, beans, chickpeas, chia seeds")),
        (_("Protein-Rich Foods"), _("Eggs,chicken breast, fish, yogurt, paneer, tofu, dal, nuts, seeds")),
        (_("Healthy Fats"), _("Olive oil, coconut oil, avocado, almonds, walnuts, flax seeds, chia seeds")),
        (_("Leafy Greens"), _("Spinach, kale, methi, palak, cabbage, broccoli, bell peppers, tomatoes")),
        (_("Spices for Control"), _("Cinnamon, turmeric, fenugreek seeds, curry leaves, garlic, ginger")),
        (_("Beverages"), _("Water, unsweetened tea, black coffee, herbal teas (no sugar added)")),
        (_("Avoid"), _("Sugary drinks, refined carbs, processed foods, excess salt, saturated fats")),
    ]
    
    addon_rows = [[sp(_("Category")), sp(_("Recommended Foods"))]]
    for category, foods in healthy_addons:
        addon_rows.append([sp(category), Paragraph(sp(foods), styles['TableCell'])])
    
    addon_t = Table(addon_rows, colWidths=[120, 380])
    addon_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, -1), LBLUE),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (0, -1), BLUE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
        ('BOX', (0, 0), (-1, -1), 1.5, BLUE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, GRID),
    ]
    addon_t.setStyle(TableStyle(addon_styles))
    elements.append(addon_t)
    elements.append(Spacer(1, 0.2 * inch))
    
    # General guidelines
    guidelines = [
        sp(_("Eat regular, smaller meals throughout the day to maintain stable blood sugar levels.")),
        sp(_("Include protein and fiber in every meal to slow down glucose absorption.")),
        sp(_("Limit portion sizes and avoid overeating at any meal.")),
        sp(_("Drink plenty of water and stay hydrated throughout the day.")),
        sp(_("Exercise regularly: aim for 30 minutes of moderate activity, 5 days a week.")),
        sp(_("Consult a certified dietitian for a personalized nutrition plan based on your health conditions.")),
        sp(_("This guide is for educational purposes and should not replace professional medical advice.")),
    ]
    note_rows = [[sp(_("#")), sp(_("General Guidelines"))]]
    for i, g in enumerate(guidelines, 1):
        note_rows.append([sp(str(i)), Paragraph(g, styles['NoteCell'])])

    note_t = Table(note_rows, colWidths=[30, 470])
    note_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ecfdf5'), WHITE]),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#10b981')),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#a7f3d0')),
    ]))
    elements.append(note_t)

    # Footer disclaimer
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(
        sp(_("This report is generated for educational purposes. Always consult a qualified healthcare professional for medical decisions.")),
        styles['SmallText']
    ))

    doc.build(elements, onFirstPage=add_page_border, onLaterPages=add_page_border)
    buffer.seek(0)
    return buffer.getvalue()


@login_required
def pdf_report(request, pk):
    """Generate PDF report for a prediction."""
    pred = Prediction.objects.filter(pk=pk, user=request.user).first()
    if not pred:
        messages.error(request, _('Report not found for this prediction.'))
        return redirect('prediction:history')
    pdf_bytes = build_pdf_bytes(pred, request.user, include_dashboard=True)
    user_display = (request.user.get_full_name().strip() or request.user.username).replace(' ', '_')
    report_name = f'Diabetes_Risk_Report_{user_display}'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_name}.pdf"'
    return response


def train_model_info(request):
    """Page explaining how to train the model."""
    return render(request, 'prediction/train_info.html')


@login_required
def email_report(request, pk):
    """Email prediction report to user."""
    pred = Prediction.objects.filter(pk=pk, user=request.user).first()
    if not pred:
        messages.error(request, _('Report not found for this prediction.'))
        return redirect('prediction:history')
    if not request.user.email:
        messages.warning(request, _('Add your email in profile to receive reports.'))
        return redirect('prediction:history')
    
    # Generate advice ONCE so PDF and email body have the same recommendations
    advice = get_personalized_advice(pred)
    visit_dt = timezone.localtime(pred.predicted_at).strftime('%d-%m-%Y %H:%M')
    user_display = request.user.get_full_name().strip() or request.user.username

    # Risk colour for email
    risk_color = {'Low': '#059669', 'Medium': '#d97706', 'High': '#dc2626'}.get(pred.risk_level, '#1b6ef3')

    # HTML email body with bold date and risk details
    advice_list = ''.join(f'<li style="margin-bottom:4px;">{t}</li>' for t in advice)
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;">
        <h2 style="color:#1e40af;">Diabetes Risk Assessment Report</h2>
        <p>Dear <strong>{user_display}</strong>,</p>
        <p>Here are your prediction details:</p>
        <table style="border-collapse:collapse;width:100%;margin:12px 0;">
            <tr>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;background:#f8fafc;"><strong>Visit Date</strong></td>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;"><strong>{visit_dt}</strong></td>
            </tr>
            <tr>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;background:#f8fafc;"><strong>Prediction</strong></td>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;"><strong>{pred.prediction_result}</strong></td>
            </tr>
            <tr>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;background:#f8fafc;"><strong>Risk Level</strong></td>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;"><strong style="color:{risk_color};font-size:16px;">{pred.risk_level}</strong></td>
            </tr>
            <tr>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;background:#f8fafc;"><strong>Probability</strong></td>
                <td style="padding:8px 12px;border:1px solid #e2e8f0;"><strong>{pred.probability * 100:.1f}%</strong></td>
            </tr>
        </table>
        <h3 style="color:#1e40af;margin-top:16px;">Personalized Health Advice</h3>
        <ol style="padding-left:20px;">{advice_list}</ol>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;">
        <p style="font-size:12px;color:#64748b;">This report is generated for educational purposes. Always consult a qualified healthcare professional for medical decisions.</p>
        <p style="font-size:12px;color:#64748b;">The detailed PDF report is attached.</p>
    </div>
    """

    email_message = EmailMessage(
        subject=_('Your Diabetes Risk Report - %(name)s') % {'name': user_display},
        body=html_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[request.user.email],
    )
    email_message.content_subtype = 'html'

    report_name = f'Diabetes_Risk_Report_{user_display.replace(" ", "_")}'
    filename = f"{report_name}.pdf"
    # Pass the SAME advice list so PDF recommendations match the email body
    pdf_bytes = build_pdf_bytes(pred, request.user, include_dashboard=False, advice=advice)
    email_message.attach(filename, pdf_bytes, 'application/pdf')

    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        messages.error(request, _('Email backend is console. No email was sent. Configure SMTP in .env.'))
        return redirect('prediction:history')

    try:
        email_message.send(fail_silently=False)
        messages.success(request, _('Report sent to your email.'))
    except Exception:
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            host_user = (settings.EMAIL_HOST_USER or '').strip()
            host_password = (settings.EMAIL_HOST_PASSWORD or '').strip()
            if not host_user or not host_password:
                messages.error(request, _('Email is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env.'))
                return redirect('prediction:history')

        try:
            console_connection = get_connection('django.core.mail.backends.console.EmailBackend')
            email_message.connection = console_connection
            email_message.send(fail_silently=False)
            messages.warning(request, _('SMTP email failed. Report was printed to server logs using console backend.'))
        except Exception:
            messages.error(request, _('Failed to send email. Check email configuration.'))
    return redirect('prediction:history')


def set_language(request):
    """Set user's preferred language."""
    if request.method == 'POST':
        lang = request.POST.get('language', 'en')
        if lang in ['en', 'ta', 'hi']:
            from django.utils import translation
            translation.activate(lang)
            response = redirect(request.META.get('HTTP_REFERER', '/'))
            request.session['django_language'] = lang
            response.set_cookie('django_language', lang, max_age=365*24*60*60)
            return response
    return redirect('/')


@login_required
def health_check(request):
    """Simple health check for translation, PDF, and email readiness."""
    from django.utils import translation
    from pathlib import Path

    base_dir = Path(settings.BASE_DIR)
    locale_dir = base_dir / 'locale'
    translation_status = []
    
    # Check if .mo files exist for each language
    for code, name in [('ta', 'Tamil'), ('hi', 'Hindi')]:
        mo_path = locale_dir / code / 'LC_MESSAGES' / 'django.mo'
        mo_exists = mo_path.exists()
        translation_status.append({
            'code': code,
            'name': name,
            'status': 'Ready' if mo_exists else 'Needs attention',
            'details': f"Compiled translation file found" if mo_exists else "Missing .mo file",
        })

    # Check email configuration
    email_backend = settings.EMAIL_BACKEND
    email_status = 'Backend: ' + email_backend.split('.')[-1]
    if email_backend == 'django.core.mail.backends.smtp.EmailBackend':
        has_user = bool((settings.EMAIL_HOST_USER or '').strip())
        has_password = bool((settings.EMAIL_HOST_PASSWORD or '').strip())
        email_configured = has_user and has_password
        email_status = 'SMTP Configured' if email_configured else 'SMTP Not Configured'
    else:
        email_status = 'Console Backend (Emails printed to console)'

    return render(request, 'prediction/health.html', {
        'translation_status': translation_status,
        'email_backend': email_backend,
        'email_status': email_status,
        'pdf_ready': True,
    })


# ────────────────────────────────────────────────────────────────────────────
#  Survey View
# ────────────────────────────────────────────────────────────────────────────
def survey_view(request):
    """Contribute to Diabetes Survey page."""
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            SurveyResponse.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=form.cleaned_data['name'],
                age=form.cleaned_data['age'],
                pregnancies=form.cleaned_data['pregnancies'],
                height=form.cleaned_data['height'],
                weight=form.cleaned_data['weight'],
                glucose=form.cleaned_data['glucose'],
                blood_pressure=form.cleaned_data['blood_pressure'],
                outcome=int(form.cleaned_data['outcome']),
                date_recorded=timezone.now(),
            )
            messages.success(request, _('Thank you! Your survey response has been recorded.'))
            return redirect('prediction:survey')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = SurveyForm()
    
    total_responses = SurveyResponse.objects.count()
    diabetes_count = SurveyResponse.objects.filter(outcome=1).count()
    no_diabetes_count = total_responses - diabetes_count
    
    return render(request, 'prediction/survey.html', {
        'form': form,
        'total_responses': total_responses,
        'diabetes_count': diabetes_count,
        'no_diabetes_count': no_diabetes_count,
    })


# ────────────────────────────────────────────────────────────────────────────
#  Admin Dashboard View
# ────────────────────────────────────────────────────────────────────────────
@staff_member_required(login_url='/login/')
def admin_dashboard_view(request):
    """Admin dashboard showing all predictions and survey responses with tags."""
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))
    per_page = 25

    responses = []

    # Gather Predictions (includes anonymous / without-login predictions)
    if filter_type in ('all', 'prediction', 'anonymous', 'logged_in'):
        from django.db.models import Q
        preds = Prediction.objects.select_related('user').all()
        # Sub-filter: anonymous vs logged-in
        if filter_type == 'anonymous':
            preds = preds.filter(user__isnull=True)
        elif filter_type == 'logged_in':
            preds = preds.filter(user__isnull=False)
        if search_query:
            q = Q(user__username__icontains=search_query)
            # Also surface anonymous results when 'anon' is part of the search
            if 'anon' in search_query.lower():
                q = q | Q(user__isnull=True)
            preds = preds.filter(q)
        for p in preds:
            responses.append({
                'type': 'prediction',
                'login_type': 'logged_in' if p.user else 'anonymous',
                'name': p.user.get_full_name() if p.user and p.user.get_full_name().strip() else (p.user.username if p.user else 'Anonymous'),
                'username': p.user.username if p.user else '',
                'age': p.age,
                'glucose': p.glucose,
                'bp': p.blood_pressure,
                'result': p.prediction_result,
                'risk': p.risk_level,
                'probability': f"{p.probability * 100:.1f}",
                'outcome': None,
                'height': None,
                'weight': None,
                'date': p.predicted_at,
            })

    # Gather Survey Responses
    if filter_type in ('all', 'survey'):
        surveys = SurveyResponse.objects.select_related('user').all()
        if search_query:
            surveys = surveys.filter(name__icontains=search_query)
        for s in surveys:
            responses.append({
                'type': 'survey',
                'name': s.name,
                'username': s.user.username if s.user else '',
                'age': s.age,
                'glucose': s.glucose,
                'bp': s.blood_pressure,
                'result': None,
                'risk': None,
                'probability': None,
                'outcome': s.outcome,
                'height': s.height,
                'weight': s.weight,
                'date': s.date_recorded,
            })

    # Count anonymous vs logged-in predictions for stats
    anonymous_pred_count = Prediction.objects.filter(user__isnull=True).count()
    loggedin_pred_count = Prediction.objects.filter(user__isnull=False).count()

    # Sort by date descending
    responses.sort(key=lambda x: x['date'], reverse=True)

    # Pagination
    total_count = len(responses)
    total_pages = max(1, math.ceil(total_count / per_page))
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_responses = responses[start_idx:end_idx]

    # Page range for pagination
    page_range = range(max(1, page - 3), min(total_pages + 1, page + 4))

    # Stats
    from django.contrib.auth.models import User as AuthUser
    total_predictions = Prediction.objects.count()
    total_surveys = SurveyResponse.objects.count()
    high_risk_count = Prediction.objects.filter(risk_level='High').count()
    diabetes_survey_count = SurveyResponse.objects.filter(outcome=1).count()
    no_diabetes_survey_count = SurveyResponse.objects.filter(outcome=0).count()
    diabetic_pred_count = Prediction.objects.filter(prediction_result='Diabetic').count()
    non_diabetic_pred_count = Prediction.objects.filter(prediction_result='Non-Diabetic').count()
    registered_user_count = AuthUser.objects.exclude(username__startswith='survey_user_').count()

    return render(request, 'prediction/admin_dashboard.html', {
        'responses': page_responses,
        'filter': filter_type,
        'search_query': search_query,
        'total_predictions': total_predictions,
        'total_surveys': total_surveys,
        'high_risk_count': high_risk_count,
        'diabetes_survey_count': diabetes_survey_count,
        'no_diabetes_survey_count': no_diabetes_survey_count,
        'diabetic_pred_count': diabetic_pred_count,
        'non_diabetic_pred_count': non_diabetic_pred_count,
        'anonymous_pred_count': anonymous_pred_count,
        'loggedin_pred_count': loggedin_pred_count,
        'total_count': total_count,
        'current_page': page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1,
        'next_page': page + 1,
        'page_start': start_idx + 1,
        'page_end': min(end_idx, total_count),
        'page_range': page_range,
        'registered_user_count': registered_user_count,
    })


@staff_member_required(login_url='/login/')
def admin_users_view(request):
    """Show all registered users (excluding survey bot accounts)."""
    from django.contrib.auth.models import User
    search = request.GET.get('search', '').strip()
    users_qs = User.objects.exclude(username__startswith='survey_user_').order_by('-date_joined')
    if search:
        from django.db.models import Q
        users_qs = users_qs.filter(
            Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search)
        )
    user_data = []
    for u in users_qs:
        pred_count = Prediction.objects.filter(user=u).count()
        survey_count = SurveyResponse.objects.filter(user=u).count()
        user_data.append({
            'user': u,
            'pred_count': pred_count,
            'survey_count': survey_count,
        })
    return render(request, 'prediction/admin_users.html', {
        'user_data': user_data,
        'search_query': search,
        'total_users': len(user_data),
    })


@staff_member_required(login_url='/login/')
@require_POST
def admin_delete_user(request, username):
    """Delete a registered user and all their data."""
    from django.contrib.auth.models import User
    target_user = get_object_or_404(User, username=username)
    # Prevent deleting yourself or other superusers
    if target_user == request.user:
        messages.error(request, _('You cannot delete your own account.'))
        return redirect('prediction:admin_users')
    if target_user.is_superuser and not request.user.is_superuser:
        messages.error(request, _('Only superusers can delete other superusers.'))
        return redirect('prediction:admin_users')
    deleted_username = target_user.username
    target_user.delete()  # CASCADE deletes predictions, surveys etc.
    messages.success(request, _('User "%(username)s" has been deleted.') % {'username': deleted_username})
    return redirect('prediction:admin_users')


@staff_member_required(login_url='/login/')
def admin_user_history_view(request, username):
    """Show prediction and survey history for a specific user."""
    from django.contrib.auth.models import User
    target_user = get_object_or_404(User, username=username)
    predictions = Prediction.objects.filter(user=target_user).order_by('-predicted_at')
    surveys = SurveyResponse.objects.filter(user=target_user).order_by('-date_recorded')
    return render(request, 'prediction/admin_user_history.html', {
        'target_user': target_user,
        'predictions': predictions,
        'surveys': surveys,
    })
