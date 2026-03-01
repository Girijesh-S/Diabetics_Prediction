#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Create superusers if they don't exist
python manage.py shell -c "
from django.contrib.auth.models import User

if not User.objects.filter(username='HariKrish').exists():
    User.objects.create_superuser('HariKrish', 'admin@diabetespredict.com', 'Hari123')
    print('✓ Superuser created: HariKrish')
else:
    print('✓ HariKrish already exists')

if not User.objects.filter(username='Rishi').exists():
    User.objects.create_superuser('Rishi', 'rishi@diabetespredict.com', 'Rishi123')
    print('✓ Superuser created: Rishi')
else:
    print('✓ Rishi already exists')
"

# Seed survey data (375 records)
python manage.py seed_survey 