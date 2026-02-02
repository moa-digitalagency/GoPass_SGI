from models import db, Flight
from datetime import datetime, timedelta
import random

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
    def sync_flights_from_api(airport_code='FIH'):
        """
        Mock implementation of AviationStack API sync.
        In a real scenario, this would call requests.get('http://api.aviationstack.com/v1/flights')
        """
        # Mock data generation
        mock_airlines = ['CAA', 'Congo Airways', 'Ethiopian Airlines', 'Air France', 'Brussels Airlines']
        mock_destinations = ['FBM', 'GOM', 'ADD', 'CDG', 'BRU', 'JNB']

        added_count = 0

        # Generate 5 mock flights for today/tomorrow
        now = datetime.now()
        for i in range(5):
            dest = random.choice(mock_destinations)
            airline = random.choice(mock_airlines)
            flight_num = f"{airline[:2].upper()}{random.randint(100, 999)}"

            dep_time = now + timedelta(hours=random.randint(1, 24))
            arr_time = dep_time + timedelta(hours=random.randint(1, 8))

            # Check if exists
            exists = Flight.query.filter_by(
                flight_number=flight_num,
                departure_time=dep_time
            ).first()

            if not exists:
                flight = Flight(
                    flight_number=flight_num,
                    airline=airline,
                    departure_airport=airport_code,
                    arrival_airport=dest,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    status='scheduled',
                    source='api',
                    capacity=180
                )
                db.session.add(flight)
                added_count += 1

        db.session.commit()
        return added_count
