"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for verify_dashboard.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""


import sys
import os
import unittest
from flask import Flask
from flask_login import login_user, LoginManager

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Ensure db exists (we use the local sqlite for now)
        # db.create_all() # Assuming it's already created by init_db.py

    def tearDown(self):
        self.app_context.pop()

    def test_dashboard_access(self):
        # Log in as admin
        with self.client:
            # We need to simulate login.
            # Or use the login route.
            response = self.client.post('/login', data=dict(
                username='admin',
                password='admin123'
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Access dashboard
            response = self.client.get('/dashboard/')
            self.assertEqual(response.status_code, 200)
            print("Dashboard accessed successfully (status code 200).")

            # Check for content related to daily validations if possible
            # Since daily_validations is rendered in template (probably passed as JSON or list)
            # We can check if the response contains 'daily_validations' or similar if it's in JS.
            # But the template might just render nothing if the list is empty.
            # I'll check the template content later if needed.

if __name__ == '__main__':
    unittest.main()
