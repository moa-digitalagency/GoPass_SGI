import unittest
import os
import io
from app import create_app, db
from models import GoPass, Flight, User, Transaction
from services.gopass_service import GoPassService
from datetime import datetime

class PdfGenerationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        # Ensure static folder and logos exist for test
        # In this environment, they are at repo root/statics
        self.app.static_folder = os.path.abspath('statics')

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Setup data
            flight = Flight(
                flight_number='AF123',
                departure_time=datetime.now(),
                departure_airport='FIH',
                arrival_airport='CDG',
                airline='Air France'
            )
            db.session.add(flight)
            db.session.commit()

            user = User(username='agent', email='agent@test.com', first_name='James', last_name='Bond', role='agent', location='FIH', phone='123456789')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            self.gopass = GoPass(
                token='testtoken',
                flight_id=flight.id,
                passenger_name='TEST PASSENGER',
                passenger_passport='A12345678',
                price=50.0,
                currency='USD',
                status='valid',
                sold_by=user.id,
                payment_ref='PAY-TEST',
                payment_method='CASH'
            )
            db.session.add(self.gopass)
            db.session.commit()
            self.gopass_id = self.gopass.id

    def test_generate_pdf_bytes_a4(self):
        with self.app.app_context():
            gopass = GoPass.query.get(self.gopass_id)
            pdf_bytes = GoPassService.generate_pdf_bytes(gopass, fmt='a4')
            self.assertTrue(pdf_bytes.startswith(b'%PDF'), "PDF bytes should start with %PDF")
            self.assertGreater(len(pdf_bytes), 1000, "PDF should be reasonably large")

    def test_generate_pdf_bytes_thermal(self):
        with self.app.app_context():
            gopass = GoPass.query.get(self.gopass_id)
            pdf_bytes = GoPassService.generate_pdf_bytes(gopass, fmt='thermal')
            self.assertTrue(pdf_bytes.startswith(b'%PDF'), "PDF bytes should start with %PDF")
            self.assertGreater(len(pdf_bytes), 1000, "PDF should be reasonably large")

    def test_generate_bulk_pdf(self):
        with self.app.app_context():
            gopass = GoPass.query.get(self.gopass_id)
            # Create a list of 5 gopasses
            gopass_list = [gopass] * 5
            pdf_bytes = GoPassService.generate_bulk_pdf(gopass_list)
            self.assertTrue(pdf_bytes.startswith(b'%PDF'), "PDF bytes should start with %PDF")
            self.assertGreater(len(pdf_bytes), 5000, "Bulk PDF should be larger")

if __name__ == '__main__':
    unittest.main()
