from models import db, Flight
from datetime import datetime, timedelta
import requests
import os
from flask import current_app

class FlightService:
    @staticmethod
    def get_flights(airport_code=None, date=None, status=None):
        query = Flight.query

        if airport_code:
            query = query.filter(Flight.departure_airport == airport_code)

        if date:
            # Filter by date (ignoring time)
            next_day = date + timedelta(days=1)
            query = query.filter(
                Flight.departure_time >= date,
                Flight.departure_time < next_day
            )

        if status:
            query = query.filter(Flight.status == status)

        return query.order_by(Flight.departure_time.asc()).all()

    @staticmethod
    def get_flight(flight_id):
        return Flight.query.get(flight_id)

    @staticmethod
    def create_manual_flight(flight_number, airline, dep_airport, arr_airport, dep_time, arr_time, capacity=0):
        flight = Flight(
            flight_number=flight_number,
            airline=airline,
            departure_airport=dep_airport,
            arrival_airport=arr_airport,
            departure_time=dep_time,
            arrival_time=arr_time,
            status='scheduled',
            source='manual',
            capacity=capacity
        )
        db.session.add(flight)
        db.session.commit()
        return flight

    @staticmethod
    def sync_flights_from_api(airport_code='FIH', date=None):
        """
        Sync flights from AviationStack API.
        """
        api_key = current_app.config.get('AVIATIONSTACK_API_KEY')
        if not api_key:
            raise Exception("AVIATIONSTACK_API_KEY not configured in application config")

        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': api_key,
            'dep_iata': airport_code,
            'limit': 100
        }

        if date:
            params['flight_date'] = date.strftime('%Y-%m-%d')

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API Request Failed: {str(e)}")

        if 'data' not in data:
            if 'error' in data:
                raise Exception(f"API Error: {data['error'].get('info', 'Unknown error')}")
            raise Exception("Invalid API Response: 'data' field missing")

        added_count = 0
        updated_count = 0

        for item in data['data']:
            if not item.get('flight') or not item.get('departure') or not item.get('arrival'):
                continue

            flight_number = item['flight'].get('iata') or item['flight'].get('number')
            if not flight_number:
                continue

            try:
                dep_time_str = item['departure'].get('scheduled')
                arr_time_str = item['arrival'].get('scheduled')

                if not dep_time_str:
                    continue

                dep_time = datetime.fromisoformat(dep_time_str)
                arr_time = None
                if arr_time_str:
                    arr_time = datetime.fromisoformat(arr_time_str)

                if dep_time.tzinfo is not None:
                    dep_time = dep_time.astimezone(None).replace(tzinfo=None)

                dep_time = dep_time.replace(tzinfo=None)
                if arr_time:
                    arr_time = arr_time.replace(tzinfo=None)

            except ValueError:
                continue

            airline = item['airline'].get('name', 'Unknown Airline')
            dep_airport = item['departure'].get('iata', airport_code)
            arr_airport = item['arrival'].get('iata', 'UNK')
            status = item.get('flight_status', 'scheduled')

            # Check if exists by flight number and DATE (ignoring time)
            start_of_day = dep_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            flight = Flight.query.filter(
                Flight.flight_number == flight_number,
                Flight.departure_time >= start_of_day,
                Flight.departure_time < end_of_day
            ).first()

            if flight:
                # Update status and times
                flight.status = status
                flight.departure_time = dep_time
                if arr_time:
                    flight.arrival_time = arr_time
                updated_count += 1
            else:
                flight = Flight(
                    flight_number=flight_number,
                    airline=airline,
                    departure_airport=dep_airport,
                    arrival_airport=arr_airport,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    status=status,
                    source='api',
                    capacity=150
                )
                db.session.add(flight)
                added_count += 1

        db.session.commit()
        return added_count + updated_count
