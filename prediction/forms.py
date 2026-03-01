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
        min_value=0, max_value=300,
        label=_('Glucose'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('0-199 mg/dL'), 'id': 'glucose'})
    )
    blood_pressure = forms.FloatField(
        min_value=0, max_value=200,
        label=_('Blood Pressure'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('0-122 mmHg'), 'id': 'blood_pressure'})
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
        min_value=1, max_value=120,
        label=_('Age'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('21-81 years'), 'id': 'age'})
    )


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
