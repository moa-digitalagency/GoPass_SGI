"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for benchmark_validations.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import sys
import os
import time
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, AccessLog, User, GoPass
from sqlalchemy import func

app = create_app('default')

def setup_data():
    """Populate AccessLog with 10,000 entries over the last 10 days"""
    with app.app_context():
        # Check if we have enough data
        count = AccessLog.query.count()
        if count >= 10000:
            print(f"Data already exists: {count} records. Skipping setup.")
            return

        print(f"Generating data... Current count: {count}")

        # Ensure we have dependencies
        holder = User.query.filter_by(role='holder').first()
        validator = User.query.filter_by(role='agent').first()
        pass_record = GoPass.query.first()

        if not (holder and validator and pass_record):
            print("Missing dependencies (users/pass). Run init_db.py first.")
            # Create a dummy user/pass if missing, just for benchmark?
            # Better to rely on init_db.py
            return

        logs = []
        now = datetime.utcnow()
        for i in range(10000):
            # Random time in last 10 days
            days_ago = random.randint(0, 10)
            seconds_ago = random.randint(0, 86400)
            validation_time = now - timedelta(days=days_ago, seconds=seconds_ago)

            log = AccessLog(
                pass_id=pass_record.id,
                validator_id=validator.id,
                validation_time=validation_time,
                status='valid'
            )
            logs.append(log)

            if len(logs) >= 1000:
                db.session.add_all(logs)
                db.session.commit()
                logs = []

        if logs:
            db.session.add_all(logs)
            db.session.commit()

        print(f"Data generation complete. Total records: {AccessLog.query.count()}")

def get_validations_n_plus_1():
    """Simulate the N+1 query loop"""
    week_ago = datetime.utcnow().date() - timedelta(days=7)
    daily_validations = []

    for i in range(7):
        day = week_ago + timedelta(days=i+1)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())

        count = AccessLog.query.filter(
            AccessLog.validation_time >= day_start,
            AccessLog.validation_time <= day_end
        ).count()

        daily_validations.append(count)
    return daily_validations

def get_validations_aggregated():
    """Use the optimized aggregation query"""
    week_ago = datetime.utcnow().date() - timedelta(days=7)

    results = db.session.query(
        func.date(AccessLog.validation_time),
        func.count(AccessLog.id)
    ).filter(
        AccessLog.validation_time >= week_ago
    ).group_by(
        func.date(AccessLog.validation_time)
    ).all()

    counts_map = {str(r[0]): r[1] for r in results}

    daily_validations = []
    for i in range(7):
        day = week_ago + timedelta(days=i+1)
        day_str = day.strftime('%Y-%m-%d')
        daily_validations.append(counts_map.get(day_str, 0))

    return daily_validations

def benchmark():
    with app.app_context():
        print("Running benchmark...")

        # Warm up
        get_validations_n_plus_1()
        get_validations_aggregated()

        iterations = 50

        # Measure N+1
        start_time = time.time()
        for _ in range(iterations):
            get_validations_n_plus_1()
        duration_n1 = (time.time() - start_time) / iterations
        print(f"N+1 Approach (Avg of {iterations} runs): {duration_n1:.5f} seconds")

        # Measure Aggregated
        start_time = time.time()
        for _ in range(iterations):
            get_validations_aggregated()
        duration_agg = (time.time() - start_time) / iterations
        print(f"Aggregated Approach (Avg of {iterations} runs): {duration_agg:.5f} seconds")

        if duration_n1 > 0:
            improvement = (duration_n1 - duration_agg) / duration_n1 * 100
            print(f"Improvement: {improvement:.2f}%")
        else:
            print("N+1 duration was 0, cannot calculate improvement.")

if __name__ == '__main__':
    setup_data()
    benchmark()
