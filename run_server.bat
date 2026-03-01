@echo off
cd /d "%~dp0"
echo Starting Diabetes Prediction server...
echo Open http://127.0.0.1:8000/ in your browser.
echo Press Ctrl+C to stop.
python manage.py runserver
pause
