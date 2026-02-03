"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for verify_cache_invalidation.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uuid
from app import create_app
from models import db, User
from services.user_service import UserService

def verify_invalidation():
    app = create_app()
    with app.app_context():
        # 1. Initial Stats
        print("Getting initial stats...")
        initial_stats = UserService.get_statistics()
        print(f"Initial Total Users: {initial_stats['total_users']}")

        # 2. Add User
        print("Adding a new user...")
        uid = uuid.uuid4()
        new_user = UserService.create_user(
            username=f"test_user_{uid}",
            email=f"test_{uid}@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            role="holder"
        )
        print(f"User added: {new_user.username}")

        # 3. Check Stats again
        print("Getting stats after addition...")
        updated_stats = UserService.get_statistics()
        print(f"Updated Total Users: {updated_stats['total_users']}")

        if updated_stats['total_users'] == initial_stats['total_users'] + 1:
            print("SUCCESS: Cache invalidated and stats updated after user creation.")
        else:
            print("FAILURE: Stats did not update after user creation.")
            sys.exit(1)

        # 4. Delete User
        print("Deleting the user...")
        UserService.delete_user(new_user.id)

        # 5. Check Stats again
        print("Getting stats after deletion...")
        final_stats = UserService.get_statistics()
        print(f"Final Total Users: {final_stats['total_users']}")

        if final_stats['total_users'] == initial_stats['total_users']:
            print("SUCCESS: Cache invalidated and stats updated after user deletion.")
        else:
             print("FAILURE: Stats did not update after user deletion.")
             sys.exit(1)

if __name__ == '__main__':
    verify_invalidation()
