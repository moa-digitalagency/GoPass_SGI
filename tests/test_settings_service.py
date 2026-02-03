import unittest
import os
from app import create_app
from models import db, Airport, Airline, Tariff
from services.settings_service import SettingsService

class SettingsServiceTestCase(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SESSION_SECRET'] = 'testing'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_airport(self):
        data = {'iata_code': 'TST', 'city': 'Test City', 'type': 'national'}
        airport = SettingsService.create_airport(data)
        self.assertIsNotNone(airport)
        self.assertEqual(airport.iata_code, 'TST')

        # Test unique constraint
        airport2 = SettingsService.create_airport(data)
        self.assertIsNone(airport2)

    def test_tariffs(self):
        # Create a tariff
        t = Tariff(flight_type='national', passenger_category='Adulte', price=50.0)
        db.session.add(t)
        db.session.commit()

        updated = SettingsService.update_tariff(t.id, 60.0)
        self.assertEqual(updated.price, 60.0)

    def test_airlines(self):
        data = {'name': 'Test Air', 'is_active': True}
        airline = SettingsService.create_airline(data)
        self.assertIsNotNone(airline)
        self.assertEqual(airline.name, 'Test Air')

if __name__ == '__main__':
    unittest.main()
