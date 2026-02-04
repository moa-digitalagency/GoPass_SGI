#!/usr/bin/env python3
"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for init_db.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

"""
Database Initialization Script for GO-PASS SGI-GP
This script creates all necessary tables and initializes default data.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from sqlalchemy import inspect, text

def check_and_update_schema(db, app):
    """
    Checks for existing tables and columns, and attempts to update schema if needed.
    """
    print("Checking database schema...")
    inspector = inspect(db.engine)

    # Define critical columns for each table based on models/__init__.py
    expected_schema = {
        'users': ['uuid', 'role', 'location', 'is_active', 'phone', 'first_name', 'last_name', 'email', 'username', 'password_hash', 'created_at', 'updated_at'],
        'flights': ['source', 'capacity', 'status', 'manifest_pax_count', 'aircraft_registration', 'flight_number', 'airline', 'departure_airport', 'arrival_airport', 'departure_time', 'arrival_time', 'created_at'],
        'gopasses': ['token', 'pass_number', 'payment_status', 'payment_ref', 'scan_date', 'scan_location', 'payment_method', 'sold_by', 'sales_channel', 'passenger_document_type', 'transaction_id', 'issue_date', 'flight_id', 'holder_id', 'pass_type_id', 'price', 'currency', 'passenger_name', 'passenger_passport', 'status', 'scanned_by'],
        'access_logs': ['status', 'validation_time', 'is_offline', 'validator_id', 'pass_id'],
        'pass_types': ['color', 'name'],
        'app_configs': ['value', 'description', 'updated_at'],
        'payment_gateways': ['is_active', 'config_json', 'provider'],
        'transactions': ['uuid', 'agent_id', 'amount_collected', 'currency', 'payment_method', 'provider_ref', 'status', 'is_offline_sync', 'created_at'],
        'cash_deposits': ['agent_id', 'supervisor_id', 'amount', 'deposit_date', 'notes'],
        'mobile_money_logs': ['transaction_ref', 'amount', 'currency', 'provider', 'status', 'timestamp', 'reconciled'],
        'offline_sync_logs': ['agent_id', 'sync_time', 'record_count', 'status', 'details'],
        'devices': ['unique_id', 'mac_address', 'device_type', 'last_ping', 'app_version', 'battery_level', 'is_sync'],
        'printers': ['name', 'location', 'status', 'assigned_to'],
        'security_keys': ['key_value', 'key_type', 'is_active', 'expires_at'],
        'airports': ['iata_code', 'city', 'type'],
        'airlines': ['name', 'logo_path', 'is_active'],
        'tariffs': ['flight_type', 'passenger_category', 'price', 'currency'],
        'flight_manifests': ['flight_id', 'passenger_count_declared', 'file_upload_path', 'upload_date']
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

                    col_type = 'VARCHAR(255)' # Default fallback

                    # Heuristic type mapping based on column names and common usage in this app
                    if col in ['is_active', 'is_offline', 'is_offline_sync', 'is_sync', 'reconciled']:
                        col_type = 'BOOLEAN DEFAULT FALSE' # Default false is safer for flags usually
                        if col == 'is_active': col_type = 'BOOLEAN DEFAULT TRUE'
                    elif col in ['capacity', 'manifest_pax_count', 'record_count', 'battery_level', 'agent_id', 'flight_id', 'pass_id', 'validator_id', 'supervisor_id', 'holder_id', 'pass_type_id', 'transaction_id', 'sold_by', 'assigned_to', 'passenger_count_declared', 'scanned_by']:
                        col_type = 'INTEGER'
                    elif col in ['scan_date', 'validation_time', 'updated_at', 'created_at', 'departure_time', 'arrival_time', 'last_ping', 'deposit_date', 'timestamp', 'sync_time', 'expires_at', 'issue_date', 'upload_date']:
                        col_type = 'TIMESTAMP'
                    elif col in ['price', 'amount', 'amount_collected']:
                        col_type = 'FLOAT DEFAULT 0.0'
                    elif col in ['config_json']:
                        col_type = 'JSON' # SQLite might treat this as TEXT, Postgres as JSON
                    elif col in ['value', 'key_value', 'notes', 'details']:
                        col_type = 'TEXT'

                    try:
                        with db.engine.connect() as conn:
                            # Adjust for SQLite vs Postgres if necessary, but standard SQL usually works for simple adds
                            # SQLite doesn't support adding columns with constraints easily in one go sometimes, but basic ADD COLUMN is supported.
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                            conn.commit()
                        print(f"Successfully added column '{col}' to '{table}'.")
                    except Exception as e:
                        print(f"Failed to add column '{col}' to '{table}': {e}")

    # Check for index on validation_time in access_logs
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
                    conn.execute(text("CREATE INDEX ix_access_logs_validation_time ON access_logs (validation_time)"))
                    conn.commit()
                print("Index created.")
            except Exception as e:
                print(f"Failed to create index: {e}")

    print("Schema check completed.")

def init_database():
    from app import create_app
    from models import db, User, Flight, GoPass, PassType, Device, Printer, SecurityKey, Airport, Airline, Tariff, AppConfig, PaymentGateway
    import uuid
    import secrets
    
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
                            passenger_document_type='Passeport',
                            pass_type_id=standard_type.id,
                            status='valid',
                            payment_status='paid',
                            price=50.0
                        )
                        db.session.add(pass_obj)
                print("Sample passes created.")

        # Seed Infrastructure Data
        print("Checking infrastructure data...")
        if Device.query.count() == 0:
            devices = [
                Device(unique_id='PDA-001', mac_address='00:1A:2B:3C:4D:5E', device_type='PDA', app_version='1.0.2', battery_level=85, last_ping=datetime.now(timezone.utc)),
                Device(unique_id='PDA-002', mac_address='00:1A:2B:3C:4D:5F', device_type='PDA', app_version='1.0.1', battery_level=12, last_ping=datetime.now(timezone.utc) - timedelta(hours=2)), # Offline
                Device(unique_id='TERM-001', mac_address='11:22:33:44:55:66', device_type='Terminal', app_version='2.1.0', battery_level=100, last_ping=datetime.now(timezone.utc), is_sync=False)
            ]
            db.session.add_all(devices)
            print("Sample devices created.")

        if Printer.query.count() == 0:
            printers = [
                Printer(name='Printer-Counter-1', location='Check-in Counter 1', status='connected'),
                Printer(name='Printer-Counter-2', location='Check-in Counter 2', status='paper_error'),
                Printer(name='Printer-Gate-A', location='Boarding Gate A', status='offline')
            ]
            db.session.add_all(printers)
            print("Sample printers created.")

        if SecurityKey.query.count() == 0:
            keys = [
                SecurityKey(key_value=secrets.token_hex(32), key_type='flight_bound', expires_at=datetime.now(timezone.utc) + timedelta(days=90)),
                SecurityKey(key_value=secrets.token_hex(32), key_type='flight_bound', is_active=False, expires_at=datetime.now(timezone.utc) - timedelta(days=10))
            ]
            db.session.add_all(keys)
            print("Sample security keys created.")

        # Seed Airports
        print("Checking airports...")
        if Airport.query.count() == 0:
            airports = [
                Airport(iata_code='FIH', city='Kinshasa', type='international'),
                Airport(iata_code='FBM', city='Lubumbashi', type='international'),
                Airport(iata_code='GOM', city='Goma', type='international'),
                Airport(iata_code='LUB', city='Lubumbashi (Luano)', type='national'),
                Airport(iata_code='FKI', city='Kisangani', type='national')
            ]
            db.session.add_all(airports)
            print("Sample airports created.")

        # Seed Airlines
        print("Checking airlines...")
        if Airline.query.count() == 0:
            airlines = [
                Airline(name='Compagnie Africaine d\'Aviation', is_active=True),
                Airline(name='Congo Airways', is_active=True),
                Airline(name='Air France', is_active=True),
                Airline(name='Brussels Airlines', is_active=True),
                Airline(name='Ethiopian Airlines', is_active=True)
            ]
            db.session.add_all(airlines)
            print("Sample airlines created.")

        # Seed Tariffs
        print("Checking tariffs...")
        if Tariff.query.count() == 0:
            tariffs = [
                Tariff(flight_type='national', passenger_category='Adulte', price=50.0),
                Tariff(flight_type='national', passenger_category='Enfant', price=25.0),
                Tariff(flight_type='national', passenger_category='Bébé', price=5.0),
                Tariff(flight_type='international', passenger_category='Adulte', price=55.0),
                Tariff(flight_type='international', passenger_category='Enfant', price=30.0),
                Tariff(flight_type='international', passenger_category='Bébé', price=10.0),
            ]
            db.session.add_all(tariffs)
            print("Sample tariffs created.")

        # Seed App Config
        print("Checking app config...")
        configs = [
            {"key": "logo_rva_url", "value": "/static/img/logo_rva.png", "description": "URL of the RVA logo"},
            {"key": "logo_gopass_url", "value": "/static/img/logo_gopass.png", "description": "URL of the GoPass logo (Platform)"},
            {"key": "logo_gopass_ticket_url", "value": "/static/img/logo_gopass.png", "description": "URL of the GoPass logo (Ticket/PDF)"},
            {"key": "site_name", "value": "SGI-GP RDC", "description": "Name of the application"},
            {"key": "idef_price_int", "value": "50", "description": "International IDEF Price"}
        ]

        for conf in configs:
            existing = db.session.get(AppConfig, conf['key'])
            if not existing:
                new_conf = AppConfig(key=conf['key'], value=conf['value'], description=conf['description'])
                db.session.add(new_conf)
                print(f"Added AppConfig: {conf['key']}")

        # Seed Payment Gateways
        print("Checking payment gateways...")
        gateways = [
            {"provider": "STRIPE", "is_active": True, "config_json": {}},
            {"provider": "MOBILE_MONEY_AGGREGATOR", "is_active": False, "config_json": {}}
        ]

        for gw in gateways:
            existing = PaymentGateway.query.filter_by(provider=gw['provider']).first()
            if not existing:
                new_gw = PaymentGateway(provider=gw['provider'], is_active=gw['is_active'], config_json=gw['config_json'])
                db.session.add(new_gw)
                print(f"Added PaymentGateway: {gw['provider']}")

        db.session.commit()
        print("\nDatabase initialization completed successfully!")

if __name__ == '__main__':
    init_database()
