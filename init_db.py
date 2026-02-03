#!/usr/bin/env python3
"""
Database Initialization Script for GO-PASS SGI-GP
This script creates all necessary tables and initializes default data.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import inspect, text

def check_and_update_schema(db, app):
    """
    Checks for existing tables and columns, and attempts to update schema if needed.
    """
    print("Checking database schema...")
    inspector = inspect(db.engine)

    # Define critical columns for each table that might have been added recently
    # This is a manual mapping based on models/__init__.py
    expected_schema = {
        'users': ['uuid', 'role', 'location', 'is_active', 'phone'],
        'flights': ['source', 'capacity', 'status'],
        'gopasses': ['token', 'pass_number', 'payment_status', 'scan_date', 'scan_location'],
        'access_logs': ['status', 'validation_time'],
        'pass_types': ['color']
    }

    # Only create tables if they don't exist
    db.create_all()

    existing_tables = inspector.get_table_names()

    for table, columns in expected_schema.items():
        if table in existing_tables:
            existing_columns = [col['name'] for col in inspector.get_columns(table)]
            for col in columns:
                if col not in existing_columns:
                    print(f"Missing column '{col}' in table '{table}'. Attempting to add...")
                    # Construct ALTER TABLE statement.
                    # Note: Type inference is tricky here without full introspection of models.
                    # We will use text types for simplicity or specific types if known criticals.
                    col_type = 'VARCHAR(255)'
                    if col in ['is_active']:
                        col_type = 'BOOLEAN DEFAULT TRUE'
                    elif col in ['capacity']:
                        col_type = 'INTEGER DEFAULT 0'
                    elif col in ['scan_date', 'validation_time']:
                        col_type = 'TIMESTAMP'
                    elif col in ['price']:
                        col_type = 'FLOAT'

                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                            conn.commit()
                        print(f"Successfully added column '{col}' to '{table}'.")
                    except Exception as e:
                        print(f"Failed to add column '{col}' to '{table}': {e}")
    # Check for index on validation_time
    if 'access_logs' in existing_tables:
        indexes = inspector.get_indexes('access_logs')
        has_index = False
        for idx in indexes:
            if 'validation_time' in idx['column_names']:
                has_index = True
                break

        if not has_index:
            print("Creating index on access_logs.validation_time...")
            try:
                with db.engine.connect() as conn:
                    # Generic SQL, should work for SQLite and Postgres
                    conn.execute(text("CREATE INDEX ix_access_logs_validation_time ON access_logs (validation_time)"))
                    conn.commit()
                print("Index created.")
            except Exception as e:
                print(f"Failed to create index: {e}")

    print("Schema check completed.")

def init_database():
    from app import create_app
    from models import db, User, Flight, GoPass, PassType
    import uuid
    
    app = create_app()
    
    with app.app_context():
        check_and_update_schema(db, app)
        
        # Create Default Users
        users_data = [
            {'username': 'admin', 'email': 'admin@gopass.local', 'role': 'admin', 'first': 'Administrateur', 'last': 'Système', 'pass': 'admin123', 'loc': None},
            {'username': 'agent', 'email': 'agent@gopass.local', 'role': 'agent', 'first': 'Agent', 'last': 'Percepteur', 'pass': 'agent123', 'loc': 'FIH'},
            {'username': 'controller', 'email': 'controller@gopass.local', 'role': 'controller', 'first': 'Agent', 'last': 'Contrôleur', 'pass': 'controller123', 'loc': 'FIH'},
            {'username': 'traveler1', 'email': 'traveler1@example.com', 'role': 'holder', 'first': 'Jean', 'last': 'Dupont', 'pass': 'traveler123', 'loc': None}
        ]

        for u in users_data:
            user = User.query.filter_by(username=u['username']).first()
            if not user:
                print(f"Creating default {u['role']} user ({u['username']})...")
                user = User(
                    username=u['username'],
                    email=u['email'],
                    first_name=u['first'],
                    last_name=u['last'],
                    role=u['role'],
                    location=u['loc'],
                    is_active=True
                )
                user.set_password(u['pass'])
                db.session.add(user)
            else:
                # Update critical fields if needed (idempotence)
                if not user.role:
                    user.role = u['role']
        
        db.session.commit() # Commit users first

        # Create Pass Types
        print("Checking pass types...")
        types = [
            PassType(name='Standard', color='#3B82F6'), # Blue
            PassType(name='VIP', color='#F59E0B'),      # Amber
            PassType(name='Diplomatique', color='#EF4444'), # Red
            PassType(name='Resident', color='#10B981')  # Green
        ]
        for t in types:
            existing = PassType.query.filter_by(name=t.name).first()
            if not existing:
                db.session.add(t)
                print(f"Added PassType: {t.name}")
        db.session.commit()

        # Create Sample Flight
        print("Checking sample flights...")
        flight_num = 'CAA-BU1421'
        flight = Flight.query.filter_by(flight_number=flight_num).first()
        if not flight:
            print(f"Creating sample flight {flight_num}...")
            flight = Flight(
                flight_number=flight_num,
                airline='Compagnie Africaine d\'Aviation',
                departure_airport='FIH',
                arrival_airport='FBM',
                departure_time=datetime.now() + timedelta(days=1),
                arrival_time=datetime.now() + timedelta(days=1, hours=2),
                status='scheduled',
                source='manual',
                capacity=150
            )
            db.session.add(flight)
            db.session.commit() # Commit to get ID

        # Create Sample Passes
        print("Checking sample passes...")
        if GoPass.query.count() == 0:
            holder = User.query.filter_by(role='holder').first()
            standard_type = PassType.query.filter_by(name='Standard').first()

            if flight and holder and standard_type:
                for i in range(5):
                    pass_num = f"GP{datetime.now().year}{str(i).zfill(6)}"
                    if not GoPass.query.filter_by(pass_number=pass_num).first():
                        pass_obj = GoPass(
                            token=f"TOKEN-{uuid.uuid4()}",
                            pass_number=pass_num,
                            flight_id=flight.id,
                            holder_id=holder.id,
                            passenger_name=f"{holder.first_name} {holder.last_name}",
                            passenger_passport=f"P{i}12345",
                            pass_type_id=standard_type.id,
                            status='valid',
                            payment_status='paid',
                            price=50.0
                        )
                        db.session.add(pass_obj)
                print("Sample passes created.")

        db.session.commit()
        print("\nDatabase initialization completed successfully!")

if __name__ == '__main__':
    init_database()
