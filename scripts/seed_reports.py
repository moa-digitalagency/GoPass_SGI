import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from models import db, User, Flight, GoPass, AccessLog, PassType
from datetime import datetime, timedelta
import random
import uuid

def seed_reports_data():
    app = create_app()
    with app.app_context():
        print("Seeding reports data...")

        # 1. Clear previous test data (optional, but cleaner)
        # db.session.query(AccessLog).delete()
        # db.session.query(GoPass).delete()
        # db.session.query(Flight).delete()
        # db.session.commit()

        # Ensure we have users
        agent = User.query.filter_by(role='agent').first()
        controller = User.query.filter_by(role='controller').first()
        if not agent or not controller:
            print("Agent or Controller user missing. Run init_db.py first.")
            return

        pass_type = PassType.query.first()

        # 2. Create Flights with Manifest Counts
        # Flight 1: Normal (Manifest = Scanned)
        # Flight 2: Under-declared (Manifest < Scanned) -> Fraud
        # Flight 3: Over-declared (Manifest > Scanned)

        flights_config = [
            {'num': 'CAA-R101', 'dep': 'FIH', 'arr': 'FBM', 'manifest': 20, 'scanned': 20, 'fraud': 0},
            {'num': 'CAA-R102', 'dep': 'FBM', 'arr': 'FIH', 'manifest': 15, 'scanned': 25, 'fraud': 2}, # Red Alert
            {'num': 'CAA-R103', 'dep': 'GOM', 'arr': 'FKI', 'manifest': 30, 'scanned': 10, 'fraud': 0},
            {'num': 'CAA-R104', 'dep': 'FKI', 'arr': 'FIH', 'manifest': 50, 'scanned': 55, 'fraud': 5}  # Red Alert
        ]

        payment_methods = ['Cash', 'M-Pesa', 'Airtel', 'Orange', 'Cash', 'Cash']

        for cfg in flights_config:
            flight = Flight(
                flight_number=cfg['num'],
                airline='CAA',
                departure_airport=cfg['dep'],
                arrival_airport=cfg['arr'],
                departure_time=datetime.utcnow() + timedelta(hours=random.randint(1, 48)),
                status='active',
                capacity=100,
                manifest_pax_count=cfg['manifest']
            )
            db.session.add(flight)
            db.session.commit()

            # Create Passes and Scans
            for i in range(cfg['scanned']):
                # Create Pass
                pass_obj = GoPass(
                    token=f"TOK-{flight.id}-{i}-{uuid.uuid4()}",
                    flight_id=flight.id,
                    pass_number=f"GP-{flight.id}-{i}",
                    passenger_name=f"Passenger {i}",
                    passenger_passport=f"P{i}XYZ",
                    pass_type_id=pass_type.id,
                    price=50.0,
                    currency='USD',
                    payment_status='paid',
                    payment_method=random.choice(payment_methods),
                    sold_by=agent.id,
                    issue_date=datetime.utcnow() - timedelta(hours=random.randint(1, 23)),
                    status='consumed', # scanned
                    scanned_by=controller.id,
                    scan_date=datetime.utcnow(),
                    scan_location=cfg['dep']
                )
                db.session.add(pass_obj)
                db.session.commit()

                # Create Valid AccessLog
                log = AccessLog(
                    pass_id=pass_obj.id,
                    validator_id=controller.id,
                    validation_time=pass_obj.scan_date,
                    status='VALID'
                )
                db.session.add(log)

            # Create Anomalies (Fraud attempts)
            # These are EXTRA scans or invalid scans
            for k in range(cfg['fraud']):
                # Case: Already Scanned
                # Pick an existing pass
                existing_pass = GoPass.query.filter_by(flight_id=flight.id).first()
                if existing_pass:
                    log = AccessLog(
                        pass_id=existing_pass.id,
                        validator_id=controller.id,
                        validation_time=datetime.utcnow() + timedelta(minutes=5),
                        status='ALREADY_SCANNED'
                    )
                    db.session.add(log)

            db.session.commit()

        # Add some random anomalies (Wrong Flight)
        random_pass = GoPass.query.first()
        if random_pass:
            log = AccessLog(
                pass_id=random_pass.id,
                validator_id=controller.id,
                validation_time=datetime.utcnow(),
                status='WRONG_FLIGHT'
            )
            db.session.add(log)

        # Add some INVALID anomalies
        log = AccessLog(
            pass_id=None,
            validator_id=controller.id,
            validation_time=datetime.utcnow(),
            status='INVALID'
        )
        db.session.add(log)

        db.session.commit()
        print("Seeding complete.")

if __name__ == '__main__':
    seed_reports_data()
