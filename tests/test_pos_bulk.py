import unittest
from app import create_app, db
from models import User, Flight
from datetime import datetime
import json

class PosBulkTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Create Agent
            user = User(username='agent', email='agent@test.com', role='agent', first_name='Bond', last_name='James', location='FIH')
            user.set_password('password')
            db.session.add(user)

            # Create Flight
            flight = Flight(
                flight_number='AF123',
                airline='Air France',
                departure_airport='FIH',
                arrival_airport='CDG',
                departure_time=datetime.now(),
                status='scheduled'
            )
            db.session.add(flight)
            db.session.commit()

            self.flight_id = flight.id

    def login(self):
        return self.client.post('/login', data=dict(
            username='agent',
            password='password'
        ), follow_redirects=True)

    def test_bulk_sale(self):
        with self.client:
            self.login()

            # Payload
            payload = {
                'flight_mode': 'today',
                'flight_id': self.flight_id,
                'price': 50.0,
                'passengers': [
                    {'name': 'Passenger 1', 'doc_num': 'A100', 'doc_type': 'Passport'},
                    {'name': 'Passenger 2', 'doc_num': 'B200', 'doc_type': 'ID Card'}
                ]
            }

            response = self.client.post('/ops/pos/sale',
                                      data=json.dumps(payload),
                                      content_type='application/json')

            print("Response Status:", response.status_code)
            print("Response Data:", response.data.decode())

            self.assertEqual(response.status_code, 200)
            data = response.get_json()

            self.assertTrue(data['success'])
            self.assertEqual(len(data['tickets']), 2)
            self.assertEqual(data['total_price'], 100.0)
            self.assertEqual(data['tickets'][0]['passenger_name'], 'Passenger 1')
            self.assertEqual(data['tickets'][1]['passenger_name'], 'Passenger 2')

if __name__ == '__main__':
    unittest.main()
