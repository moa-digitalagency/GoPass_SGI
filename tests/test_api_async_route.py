
import pytest
from unittest.mock import AsyncMock, patch
from app import create_app
from flask import Flask

@pytest.fixture
def app():
    # Make sure we use a config that doesn't need DB or anything
    # 'testing' config usually exists
    # We need to make sure we don't need database connection if possible
    # But create_app inits db.
    # We can mock init_app or use in-memory db.
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SESSION_SECRET'] = 'test'
    app = create_app('default')
    app.config['LOGIN_DISABLED'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['AVIATIONSTACK_API_KEY'] = 'test'

    with app.app_context():
        from models import db
        db.create_all()

    return app

import os

def test_verify_flight_route(app):
    client = app.test_client()

    mock_data = {
        'airline': 'Test Airline',
        'departure': {'iata': 'FIH', 'country_iso2': 'CD', 'time': '10:00'},
        'arrival': {'iata': 'CDG', 'country_iso2': 'FR'},
        'status': 'scheduled'
    }

    # patch verify_flight_with_api_async to be an AsyncMock
    with patch('services.flight_service.FlightService.verify_flight_with_api_async', new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = mock_data

        response = client.post('/api/external/verify-flight', json={
            'flight_number': 'AF123',
            'flight_date': '2023-10-27'
        })

        assert response.status_code == 200
        assert response.json['found'] == True
        assert response.json['flight_data']['airline'] == 'Test Airline'

    # Test not found
    with patch('services.flight_service.FlightService.verify_flight_with_api_async', new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = None

        response = client.post('/api/external/verify-flight', json={
            'flight_number': 'AF123',
            'flight_date': '2023-10-27'
        })

        assert response.status_code == 404
