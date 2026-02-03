"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for benchmark_stats.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import uuid
import random
from app import create_app
from models import db, GoPass, Flight
from services.pass_service import PassService
from datetime import datetime, timedelta

def setup_data(app_context):
    with app_context:
        db.create_all()
        print("Checking for existing data...")
        # Check if we have enough data
        count = GoPass.query.count()
        if count >= 1000:
            print(f"Data already exists ({count} passes). Skipping population.")
            return

        print(f"Populating database with {1000 - count} GoPasses...")

        # Ensure a flight exists
        flight = Flight.query.first()
        if not flight:
            flight = Flight(
                flight_number='TEST-001',
                airline='Test Air',
                departure_airport='FIH',
                arrival_airport='FBM',
                departure_time=datetime.now() + timedelta(days=1),
                status='scheduled',
                capacity=1000
            )
            db.session.add(flight)
            db.session.commit()
            print("Created test flight.")

        statuses = ['valid', 'consumed', 'expired', 'cancelled']
        passes = []
        for i in range(1000 - count):
            status = random.choice(statuses)
            gopass = GoPass(
                token=f"TEST-{uuid.uuid4()}",
                flight_id=flight.id,
                passenger_name=f"Passenger {i}",
                passenger_passport=f"P-{i}",
                status=status,
                payment_status='paid'
            )
            passes.append(gopass)

        db.session.bulk_save_objects(passes)
        db.session.commit()
        print("Database populated.")

def run_benchmark():
    app = create_app()
    with app.app_context():
        setup_data(app.app_context())

        print("\nStarting benchmark...")
        # Warmup
        PassService.get_statistics()

        start_time = time.time()
        iterations = 50
        for _ in range(iterations):
            stats = PassService.get_statistics()
        end_time = time.time()

        avg_time = (end_time - start_time) / iterations
        print(f"Total time for {iterations} iterations: {end_time - start_time:.4f}s")
        print(f"Average time per call: {avg_time:.6f}s")
        print(f"Stats result: {stats}")

if __name__ == '__main__':
    run_benchmark()
