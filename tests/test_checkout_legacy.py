import pytest
from app import create_app, db
from models import Flight, GoPass, PaymentGateway
from datetime import datetime

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['AVIATIONSTACK_API_KEY'] = 'test'
    app.config['SESSION_SECRET'] = 'test'
    app.config['TELEGRAM_ENCRYPTION_KEY'] = 'test'
    app.config['ENABLE_DEMO_PAYMENT'] = True  # Enable demo payment to bypass external checks if any

    with app.app_context():
        db.create_all()

        # Create a Flight
        f = Flight(
            flight_number='CAA123',
            airline='CAA',
            departure_airport='FIH',
            arrival_airport='FBM',
            departure_time=datetime.now()
        )
        db.session.add(f)

        # Create Payment Gateway
        pg = PaymentGateway(provider='MOBILE_MONEY_AGGREGATOR', is_active=True)
        db.session.add(pg)

        db.session.commit()

        yield app

def test_checkout_route_legacy_pax(app):
    with app.app_context():
        flight = Flight.query.first()
        client = app.test_client()

        # Post data in legacy format (no brackets)
        data = {
            'passenger_name': 'Legacy User',
            'passport': 'LEGACY001',
            'document_type': 'Passeport',
            'payment_method': 'MOBILE_MONEY',
            'mobile_number': '0990000000'
        }

        response = client.post(f'/checkout/{flight.id}', data=data, follow_redirects=True)

        # Check success
        assert response.status_code == 200
        assert b'Legacy User' in response.data

        # Verify DB
        passes = GoPass.query.filter_by(passenger_name='Legacy User').all()
        assert len(passes) == 1
        assert passes[0].passenger_passport == 'LEGACY001'

def test_checkout_route_legacy_pax_missing_passport(app):
    with app.app_context():
        flight = Flight.query.first()
        client = app.test_client()

        # Post data in legacy format (missing passport)
        data = {
            'passenger_name': 'Incomplete User',
            # 'passport': 'MISSING',
            'document_type': 'Passeport',
            'payment_method': 'MOBILE_MONEY',
            'mobile_number': '0990000000'
        }

        response = client.post(f'/checkout/{flight.id}', data=data, follow_redirects=True)

        # Should verify what happens.
        # Code says: if name and passport: create_gopass
        # If passport is None, it won't create pass.
        # But if passenger_names list is not empty, it won't trigger "Veuillez ajouter au moins un passager".
        # It will likely redirect to confirmation but with 0 passes if code logic allows empty pass creation loop.
        # Let's check logic:
        # if not passenger_names: flash error
        # ...
        # for loop ... if name and passport: create_gopass
        # commit()
        # redirect confirmation

        # If 0 passes created, confirmation page might be empty or show error.

        passes = GoPass.query.filter_by(passenger_name='Incomplete User').all()
        assert len(passes) == 0
