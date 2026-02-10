import requests
import threading
from flask import current_app
from models import db, Airport, Airline

class ExternalDataSync:
    BASE_URL = "http://api.aviationstack.com/v1"

    @staticmethod
    def _get_api_key():
        return current_app.config.get('AVIATIONSTACK_API_KEY')

    @classmethod
    def sync_airports(cls):
        api_key = cls._get_api_key()
        if not api_key or api_key == 'mock_key':
            return cls._mock_sync_airports()

        app = current_app._get_current_object()
        thread = threading.Thread(target=cls._perform_sync_airports, args=(app, api_key))
        thread.start()

        return {"status": "success", "message": "Synchronization started in background"}

    @classmethod
    def _perform_sync_airports(cls, app, api_key):
        with app.app_context():
            # Fetch active airports
            params = {
                'access_key': api_key,
                'limit': 100  # Default limit
            }

            try:
                response = requests.get(f"{cls.BASE_URL}/airports", params=params)
                response.raise_for_status()
                data = response.json()

                if 'data' not in data:
                    print("Error syncing airports: Invalid API response structure")
                    return

                count = 0
                for item in data['data']:
                    iata = item.get('iata_code')
                    if not iata:
                        continue

                    # Check if exists
                    airport = db.session.query(Airport).filter_by(iata_code=iata).first()
                    if not airport:
                        airport = Airport(iata_code=iata, city=item.get('airport_name', 'Unknown')) # Fallback
                        db.session.add(airport)

                    airport.name = item.get('airport_name')
                    airport.country = item.get('country_name')
                    # Aviationstack doesn't always provide city clearly in free tier or standard response, sometimes it is same as airport name
                    # We update city if valid
                    if item.get('city_iata_code'): # Usually just a code, but maybe helpful?
                        pass

                    # Update type logic (heuristic)
                    if airport.country and airport.country.lower() != 'congo': # Assuming 'congo' refers to local context if needed, but 'national' vs 'international' is complex.
                        airport.type = 'international'

                    count += 1

                db.session.commit()
                print(f"Synced {count} airports from API")

            except Exception as e:
                print(f"Error syncing airports: {e}")

    @classmethod
    def sync_airlines(cls):
        api_key = cls._get_api_key()
        if not api_key or api_key == 'mock_key':
            return cls._mock_sync_airlines()

        app = current_app._get_current_object()
        thread = threading.Thread(target=cls._perform_sync_airlines, args=(app, api_key))
        thread.start()

        return {"status": "success", "message": "Synchronization started in background"}

    @classmethod
    def _perform_sync_airlines(cls, app, api_key):
        with app.app_context():
            params = {
                'access_key': api_key,
                'limit': 100,
                'airline_status': 'active'
            }

            try:
                response = requests.get(f"{cls.BASE_URL}/airlines", params=params)
                response.raise_for_status()
                data = response.json()

                if 'data' not in data:
                    print("Error syncing airlines: Invalid API response structure")
                    return

                count = 0
                for item in data['data']:
                    name = item.get('airline_name')
                    if not name:
                        continue

                    airline = db.session.query(Airline).filter_by(name=name).first()
                    if not airline:
                        airline = Airline(name=name)
                        db.session.add(airline)

                    airline.iata_code = item.get('iata_code')
                    airline.icao_code = item.get('icao_code')
                    airline.country = item.get('country_name')

                    count += 1

                db.session.commit()
                print(f"Synced {count} airlines from API")

            except Exception as e:
                print(f"Error syncing airlines: {e}")

    @classmethod
    def _mock_sync_airports(cls):
        # Mock data for demonstration
        mock_data = [
            {"iata_code": "CDG", "name": "Charles de Gaulle", "city": "Paris", "country": "France", "type": "international"},
            {"iata_code": "JFK", "name": "John F Kennedy", "city": "New York", "country": "USA", "type": "international"},
            {"iata_code": "DXB", "name": "Dubai International", "city": "Dubai", "country": "UAE", "type": "international"},
            {"iata_code": "LHR", "name": "Heathrow", "city": "London", "country": "United Kingdom", "type": "international"},
            {"iata_code": "FIH", "name": "N'Djili International", "city": "Kinshasa", "country": "Congo (Kinshasa)", "type": "international"}
        ]

        count = 0
        for item in mock_data:
            airport = db.session.query(Airport).filter_by(iata_code=item['iata_code']).first()
            if not airport:
                airport = Airport(iata_code=item['iata_code'], city=item['city'])
                db.session.add(airport)

            airport.name = item['name']
            airport.city = item['city']
            airport.country = item['country']
            airport.type = item['type']
            count += 1

        db.session.commit()
        return {"status": "success", "count": count, "message": "Synced with Mock Data (No API Key provided)"}

    @classmethod
    def _mock_sync_airlines(cls):
        mock_data = [
            {"name": "Emirates", "iata": "EK", "icao": "UAE", "country": "UAE"},
            {"name": "Delta Air Lines", "iata": "DL", "icao": "DAL", "country": "USA"},
            {"name": "Lufthansa", "iata": "LH", "icao": "DLH", "country": "Germany"},
            {"name": "Turkish Airlines", "iata": "TK", "icao": "THY", "country": "Turkey"},
            {"name": "Compagnie Africaine d'Aviation", "iata": "BU", "icao": "FPY", "country": "Congo (Kinshasa)"}
        ]

        count = 0
        for item in mock_data:
            airline = db.session.query(Airline).filter_by(name=item['name']).first()
            if not airline:
                airline = Airline(name=item['name'])
                db.session.add(airline)

            airline.iata_code = item['iata']
            airline.icao_code = item['icao']
            airline.country = item['country']
            count += 1

        db.session.commit()
        return {"status": "success", "count": count, "message": "Synced with Mock Data (No API Key provided)"}
