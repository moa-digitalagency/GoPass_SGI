import pytest
from app import create_app, db
from models import Flight, GoPass, PaymentGateway
from services.gopass_service import GoPassService
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

    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create a Flight
        f = Flight(
            flight_number='CAA123',
            airline='CAA',
            departure_airport='FIH',
            arrival_airport='FBM',
            departure_time=datetime.utcnow()
        )
        db.session.add(f)

        # Create Payment Gateway
        pg = PaymentGateway(provider='MOBILE_MONEY_AGGREGATOR', is_active=True)
        db.session.add(pg)

        db.session.commit()

        yield app

def test_create_gopass_multi_service(app):
    with app.app_context():
        flight = Flight.query.first()

        # Manually emulate the loop in route
        import uuid
        ref = f"WEB-{uuid.uuid4().hex}"

        gp1 = GoPassService.create_gopass(flight.id, "Pax 1", "P1", payment_ref=ref, commit=False)
        gp2 = GoPassService.create_gopass(flight.id, "Pax 2", "P2", payment_ref=ref, commit=False)

        db.session.commit()

        passes = GoPass.query.filter_by(payment_ref=ref).all()
        assert len(passes) == 2
        assert passes[0].passenger_name == "Pax 1"
        assert passes[1].passenger_name == "Pax 2"

def test_checkout_route_multi_pax(app):
    with app.app_context():
        flight = Flight.query.first()
        client = app.test_client()

        # Post data
        data = {
            'passenger_name[]': ['Alice', 'Bob'],
            'passport[]': ['A001', 'B002'],
            'document_type[]': ['Passeport', 'Passeport'],
            'payment_method': 'MOBILE_MONEY'
        }

        response = client.post(f'/checkout/{flight.id}', data=data, follow_redirects=True)
        assert response.status_code == 200

        # Check if passes created
        # In a real test we would check DB, but here we can check response content if it shows names
        assert b'Alice' in response.data
        assert b'Bob' in response.data

        # Verify DB
        passes = GoPass.query.all()
        assert len(passes) == 2
