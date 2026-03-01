"""
Management command to seed 375 realistic survey records and export to CSV.
Records simulate survey data collected from Dec 15 2025 to Jan 15 2026 in IST.
CSV excludes name and date_recorded for anonymity.
Each record gets a unique user_id in the database.
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
import zoneinfo

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from prediction.models import SurveyResponse


# Realistic Indian names for the survey
INDIAN_FIRST_NAMES_FEMALE = [
    "Priya", "Anita", "Sunita", "Kavita", "Rekha", "Neha", "Pooja", "Deepa",
    "Meena", "Suman", "Radha", "Lata", "Geeta", "Savita", "Rani", "Asha",
    "Kiran", "Meera", "Nisha", "Ritu", "Sarita", "Usha", "Vandana", "Swati",
    "Padma", "Shanti", "Lakshmi", "Saroja", "Divya", "Anjali", "Sneha",
    "Bhavna", "Chitra", "Durga", "Esha", "Farah", "Gauri", "Hema",
    "Indira", "Jaya", "Kamla", "Lalita", "Manju", "Nandini", "Pallavi",
    "Rashmi", "Shalini", "Tanvi", "Uma", "Vidya", "Yamuna", "Zara",
    "Aishwarya", "Bhavani", "Chandni", "Devi", "Ekta", "Falguni",
    "Girija", "Harini", "Isha", "Janaki", "Kusum", "Leela", "Madhavi",
    "Nalini", "Oviya", "Parvati", "Revathi", "Sarala", "Tulsi", "Urmila",
]

INDIAN_FIRST_NAMES_MALE = [
    "Rajesh", "Suresh", "Ramesh", "Mahesh", "Dinesh", "Ganesh", "Arun",
    "Vijay", "Sanjay", "Ajay", "Ravi", "Sunil", "Anil", "Nitin",
    "Amit", "Sumit", "Rohit", "Mohit", "Vivek", "Manoj", "Rakesh",
    "Mukesh", "Deepak", "Ashok", "Girish", "Harish", "Kamal", "Naveen",
    "Pramod", "Satish", "Vinod", "Yogesh", "Ajit", "Bimal", "Chandan",
    "Dilip", "Firoz", "Gopal", "Hari", "Jagdish", "Krishna", "Lalit",
    "Mohan", "Narayan", "Om", "Pankaj", "Raghav", "Shankar", "Tarun",
    "Umesh", "Vikram", "Wasim", "Yash", "Zaheer", "Arjun", "Balaji",
]

INDIAN_LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Reddy",
    "Iyer", "Nair", "Pillai", "Rao", "Das", "Ghosh", "Mukherjee",
    "Banerjee", "Chatterjee", "Bose", "Sen", "Dutta", "Sinha", "Mishra",
    "Pandey", "Tiwari", "Joshi", "Saxena", "Agarwal", "Jain", "Mehta",
    "Shah", "Desai", "Kulkarni", "Patil", "Shinde", "Jadhav", "More",
    "Pawar", "Thakur", "Chauhan", "Yadav", "Dubey", "Srivastava",
    "Trivedi", "Bhatt", "Chopra", "Kapoor", "Malhotra", "Bhatia",
    "Khanna", "Gill", "Dhillon", "Kaur", "Sethi", "Arora", "Bajaj",
    "Choudhary", "Goel", "Mittal", "Rastogi", "Saini", "Tandon",
]


def _realistic_ist_datetime(start_date, end_date):
    """Generate a realistic IST datetime — mostly 8 AM to 9 PM,
    with higher probability on weekdays and morning/evening peaks."""
    ist = zoneinfo.ZoneInfo("Asia/Kolkata")
    total_days = (end_date - start_date).days

    while True:
        day_offset = random.randint(0, total_days)
        dt = start_date + timedelta(days=day_offset)
        weekday = dt.weekday()  # 0=Mon, 6=Sun

        # 80% chance weekday, 20% weekend (realistic clinic/survey pattern)
        if weekday >= 5 and random.random() < 0.35:
            continue  # skip some weekends

        # Realistic hour distribution IST (peaks at 9-11 AM and 4-7 PM)
        hour_weights = {
            7: 2, 8: 5, 9: 12, 10: 15, 11: 12, 12: 8, 13: 5,
            14: 6, 15: 8, 16: 12, 17: 14, 18: 10, 19: 7, 20: 4, 21: 2,
        }
        hours = list(hour_weights.keys())
        weights = list(hour_weights.values())
        hour = random.choices(hours, weights=weights, k=1)[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        result = datetime(dt.year, dt.month, dt.day, hour, minute, second, tzinfo=ist)
        return result


def generate_realistic_record(date_recorded, name, is_female=True):
    """Generate a single realistic survey record.
    is_female controls pregnancy count: males always get 0."""
    # is_female is now passed from caller to match the name list used
    age = random.choices(
        population=list(range(21, 82)),
        weights=[
            3 if a < 25 else
            8 if a < 30 else
            12 if a < 35 else
            15 if a < 40 else
            14 if a < 45 else
            12 if a < 50 else
            10 if a < 55 else
            8 if a < 60 else
            6 if a < 65 else
            4 if a < 70 else
            3 if a < 75 else
            2
            for a in range(21, 82)
        ],
        k=1
    )[0]

    if is_female:
        if age < 25:
            pregnancies = random.choices([0, 1, 2], weights=[50, 35, 15], k=1)[0]
        elif age < 35:
            pregnancies = random.choices([0, 1, 2, 3, 4], weights=[15, 25, 30, 20, 10], k=1)[0]
        elif age < 45:
            pregnancies = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[5, 10, 20, 25, 20, 12, 8], k=1)[0]
        else:
            pregnancies = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8], weights=[3, 8, 15, 20, 20, 15, 10, 5, 4], k=1)[0]
    else:
        pregnancies = 0

    # Height (cm) - realistic Indian population
    if is_female:
        height = round(random.gauss(155, 6), 1)
        height = max(140, min(175, height))
    else:
        height = round(random.gauss(168, 7), 1)
        height = max(150, min(190, height))

    # Weight (kg) - varies with height and age
    base_weight = (height - 100) * 0.9
    weight_variation = random.gauss(0, 8)
    weight = round(base_weight + weight_variation + (age * 0.1), 1)
    weight = max(40, min(130, weight))

    # BMI for outcome determination
    height_m = height / 100.0
    bmi = weight / (height_m ** 2)

    # Glucose - bimodal: normal vs elevated
    if random.random() < 0.35:
        glucose = round(random.gauss(145, 30), 1)
        glucose = max(100, min(250, glucose))
    else:
        glucose = round(random.gauss(95, 15), 1)
        glucose = max(60, min(160, glucose))

    # Blood Pressure
    if age > 50:
        bp = round(random.gauss(82, 12), 1)
    else:
        bp = round(random.gauss(72, 10), 1)
    bp = max(50, min(140, bp))

    # Determine outcome based on realistic risk factors
    risk_score = 0
    if glucose > 140:
        risk_score += 3
    elif glucose > 120:
        risk_score += 2
    elif glucose > 100:
        risk_score += 1
    if bmi > 35:
        risk_score += 3
    elif bmi > 30:
        risk_score += 2
    elif bmi > 25:
        risk_score += 1
    if age > 55:
        risk_score += 2
    elif age > 40:
        risk_score += 1
    if pregnancies > 5:
        risk_score += 2
    elif pregnancies > 3:
        risk_score += 1
    if bp > 90:
        risk_score += 1

    # Probability-based outcome
    prob_diabetes = min(0.85, max(0.05, risk_score / 12))
    outcome = 1 if random.random() < prob_diabetes else 0

    return {
        'name': name,
        'gender': 'Female' if is_female else 'Male',
        'age': age,
        'pregnancies': pregnancies,
        'height': height,
        'weight': weight,
        'glucose': round(glucose, 1),
        'blood_pressure': round(bp, 1),
        'outcome': outcome,
        'date_recorded': date_recorded,
    }


class Command(BaseCommand):
    help = 'Seed 375 realistic survey records and export to CSV (without name & date)'

    def handle(self, *args, **options):
        self.stdout.write("Seeding 375 survey records...")

        # Clear existing survey data and old survey users
        SurveyResponse.objects.all().delete()
        User.objects.filter(username__startswith='survey_user_').delete()

        # Date range: Dec 15, 2025 to Jan 15, 2026 (IST)
        ist = zoneinfo.ZoneInfo("Asia/Kolkata")
        start_date = datetime(2025, 12, 15, tzinfo=ist)
        end_date = datetime(2026, 1, 15, tzinfo=ist)

        # Create 375 UNIQUE users — one per survey record
        # Pre-hash a single password to avoid 375 slow PBKDF2 calls
        from django.contrib.auth.hashers import make_password
        hashed_pw = make_password('SurveyPass123!')

        user_objects = []
        for i in range(1, 376):
            user_objects.append(User(
                username=f"survey_user_{i:04d}",
                email=f'survey_user_{i:04d}@survey.example.com',
                password=hashed_pw,
            ))
        survey_users = User.objects.bulk_create(user_objects)

        records = []
        csv_rows = []

        for i in range(375):
            # Generate realistic IST datetime
            record_date = _realistic_ist_datetime(start_date, end_date)

            # Decide gender FIRST, then pick name from matching list
            is_female = random.random() < 0.65
            if is_female:
                first = random.choice(INDIAN_FIRST_NAMES_FEMALE)
            else:
                first = random.choice(INDIAN_FIRST_NAMES_MALE)
            last = random.choice(INDIAN_LAST_NAMES)
            full_name = f"{first} {last}"

            # Pass gender flag so pregnancy is 0 for males
            record = generate_realistic_record(record_date, full_name, is_female=is_female)

            # Each record gets its own unique user
            user = survey_users[i]

            survey = SurveyResponse(
                user=user,
                name=record['name'],
                age=record['age'],
                pregnancies=record['pregnancies'],
                height=record['height'],
                weight=record['weight'],
                glucose=record['glucose'],
                blood_pressure=record['blood_pressure'],
                outcome=record['outcome'],
                date_recorded=record['date_recorded'],
            )
            records.append(survey)
            csv_rows.append(record)

        # Bulk create
        SurveyResponse.objects.bulk_create(records)
        self.stdout.write(self.style.SUCCESS(f"Created {len(records)} survey records with {len(survey_users)} unique users."))

        # Count outcomes
        diabetes_count = sum(1 for r in csv_rows if r['outcome'] == 1)
        no_diabetes_count = len(csv_rows) - diabetes_count
        self.stdout.write(f"  Diabetes: {diabetes_count}, No Diabetes: {no_diabetes_count}")

        # Export to CSV — WITHOUT name and date_recorded
        csv_path = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'survey_data.csv'
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'gender', 'age', 'pregnancies', 'height', 'weight',
                'glucose', 'blood_pressure', 'outcome',
            ])
            writer.writeheader()
            for row in sorted(csv_rows, key=lambda x: x['date_recorded']):
                writer.writerow({
                    'gender': row['gender'],
                    'age': row['age'],
                    'pregnancies': row['pregnancies'],
                    'height': row['height'],
                    'weight': row['weight'],
                    'glucose': row['glucose'],
                    'blood_pressure': row['blood_pressure'],
                    'outcome': row['outcome'],
                })

        self.stdout.write(self.style.SUCCESS(f"CSV exported to {csv_path} (without name & date_recorded)"))
