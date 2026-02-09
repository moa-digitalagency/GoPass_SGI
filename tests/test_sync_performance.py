import unittest
from unittest.mock import patch, MagicMock
import time
import os
import threading
from app import create_app
from models import db, Airline
from services.external_data_sync import ExternalDataSync

class BenchmarkSync(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SESSION_SECRET'] = 'testing'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['AVIATIONSTACK_API_KEY'] = 'mock_key_for_test'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_sync_airlines_performance(self):
        # Mock the requests.get call to be slow
        with patch('requests.get') as mock_get:
            # Setup the mock response
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'data': [
                    {"airline_name": "Test Airline 1", "iata_code": "T1", "icao_code": "TST1", "country_name": "TestLand"},
                    {"airline_name": "Test Airline 2", "iata_code": "T2", "icao_code": "TST2", "country_name": "TestLand"}
                ]
            }

            # Simulate network delay
            def side_effect(*args, **kwargs):
                time.sleep(1.0) # Reduce to 1s to save test time, still enough to prove non-blocking
                return mock_response

            mock_get.side_effect = side_effect

            start_time = time.time()
            result = ExternalDataSync.sync_airlines()
            end_time = time.time()
            duration = end_time - start_time

            print(f"Sync call took {duration:.4f} seconds")

            # Assert non-blocking behavior
            self.assertLess(duration, 0.5, "Sync should be non-blocking and return immediately")
            self.assertEqual(result['status'], 'success')
            self.assertIn('background', result['message'])

            # Verify that data is NOT yet in DB (immediately)
            # Note: This is race-condition prone if the thread is super fast, but with 1s sleep it's safe.
            count_immediate = db.session.query(Airline).count()
            self.assertEqual(count_immediate, 0, "Data should not be in DB yet")

            # Wait for thread to complete
            print("Waiting for background task...")
            # We can't join the thread directly as we don't have a handle to it.
            # We just wait longer than the sleep time.
            time.sleep(1.5)

            # Verify data IS in DB now
            count_after = db.session.query(Airline).count()
            self.assertEqual(count_after, 2, "Data should be in DB after background task completes")

if __name__ == '__main__':
    unittest.main()
