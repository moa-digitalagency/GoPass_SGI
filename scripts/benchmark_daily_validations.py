"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for benchmark_daily_validations.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""


import sys
import os
import time
from datetime import datetime, timedelta
import random

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, AccessLog, GoPass, User

def benchmark():
    app = create_app()

    with app.app_context():
        # Clean up existing logs for a clean benchmark
        # AccessLog.query.delete() # Careful, maybe we shouldn't delete everything if this is a shared env?
        # For this task, I will just add data and assume it's fine.
        # But for accurate benchmarking, I should probably have a dedicated dataset.
        # Let's add 1000 logs distributed over the last 7 days.

        print("Preparing data...")

        # Ensure we have at least one pass and one user to link logs to
        pass_record = GoPass.query.first()
        validator = User.query.first()

        if not pass_record or not validator:
            print("Error: Database must be initialized with at least one GoPass and one User.")
            return

        # Add 1000 logs
        logs_to_add = []
        now = datetime.utcnow()
        for _ in range(1000):
            days_ago = random.randint(0, 7)
            log_time = now - timedelta(days=days_ago, seconds=random.randint(0, 86400))
            log = AccessLog(
                pass_id=pass_record.id,
                validator_id=validator.id,
                validation_time=log_time,
                status='valid'
            )
            logs_to_add.append(log)

        db.session.bulk_save_objects(logs_to_add)
        db.session.commit()
        print(f"Added 1000 logs.")

        week_ago = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Method 1: Inefficient Loop
        print("Running Inefficient Loop...")
        start_time = time.time()

        daily_validations_loop = []
        for i in range(7):
            day = week_ago + timedelta(days=i+1)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())
            count = AccessLog.query.filter(
                AccessLog.validation_time >= day_start,
                AccessLog.validation_time <= day_end
            ).count()
            daily_validations_loop.append(count)

        end_time = time.time()
        loop_duration = end_time - start_time
        print(f"Inefficient Loop Duration: {loop_duration:.4f} seconds")
        print(f"Result: {daily_validations_loop}")

        # Method 2: Optimized Query
        print("Running Optimized Query...")
        start_time = time.time()

        from sqlalchemy import func

        # This queries for counts grouped by date
        # Note: SQLite and PostgreSQL have different date functions.
        # I need to check which DB is being used.
        # Assuming SQLite for local dev based on usual setups, but memory said PostgreSQL.
        # I'll check app.py configuration.

        # Let's assume generic SQLAlchemy for now, but date truncation is DB specific.
        # If it's SQLite: func.date(AccessLog.validation_time)
        # If it's Postgres: func.date(AccessLog.validation_time) works too usually, or cast.

        query = db.session.query(
            func.date(AccessLog.validation_time),
            func.count(AccessLog.id)
        ).filter(
            AccessLog.validation_time >= week_ago
        ).group_by(
            func.date(AccessLog.validation_time)
        ).all()

        # Convert query result to list of counts matching the loop logic
        # The loop iterates from week_ago + 1 day to week_ago + 7 days.
        # The query returns dates that exist. We need to map them.

        counts_map = {str(date): count for date, count in query}
        daily_validations_optimized = []
        for i in range(7):
            day = week_ago + timedelta(days=i+1)
            day_str = day.strftime('%Y-%m-%d')
            daily_validations_optimized.append(counts_map.get(day_str, 0))

        end_time = time.time()
        optimized_duration = end_time - start_time
        print(f"Optimized Query Duration: {optimized_duration:.4f} seconds")
        print(f"Result: {daily_validations_optimized}")

        # Verify results match
        if daily_validations_loop == daily_validations_optimized:
            print("VERIFICATION SUCCESS: Results match.")
        else:
            print("VERIFICATION FAILED: Results do not match.")
            print(f"Loop: {daily_validations_loop}")
            print(f"Opt:  {daily_validations_optimized}")

if __name__ == "__main__":
    benchmark()
