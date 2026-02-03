"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for settings_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from models import db, Airport, Airline, Tariff
from sqlalchemy.exc import IntegrityError
import os
import time
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class SettingsService:
    @staticmethod
    def get_all_tariffs():
        return Tariff.query.order_by(Tariff.flight_type, Tariff.passenger_category).all()

    @staticmethod
    def update_tariff(tariff_id, price):
        tariff = db.session.get(Tariff, tariff_id)
        if tariff:
            tariff.price = float(price)
            db.session.commit()
            return tariff
        return None

    @staticmethod
    def get_all_airports():
        return Airport.query.order_by(Airport.city).all()

    @staticmethod
    def create_airport(data):
        try:
            airport = Airport(
                iata_code=data['iata_code'].upper(),
                city=data['city'],
                type=data['type']
            )
            db.session.add(airport)
            db.session.commit()
            return airport
        except IntegrityError:
            db.session.rollback()
            return None

    @staticmethod
    def update_airport(airport_id, data):
        airport = db.session.get(Airport, airport_id)
        if airport:
            airport.iata_code = data.get('iata_code', airport.iata_code).upper()
            airport.city = data.get('city', airport.city)
            airport.type = data.get('type', airport.type)
            try:
                db.session.commit()
                return airport
            except IntegrityError:
                db.session.rollback()
                return None
        return None

    @staticmethod
    def delete_airport(airport_id):
        airport = db.session.get(Airport, airport_id)
        if airport:
            db.session.delete(airport)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_all_airlines():
        return Airline.query.order_by(Airline.name).all()

    @staticmethod
    def create_airline(data, logo_file=None):
        try:
            logo_path = None
            if logo_file and logo_file.filename and allowed_file(logo_file.filename):
                filename = secure_filename(logo_file.filename)
                filename = f"{int(time.time())}_{filename}"
                upload_folder = os.path.join(current_app.root_path, 'statics', 'uploads', 'airlines')
                os.makedirs(upload_folder, exist_ok=True)
                logo_path = os.path.join('uploads', 'airlines', filename)
                full_path = os.path.join(current_app.root_path, 'statics', logo_path)
                logo_file.save(full_path)

            airline = Airline(
                name=data['name'],
                logo_path=logo_path,
                is_active=data.get('is_active', True)
            )
            db.session.add(airline)
            db.session.commit()
            return airline
        except IntegrityError:
            db.session.rollback()
            return None

    @staticmethod
    def update_airline(airline_id, data, logo_file=None):
        airline = db.session.get(Airline, airline_id)
        if airline:
            airline.name = data.get('name', airline.name)

            # Handle is_active. If it's passed as a boolean or 'on' string (from checkbox)
            if 'is_active' in data:
                val = data['is_active']
                if isinstance(val, str):
                    airline.is_active = (val.lower() == 'on' or val.lower() == 'true')
                else:
                    airline.is_active = bool(val)
            else:
                # If checkbox is unchecked, it might not be sent in form data at all.
                # So we need to know if we are updating from a form that excludes unchecked boxes.
                # Usually we handle this in the route by checking request.form.
                # Here we assume data contains the intended state, OR we handle it in route.
                # For safety, let's assume if it's not present, we don't change it, UNLESS the route explicitly sets it to False.
                pass

            if logo_file and logo_file.filename and allowed_file(logo_file.filename):
                filename = secure_filename(logo_file.filename)
                filename = f"{int(time.time())}_{filename}"
                upload_folder = os.path.join(current_app.root_path, 'statics', 'uploads', 'airlines')
                os.makedirs(upload_folder, exist_ok=True)
                logo_path = os.path.join('uploads', 'airlines', filename)
                full_path = os.path.join(current_app.root_path, 'statics', logo_path)
                logo_file.save(full_path)
                airline.logo_path = logo_path

            try:
                db.session.commit()
                return airline
            except IntegrityError:
                db.session.rollback()
                return None
        return None

    @staticmethod
    def delete_airline(airline_id):
        airline = db.session.get(Airline, airline_id)
        if airline:
            db.session.delete(airline)
            db.session.commit()
            return True
        return False
