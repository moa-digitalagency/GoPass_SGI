import sys
import os
sys.path.append(os.getcwd())

import unittest
from unittest.mock import patch, MagicMock
from app import create_app
from models import db, Flight
from services import FlightService
from datetime import datetime

class TestFlightSync(unittest.TestCase):
    def setUp(self):
        # Set minimal env vars for create_app to avoid crash
        os.environ['SESSION_SECRET'] = 'test-secret'
        # We don't set AVIATIONSTACK_API_KEY in env here, so we verify config usage
        if 'AVIATIONSTACK_API_KEY' in os.environ:
            del os.environ['AVIATIONSTACK_API_KEY']

        # But we need DATABASE_URL
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Set key in config directly
        self.app.config['AVIATIONSTACK_API_KEY'] = 'mock-key'
        self.app.config['WTF_CSRF_ENABLED'] = False

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('services.flight_service.requests.get')
    def test_sync_flights(self, mock_get):
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'pagination': {'count': 1},
            'data': [
                {
                    'flight_date': '2023-10-27',
                    'flight_status': 'active',
                    'departure': {
                        'airport': 'Ndjili International',
                        'timezone': 'Africa/Kinshasa',
                        'iata': 'FIH',
                        'icao': 'FZAA',
                        'terminal': None,
                        'gate': None,
                        'delay': 13,
                        'scheduled': '2023-10-27T08:00:00+00:00',
                        'estimated': '2023-10-27T08:00:00+00:00',
                        'actual': None,
                        'estimated_runway': None,
                        'actual_runway': None
                    },
                    'arrival': {
                        'airport': 'Lubumbashi International',
                        'timezone': 'Africa/Lubumbashi',
                        'iata': 'FBM',
                        'icao': 'FZQA',
                        'terminal': None,
                        'gate': None,
                        'baggage': None,
                        'delay': None,
                        'scheduled': '2023-10-27T10:00:00+00:00',
                        'estimated': '2023-10-27T10:00:00+00:00',
                        'actual': None,
                        'estimated_runway': None,
                        'actual_runway': None
                    },
                    'airline': {
                        'name': 'Congo Airways',
                        'iata': '8Z',
                        'icao': 'CGA'
                    },
                    'flight': {
                        'number': '8Z100',
                        'iata': '8Z100',
                        'icao': 'CGA100',
                        'codeshared': None
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        # Run sync
        count = FlightService.sync_flights_from_api('FIH', date=datetime(2023, 10, 27))

        self.assertEqual(count, 1)

        # Verify DB
        flight = Flight.query.filter_by(flight_number='8Z100').first()
        self.assertIsNotNone(flight)

        # Now test Update logic
        # Change status in mock
        mock_response.json.return_value['data'][0]['flight_status'] = 'landed'
        # Change scheduled time slightly (same day)
        mock_response.json.return_value['data'][0]['departure']['scheduled'] = '2023-10-27T08:10:00+00:00'

        count = FlightService.sync_flights_from_api('FIH', date=datetime(2023, 10, 27))
        self.assertEqual(count, 1) # 1 updated

        flight = Flight.query.filter_by(flight_number='8Z100').first()
        self.assertEqual(flight.status, 'landed')
        self.assertEqual(flight.departure_time.minute, 10)

        # Verify no duplicate created
        self.assertEqual(Flight.query.count(), 1)

if __name__ == '__main__':
    unittest.main()
