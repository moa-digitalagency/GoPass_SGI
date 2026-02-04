import pytest
from unittest.mock import patch, MagicMock
from services.flight_service import FlightService
from services.gopass_service import GoPassService
from models import Transaction, Flight, User
from app import create_app, db
from datetime import datetime

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app

def test_verify_flight_service_mock(app):
    with app.app_context():
        with patch('services.flight_service.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'data': [{
                    'airline': {'name': 'Air France'},
                    'departure': {'iata': 'FIH', 'country_iso2': 'CD', 'scheduled': '2023-01-01T20:00:00+00:00'},
                    'arrival': {'iata': 'CDG', 'country_iso2': 'FR'},
                    'flight_status': 'scheduled'
                }]
            }
            mock_get.return_value = mock_response

            # Set API Key
            app.config['AVIATIONSTACK_API_KEY'] = 'test_key'

            result = FlightService.verify_flight_with_api('AF123', '2023-01-01')

            assert result is not None
            assert result['airline'] == 'Air France'
            assert result['departure']['country_iso2'] == 'CD'
            assert result['arrival']['country_iso2'] == 'FR'

def test_create_gopass_transaction(app):
    with app.app_context():
        # Setup Flight
        flight = Flight(flight_number='AF123', airline='AF', departure_airport='FIH', arrival_airport='CDG', departure_time=datetime.now())
        db.session.add(flight)

        # Setup Agent
        agent = User(username='agent', email='a@a.com', role='agent', first_name='A', last_name='B', password_hash='x')
        db.session.add(agent)
        db.session.commit()

        # Call create_gopass
        flight_details = {'airline': 'Air France', 'route': 'FIH-CDG'}
        gopass = GoPassService.create_gopass(
            flight_id=flight.id,
            passenger_name='John Doe',
            passenger_passport='A123',
            sold_by=agent.id,
            price=55.0,
            verification_source='api',
            flight_details=flight_details
        )

        assert gopass.id is not None
        assert gopass.transaction_id is not None

        txn = db.session.get(Transaction, gopass.transaction_id)
        assert txn.verification_source == 'api'
        assert txn.flight_details == flight_details
        assert txn.amount_collected == 55.0
