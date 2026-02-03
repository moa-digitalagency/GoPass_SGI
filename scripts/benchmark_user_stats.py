"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for benchmark_user_stats.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import uuid
import random
from app import create_app
from models import db, User
from services.user_service import UserService

def setup_data(app_context):
    with app_context:
        db.create_all()
        print("Checking for existing users...")
        # Check if we have enough data
        count = User.query.count()
        target_count = 1000
        if count >= target_count:
            print(f"Data already exists ({count} users). Skipping population.")
            return

        print(f"Populating database with {target_count - count} Users...")

        roles = ['holder', 'agent', 'admin', 'controller']
        users = []
        for i in range(target_count - count):
            role = random.choice(roles)
            uid = uuid.uuid4()
            user = User(
                username=f"user_{uid}",
                email=f"user_{uid}@example.com",
                first_name=f"First {i}",
                last_name=f"Last {i}",
                role=role,
                is_active=random.choice([True, False])
            )
            user.set_password('password123')
            users.append(user)

        db.session.add_all(users)
        db.session.commit()
        print("Database populated.")

def run_benchmark():
    app = create_app()
    with app.app_context():
        setup_data(app.app_context())

        print("\nStarting benchmark...")
        # Warmup
        UserService.get_statistics()

        start_time = time.time()
        iterations = 100
        for _ in range(iterations):
            stats = UserService.get_statistics()
        end_time = time.time()

        avg_time = (end_time - start_time) / iterations
        print(f"Total time for {iterations} iterations: {end_time - start_time:.4f}s")
        print(f"Average time per call: {avg_time:.6f}s")
        print(f"Stats result: {stats}")

if __name__ == '__main__':
    run_benchmark()
