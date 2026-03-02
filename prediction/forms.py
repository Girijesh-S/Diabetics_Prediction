"""
Forms for Diabetes Prediction application.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_('Email'), widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Username')}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirm Password')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'


class PredictionForm(forms.Form):
    pregnancies = forms.IntegerField(
        min_value=0, max_value=20,
        label=_('Pregnancies'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('0-20 (Male: enter 0)'), 'id': 'pregnancies'})
    )
    glucose = forms.FloatField(
        min_value=50, max_value=300,
        label=_('Glucose'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('50-300 mg/dL'), 'id': 'glucose'})
    )
    blood_pressure = forms.FloatField(
        min_value=40, max_value=200,
        label=_('Blood Pressure'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('40-200 mmHg (40+)'), 'id': 'blood_pressure'})
    )
    weight = forms.FloatField(
        min_value=30, max_value=200,
        label=_('Weight (kg)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('30-200 kg'), 'id': 'weight'})
    )
    height = forms.FloatField(
        min_value=100, max_value=220,
        label=_('Height (cm)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('100-220 cm'), 'id': 'height'})
    )
    age = forms.IntegerField(
        min_value=5, max_value=120,
        label=_('Age'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('5-120 years'), 'id': 'age'})
    )
    
    def clean_blood_pressure(self):
        """Validate blood pressure is not 0 or unrealistic."""
        bp = self.cleaned_data.get('blood_pressure')
        if bp == 0:
            raise forms.ValidationError(_('Blood Pressure cannot be 0. Please enter a realistic value (40-200 mmHg).'))
        if bp < 40 or bp > 200:
            raise forms.ValidationError(_('Blood Pressure should be between 40-200 mmHg.'))
        return bp
    
    def clean_glucose(self):
        """Validate glucose is realistic."""
        glucose = self.cleaned_data.get('glucose')
        if glucose < 50 or glucose > 300:
            raise forms.ValidationError(_('Glucose should be between 50-300 mg/dL.'))
        return glucose
    
    def clean(self):
        """Additional cross-field validation."""
        cleaned_data = super().clean()
        height = cleaned_data.get('height')
        weight = cleaned_data.get('weight')
        
        # Validate reasonable height-weight ratio
        if height and weight:
            height_m = height / 100.0
            bmi = weight / (height_m ** 2)
            if bmi < 10 or bmi > 60:
                raise forms.ValidationError(_('Height and weight combination appears unrealistic. Please check your values.'))
        
        return cleaned_data


class SurveyForm(forms.Form):
    """Form for contributing to the diabetes survey."""
    name = forms.CharField(
        max_length=150,
        label=_('Full Name'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Your full name')})
    )
    age = forms.IntegerField(
        min_value=1, max_value=120,
        label=_('Age'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Your age in years')})
    )
    pregnancies = forms.IntegerField(
        min_value=0, max_value=20,
        label=_('Number of Pregnancies'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Male: enter 0')})
    )
    height = forms.FloatField(
        min_value=100, max_value=220,
        label=_('Height (cm)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Height in centimeters')})
    )
    weight = forms.FloatField(
        min_value=30, max_value=200,
        label=_('Weight (kg)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Weight in kilograms')})
    )
    glucose = forms.FloatField(
        min_value=0, max_value=300,
        label=_('Glucose Level (mg/dL)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Fasting glucose level')})
    )
    blood_pressure = forms.FloatField(
        min_value=0, max_value=200,
        label=_('Blood Pressure (mmHg)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Systolic blood pressure')})
    )
    outcome = forms.ChoiceField(
        choices=[(0, _('No Diabetes')), (1, _('Diabetes'))],
        label=_('Diabetes Diagnosis'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
