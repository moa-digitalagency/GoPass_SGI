
import pytest
from app import create_app, db
from services.mock_payment_service import MockPaymentService
import os

class TestMockPaymentService:
    def test_mock_rules(self):
        # Card Success
        res = MockPaymentService.process_payment('STRIPE', {'card_number': '4242 4242 4242 4242'})
        assert res['success'] is True
        assert res['transaction_id'].startswith('DEMO-TX-')

        # Card Fail
        res = MockPaymentService.process_payment('STRIPE', {'card_number': '4000 0000 0000 0000'})
        assert res['success'] is False
        assert res['message'] == "Fonds insuffisants"

        # Mobile Success
        res = MockPaymentService.process_payment('MOBILE_MONEY', {'mobile_number': '0990000000'})
        assert res['success'] is True
        assert res['transaction_id'].startswith('DEMO-MM-')

        # Mobile Fail
        res = MockPaymentService.process_payment('MOBILE_MONEY', {'mobile_number': '0999999999'})
        assert res['success'] is False
        assert res['message'] == "Délai dépassé (Timeout simulé)"

@pytest.fixture
def client():
    # Force Demo Payment
    os.environ['ENABLE_DEMO_PAYMENT'] = 'True'
    os.environ['SESSION_SECRET'] = 'test'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

    app = create_app('development')
    app.config['ENABLE_DEMO_PAYMENT'] = True # Explicitly set in config too
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing convenience

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

from models import Flight, PaymentGateway
from datetime import datetime

def test_checkout_demo_flow(client):
    # Setup Data
    flight = Flight(
        flight_number="TEST-001",
        departure_airport="FIH",
        arrival_airport="CDG",
        departure_time=datetime.now(),
        arrival_time=datetime.now(),
        airline="AF",
        capacity=100
    )
    db.session.add(flight)

    # Active Gateways needed for validation checks in route
    gw1 = PaymentGateway(provider='STRIPE', is_active=True)
    gw2 = PaymentGateway(provider='MOBILE_MONEY_AGGREGATOR', is_active=True)
    db.session.add(gw1)
    db.session.add(gw2)
    db.session.commit()

    # Test Card Success
    response = client.post(f'/checkout/{flight.id}', data={
        'payment_method': 'STRIPE',
        'passenger_name[]': ['Test Pax'],
        'passport[]': ['A123'],
        'document_type[]': ['Passeport'],
        'card_number': '4242 4242 4242 4242'
    }, follow_redirects=True)

    # Expect redirect to confirmation
    assert response.status_code == 200
    assert b"Confirmation" in response.data or "confirmation" in response.request.path

    # Test Card Failure
    response = client.post(f'/checkout/{flight.id}', data={
        'payment_method': 'STRIPE',
        'passenger_name[]': ['Test Pax'],
        'passport[]': ['A123'],
        'document_type[]': ['Passeport'],
        'card_number': '4000 0000 0000 0000'
    }, follow_redirects=True)

    # Expect failure flash message and staying on checkout page
    assert b"Fonds insuffisants" in response.data

    # Test Mobile Money Success
    response = client.post(f'/checkout/{flight.id}', data={
        'payment_method': 'MOBILE_MONEY',
        'passenger_name[]': ['Test Pax'],
        'passport[]': ['A123'],
        'document_type[]': ['Passeport'],
        'mobile_number': '0990000000'
    }, follow_redirects=True)

    # Expect redirect to confirmation
    assert response.status_code == 200
    assert b"Confirmation" in response.data or "confirmation" in response.request.path
