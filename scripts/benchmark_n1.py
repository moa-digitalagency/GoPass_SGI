
import os
import sys

# Add the current directory to sys.path so we can import app and models
sys.path.append(os.getcwd())

from sqlalchemy import event
from sqlalchemy.engine import Engine
from app import create_app
from models import db, GoPass, Flight, User, PassType
from sqlalchemy.orm import joinedload
import uuid
from datetime import datetime

def run_benchmark():
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True

    query_count = 0

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    with app.app_context():
        db.create_all()

        # Create a flight
        flight = Flight(
            flight_number='AF123',
            airline='Air France',
            departure_airport='CDG',
            arrival_airport='FIH',
            departure_time=datetime.now()
        )
        db.session.add(flight)

        # Create users
        holder = User(username='holder', email='holder@test.com', first_name='John', last_name='Doe')
        holder.set_password('password')
        db.session.add(holder)

        seller = User(username='seller', email='seller@test.com', first_name='Jane', last_name='Smith')
        seller.set_password('password')
        db.session.add(seller)

        # Create pass type
        pass_type = PassType(name='Standard', color='#000000')
        db.session.add(pass_type)

        db.session.commit()

        # Create 10 passes
        for i in range(10):
            p = GoPass(
                token=f'TOKEN-{i}',
                pass_number=f'GP-{i}',
                flight_id=flight.id,
                holder_id=holder.id,
                sold_by=seller.id,
                pass_type_id=pass_type.id,
                passenger_name='John Doe',
                passenger_passport='P12345'
            )
            db.session.add(p)
        db.session.commit()

        # Clear session to ensure we are actually fetching from DB
        db.session.expire_all()

        # --- Baseline ---
        query_count = 0
        query_str = 'TOKEN'
        passes = GoPass.query.options(joinedload(GoPass.flight)).filter(
            GoPass.token.ilike(f'%{query_str}%')
        ).limit(10).all()

        results = [p.to_dict() for p in passes]
        baseline_queries = query_count
        print(f"Number of queries with original code: {baseline_queries}")

        # Clear session again
        db.session.expire_all()

        # --- Optimized ---
        query_count = 0
        passes = GoPass.query.options(
            joinedload(GoPass.flight),
            joinedload(GoPass.holder),
            joinedload(GoPass.seller),
            joinedload(GoPass.pass_type)
        ).filter(
            GoPass.token.ilike(f'%{query_str}%')
        ).limit(10).all()

        results = [p.to_dict() for p in passes]
        optimized_queries = query_count
        print(f"Number of queries with optimized code: {optimized_queries}")

        if optimized_queries < baseline_queries:
            print(f"SUCCESS: Reduced queries from {baseline_queries} to {optimized_queries}")
        else:
            print(f"FAILURE: Did not reduce queries (baseline: {baseline_queries}, optimized: {optimized_queries})")

if __name__ == '__main__':
    run_benchmark()
