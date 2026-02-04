"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for flight_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from models import db, Flight, FlightManifest
from datetime import datetime, timedelta
import requests
import os
from flask import current_app
from werkzeug.utils import secure_filename

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
    def get_or_create_manual_flight(flight_number, date, airport_code):
        # Normalize date to start of day for comparison
        # Ensure date is a date object or datetime object
        if isinstance(date, datetime):
            check_date = date.date()
        else:
            check_date = date

        start_of_day = datetime.combine(check_date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        flight = Flight.query.filter(
            Flight.flight_number == flight_number,
            Flight.departure_time >= start_of_day,
            Flight.departure_time < end_of_day
        ).first()

        if flight:
            return flight

        # If not found, create a manual flight
        # Default departure time to 12:00 if we only have a date
        dep_time = datetime.combine(check_date, datetime.min.time()).replace(hour=12)

        flight = Flight(
            flight_number=flight_number,
            airline="Unknown", # Manual entry
            departure_airport=airport_code,
            arrival_airport="UNK",
            departure_time=dep_time,
            arrival_time=dep_time + timedelta(hours=2), # Dummy duration
            status='scheduled',
            source='manual',
            capacity=0
        )
        db.session.add(flight)
        db.session.commit()
        return flight

    @staticmethod
    def create_manual_flight(flight_number, airline, dep_airport, arr_airport, dep_time, arr_time, capacity=0, aircraft_registration=None):
        flight = Flight(
            flight_number=flight_number,
            airline=airline,
            departure_airport=dep_airport,
            arrival_airport=arr_airport,
            departure_time=dep_time,
            arrival_time=arr_time,
            status='scheduled',
            source='manual',
            capacity=capacity,
            aircraft_registration=aircraft_registration
        )
        db.session.add(flight)
        db.session.commit()
        return flight

    @staticmethod
    def import_manifest(flight_id, file, upload_folder='statics/uploads/manifests'):
        flight = Flight.query.get(flight_id)
        if not flight:
            raise ValueError("Vol introuvable")

        filename = file.filename
        if not filename:
             raise ValueError("Fichier invalide")

        # Basic extension check
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in ['xlsx', 'pdf', 'xls']:
            raise ValueError("Format non supporté. Veuillez utiliser Excel (.xlsx) ou PDF.")

        # Ensure upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Save file
        safe_filename = secure_filename(filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        final_filename = f"{timestamp}_{safe_filename}"
        file_path = os.path.join(upload_folder, final_filename)

        # Reset file pointer if needed and save
        file.seek(0)
        file.save(file_path)

        count = 0

        if ext == 'xlsx':
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path)
                sheet = wb.active
                # Assuming header is row 1, we count rows from 2.
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    # Check if row is not empty (at least one cell has value)
                    if any(row):
                        count += 1
            except Exception as e:
                # If parsing fails, we still kept the file
                pass

        # Update Flight
        if count > 0:
            flight.manifest_pax_count = count

        # Create FlightManifest record
        manifest = FlightManifest(
            flight_id=flight.id,
            passenger_count_declared=count,
            file_upload_path=file_path,
            upload_date=datetime.utcnow()
        )
        db.session.add(manifest)
        db.session.commit()

        return count

    @staticmethod
    def update_status(flight_id, new_status):
        flight = Flight.query.get(flight_id)
        if not flight:
            raise ValueError("Vol introuvable")

        # Validate status
        valid_statuses = ['scheduled', 'active', 'landed', 'cancelled', 'open_for_sale', 'boarding', 'closed']
        # Map user friendly statuses if needed, but we will use the internal strings.
        # The prompt asked for: "Ouvert à la vente", "Embarquement", "Clôturé"
        # We can map these to internal codes or just use them.
        # Let's use internal codes: 'open', 'boarding', 'closed'.

        flight.status = new_status
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
