#!/usr/bin/env python3
"""
Database Initialization Script for GO-PASS SGI-GP
This script creates all necessary tables and initializes default data.
"""

import os
import sys
from datetime import datetime, timedelta

def init_database():
    from app import create_app
    from models import db, User, Flight, GoPass
    
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")
        
        # Create Default Users
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating default admin user...")
            admin = User(
                username='admin',
                email='admin@gopass.local',
                first_name='Administrateur',
                last_name='Système',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Admin user created (username: admin, password: admin123)")
        
        agent = User.query.filter_by(username='agent').first()
        if not agent:
            print("Creating default agent user...")
            agent = User(
                username='agent',
                email='agent@gopass.local',
                first_name='Agent',
                last_name='Percepteur',
                role='agent',
                location='FIH',
                is_active=True
            )
            agent.set_password('agent123')
            db.session.add(agent)
            print("Agent user created (username: agent, password: agent123)")

        controller = User.query.filter_by(username='controller').first()
        if not controller:
            print("Creating default controller user...")
            controller = User(
                username='controller',
                email='controller@gopass.local',
                first_name='Agent',
                last_name='Contrôleur',
                role='controller',
                location='FIH',
                is_active=True
            )
            controller.set_password('controller123')
            db.session.add(controller)
            print("Controller user created (username: controller, password: controller123)")
        
        # Create Sample Flight
        if Flight.query.count() == 0:
            print("Creating sample flights...")
            flight = Flight(
                flight_number='CAA-BU1421',
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
            print("Sample flight created: CAA-BU1421")

        db.session.commit()
        print("\nDatabase initialization completed successfully!")

if __name__ == '__main__':
    init_database()
