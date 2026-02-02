import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uuid
import random
from datetime import datetime, timedelta
from app import create_app
from models import db, GoPass, Flight, PassType, User

def seed_data():
    app = create_app()
    with app.app_context():
        print("Seeding performance data...")

        # Create PassTypes
        pass_types_data = [
            {'name': 'Standard', 'color': '#3B82F6', 'price': 50.0},
            {'name': 'VIP', 'color': '#8B5CF6', 'price': 150.0},
            {'name': 'Business', 'color': '#10B981', 'price': 100.0},
            {'name': 'Crew', 'color': '#F59E0B', 'price': 0.0},
            {'name': 'Diplomat', 'color': '#EF4444', 'price': 0.0}
        ]

        pass_types = []
        for pt_data in pass_types_data:
            pt = PassType.query.filter_by(name=pt_data['name']).first()
            if not pt:
                pt = PassType(
                    name=pt_data['name'],
                    color=pt_data['color'],
                    price=pt_data['price'],
                    is_active=True
                )
                db.session.add(pt)
                print(f"Created PassType: {pt.name}")
            pass_types.append(pt)
        db.session.commit()

        # Create Holder User
        holder = User.query.filter_by(username='holder_perf').first()
        if not holder:
            holder = User(
                username='holder_perf',
                email='holder_perf@example.com',
                first_name='John',
                last_name='Doe',
                role='holder',
                is_active=True
            )
            holder.set_password('password')
            db.session.add(holder)
            db.session.commit()
            print("Created Holder User")

        # Create Flight
        flight = Flight.query.filter_by(flight_number='PERF-001').first()
        if not flight:
            flight = Flight(
                flight_number='PERF-001',
                airline='Performance Air',
                departure_airport='FIH',
                arrival_airport='FBM',
                departure_time=datetime.now() + timedelta(days=5),
                status='scheduled',
                capacity=5000
            )
            db.session.add(flight)
            db.session.commit()
            print("Created Performance Flight")

        # Create GoPasses
        current_count = GoPass.query.filter(GoPass.token.like('PERF-%')).count()
        target_count = 2000

        if current_count < target_count:
            passes_to_create = target_count - current_count
            print(f"Creating {passes_to_create} GoPasses...")

            new_passes = []
            for i in range(passes_to_create):
                pt = random.choice(pass_types)
                # Ensure we have active status for the test logic mostly
                # logic uses status='valid' (or 'active' in task description, assuming valid)
                status = 'valid'

                gopass = GoPass(
                    token=f"PERF-{uuid.uuid4()}",
                    flight_id=flight.id,
                    type_id=pt.id,
                    holder_id=holder.id,
                    passenger_name=f"Passenger {i}",
                    passenger_passport=f"P-{i}",
                    status=status,
                    payment_status='paid'
                )
                new_passes.append(gopass)

                if len(new_passes) >= 500:
                    db.session.bulk_save_objects(new_passes)
                    db.session.commit()
                    new_passes = []
                    print(f"Saved batch...")

            if new_passes:
                db.session.bulk_save_objects(new_passes)
                db.session.commit()

            print("Finished seeding GoPasses.")
        else:
            print("Data already seeded.")

if __name__ == '__main__':
    seed_data()
