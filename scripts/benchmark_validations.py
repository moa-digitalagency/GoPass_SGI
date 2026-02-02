import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import random
from app import create_app
from models import db, AccessLog, GoPass, User, Flight
from sqlalchemy.orm import joinedload
from sqlalchemy import event
from sqlalchemy.engine import Engine
from datetime import datetime, timedelta

query_count = 0

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1

def setup_data(app_context):
    # Disable counting during setup
    global query_count
    temp_count = query_count

    with app_context:
        print("Checking for existing AccessLog data...")
        count = AccessLog.query.count()
        if count >= 100:
            print(f"Data already exists ({count} logs). Skipping population.")
            # Reset count
            query_count = temp_count
            return

        print(f"Populating database with {100 - count} AccessLogs...")

        # Ensure we have a flight
        flight = Flight.query.first()
        if not flight:
             flight = Flight(flight_number='TEST', airline='Test', departure_airport='A', arrival_airport='B', departure_time=datetime.now())
             db.session.add(flight)
             db.session.commit()

        # Ensure we have a user (validator)
        validator = User.query.filter_by(role='controller').first()
        if not validator:
             validator = User(username='val', email='val@test.com', password_hash='hash', first_name='Val', last_name='Idator', role='controller')
             db.session.add(validator)
             db.session.commit()

        logs = []
        for i in range(100 - count):
            # Create a GoPass
            gopass = GoPass(
                token=f"TOKEN-{time.time()}-{i}",
                flight_id=flight.id,
                passenger_name=f"Passenger {i}",
                passenger_passport=f"P-{i}",
                status='valid'
            )
            db.session.add(gopass)
            db.session.flush()

            log = AccessLog(
                pass_id=gopass.id,
                validator_id=validator.id,
                validation_time=datetime.now() - timedelta(minutes=i),
                status='valid'
            )
            logs.append(log)

        db.session.bulk_save_objects(logs)
        db.session.commit()
        print("Database populated.")

    # Reset count
    query_count = temp_count

def run_benchmark():
    global query_count
    app = create_app()
    with app.app_context():
        setup_data(app.app_context())

        print("\nStarting benchmark...")

        # Reset query count before benchmark
        query_count = 0

        start_time = time.time()
        iterations = 1
        for _ in range(iterations):
            # The code to be optimized:
            recent_validations = AccessLog.query.options(joinedload(AccessLog.pass_record)).order_by(
                AccessLog.validation_time.desc()
            ).limit(10).all()

            # Simulate template access
            for validation in recent_validations:
                # Accessing the relationship to trigger lazy load
                if validation.pass_record:
                    _ = validation.pass_record.passenger_name

        end_time = time.time()

        print(f"Total time for {iterations} iteration(s): {end_time - start_time:.4f}s")
        print(f"Total queries: {query_count}")
        print(f"Queries per iteration: {query_count / iterations}")

if __name__ == '__main__':
    run_benchmark()
