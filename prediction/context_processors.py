"""
Context processors for prediction app.
"""
from django.utils.translation import get_language


def language_processor(request):
    """Add current language and available languages to template context."""
    return {
        'current_lang': get_language(),
        'languages': [
            ('en', 'English'),
            ('ta', 'தமிழ்'),
            ('hi', 'हिन्दी'),
        ],
    }
