
import unittest
from app import create_app
from models import db, Flight, GoPass, User, AccessLog
from services.gopass_service import GoPassService
from datetime import datetime, timedelta
import json

class TestScannerLogic(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_name='default')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create Agent
        self.agent = User(
            username='agent', email='agent@test.com', role='agent',
            first_name='Agent', last_name='007'
        )
        self.agent.set_password('password')
        db.session.add(self.agent)
        db.session.commit()

        # Create Flights
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        # Flight A: Today, Target Flight
        self.flight_a = Flight(
            flight_number='FL-A', airline='TestAir', departure_airport='FIH', arrival_airport='FBM',
            departure_time=today, status='scheduled'
        )
        # Flight B: Today, Different Flight
        self.flight_b = Flight(
            flight_number='FL-B', airline='TestAir', departure_airport='FIH', arrival_airport='GOM',
            departure_time=today, status='scheduled'
        )
        # Flight C: Tomorrow, Different Date
        self.flight_c = Flight(
            flight_number='FL-C', airline='TestAir', departure_airport='FIH', arrival_airport='FBM',
            departure_time=tomorrow, status='scheduled'
        )

        db.session.add_all([self.flight_a, self.flight_b, self.flight_c])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def create_pass(self, flight):
        return GoPassService.create_gopass(
            flight_id=flight.id,
            passenger_name='John Doe',
            passenger_passport='A1234567',
            sold_by=self.agent.id
        )

    def test_valid_scan(self):
        # Case A: Success
        gp = self.create_pass(self.flight_a)

        result = GoPassService.validate_gopass(
            token=gp.token,
            flight_id=self.flight_a.id,
            agent_id=self.agent.id,
            location='FIH'
        )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['code'], 'VALID')
        self.assertEqual(result['color'], 'green')

        # Check DB status
        gp_db = GoPass.query.get(gp.id)
        self.assertEqual(gp_db.status, 'consumed')
        self.assertEqual(gp_db.scanned_by, self.agent.id)

    def test_already_scanned(self):
        # Case B: Already Scanned
        gp = self.create_pass(self.flight_a)

        # First scan
        GoPassService.validate_gopass(gp.token, self.flight_a.id, self.agent.id, 'FIH')

        # Second scan
        result = GoPassService.validate_gopass(
            token=gp.token,
            flight_id=self.flight_a.id,
            agent_id=self.agent.id,
            location='FIH'
        )

        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['code'], 'ALREADY_SCANNED')
        self.assertEqual(result['color'], 'red')
        self.assertIn('original_scan', result['data'])

    def test_wrong_flight_same_day(self):
        # Case C: Wrong Flight (Orange)
        gp = self.create_pass(self.flight_b) # Ticket for Flight B

        # Scanning for Flight A
        result = GoPassService.validate_gopass(
            token=gp.token,
            flight_id=self.flight_a.id,
            agent_id=self.agent.id,
            location='FIH'
        )

        self.assertEqual(result['status'], 'warning')
        self.assertEqual(result['code'], 'WRONG_FLIGHT')
        self.assertEqual(result['color'], 'orange')
        self.assertIn('valid_for', result['data'])
        self.assertEqual(result['data']['valid_for'], 'FL-B')

    def test_wrong_date_expired(self):
        # Case: Wrong Date (Red) - Requirement: "Si Date différente : ALERTE ROUGE (Billet Expiré)"
        gp = self.create_pass(self.flight_c) # Ticket for Tomorrow (or could be yesterday, testing difference)

        # Scanning for Flight A (Today)
        result = GoPassService.validate_gopass(
            token=gp.token,
            flight_id=self.flight_a.id,
            agent_id=self.agent.id,
            location='FIH'
        )

        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['code'], 'EXPIRED')
        self.assertEqual(result['color'], 'red')
        self.assertIn('valid_for_date', result['data'])

if __name__ == '__main__':
    unittest.main()
