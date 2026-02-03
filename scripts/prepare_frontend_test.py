"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for prepare_frontend_test.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from app import create_app
from models import db, Flight
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # Create a flight for today
    today = datetime.now()
    flight_num = 'TEST-TODAY'

    existing = Flight.query.filter_by(flight_number=flight_num).first()
    if existing:
        existing.departure_time = today
        db.session.commit()
        print(f"Updated existing flight {flight_num} to today.")
    else:
        flight = Flight(
            flight_number=flight_num,
            airline='Test Airline',
            departure_airport='FIH',
            arrival_airport='FBM',
            departure_time=today,
            arrival_time=today + timedelta(hours=2),
            status='scheduled',
            source='manual',
            capacity=100
        )
        db.session.add(flight)
        db.session.commit()
        print(f"Created flight {flight_num} for today.")
