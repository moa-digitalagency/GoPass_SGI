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
    from models import db, User, PassType
    
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")
        
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
                last_name='Test',
                role='agent',
                is_active=True
            )
            agent.set_password('agent123')
            db.session.add(agent)
            print("Agent user created (username: agent, password: agent123)")
        
        if PassType.query.count() == 0:
            print("Creating default pass types...")
            pass_types = [
                PassType(
                    name='Pass Standard',
                    description='Pass d\'accès standard valide pour 1 an',
                    validity_days=365,
                    color='#3B82F6',
                    is_active=True
                ),
                PassType(
                    name='Pass VIP',
                    description='Pass d\'accès VIP avec privilèges étendus',
                    validity_days=365,
                    color='#F59E0B',
                    is_active=True
                ),
                PassType(
                    name='Pass Temporaire',
                    description='Pass d\'accès temporaire valide pour 30 jours',
                    validity_days=30,
                    color='#10B981',
                    is_active=True
                ),
                PassType(
                    name='Pass Visiteur',
                    description='Pass d\'accès visiteur valide pour 1 jour',
                    validity_days=1,
                    color='#8B5CF6',
                    is_active=True
                )
            ]
            for pt in pass_types:
                db.session.add(pt)
            print(f"Created {len(pass_types)} pass types")
        
        db.session.commit()
        print("\nDatabase initialization completed successfully!")
        print("\nDefault credentials:")
        print("  Admin: username=admin, password=admin123")
        print("  Agent: username=agent, password=agent123")

if __name__ == '__main__':
    init_database()
