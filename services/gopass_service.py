from models import db, GoPass, Flight, User
from datetime import datetime
import json
import hashlib
import uuid
from services.qr_service import QRService

class GoPassService:
    @staticmethod
    def create_gopass(flight_id, passenger_name, passenger_passport, price=50.0, currency='USD', payment_ref=None):
        flight = Flight.query.get(flight_id)
        if not flight:
            raise ValueError("Vol invalide")

        # Generate unique token
        token_data = {
            'flight_id': flight_id,
            'passport': passenger_passport,
            'timestamp': datetime.utcnow().isoformat(),
            'nonce': str(uuid.uuid4())
        }
        token_string = json.dumps(token_data, sort_keys=True)
        token_hash = hashlib.sha256(token_string.encode()).hexdigest()

        # In a real system, we would sign this with a private key.
        # For now, the hash acts as the secure token stored in DB.

        gopass = GoPass(
            token=token_hash,
            flight_id=flight_id,
            passenger_name=passenger_name,
            passenger_passport=passenger_passport,
            price=price,
            currency=currency,
            payment_status='paid', # Assuming payment success for now
            payment_ref=payment_ref or f"PAY-{uuid.uuid4().hex[:8].upper()}",
            status='valid'
        )

        db.session.add(gopass)
        db.session.commit()

        return gopass

    @staticmethod
    def get_gopass(gopass_id):
        return GoPass.query.get(gopass_id)

    @staticmethod
    def get_gopass_by_token(token):
        return GoPass.query.filter_by(token=token).first()

    @staticmethod
    def validate_gopass(token, flight_id, agent_id, location):
        """
        Logic for validation (Cas A, B, C, D)
        """
        gopass = GoPass.query.filter_by(token=token).first()

        # Cas D: Invalide (Document non reconnu)
        if not gopass:
            return {
                'status': 'error',
                'code': 'INVALID',
                'message': 'DOCUMENT NON RECONNU',
                'color': 'red',
                'data': None
            }

        # Cas B: Déjà utilisé
        if gopass.status == 'consumed':
            original_scan = {
                'scan_date': gopass.scan_date.strftime('%Y-%m-%d %H:%M:%S'),
                'scanned_by': gopass.scanner.username if gopass.scanner else 'Inconnu',
                'location': gopass.scan_location
            }
            return {
                'status': 'error',
                'code': 'ALREADY_SCANNED',
                'message': 'DÉJÀ SCANNÉ',
                'color': 'red',
                'data': {
                    'passenger': gopass.passenger_name,
                    'flight': gopass.flight.flight_number,
                    'original_scan': original_scan
                }
            }

        # Cas C: Mauvais Vol
        if str(gopass.flight_id) != str(flight_id):
            return {
                'status': 'warning',
                'code': 'WRONG_FLIGHT',
                'message': 'MAUVAIS VOL',
                'color': 'orange',
                'data': {
                    'valid_for': gopass.flight.flight_number,
                    'date': gopass.flight.departure_time.strftime('%Y-%m-%d')
                }
            }

        # Cas A: Succès
        if gopass.status == 'valid':
            # Mark as consumed
            gopass.status = 'consumed'
            gopass.scanned_by = agent_id
            gopass.scan_date = datetime.utcnow()
            gopass.scan_location = location
            db.session.commit()

            return {
                'status': 'success',
                'code': 'VALID',
                'message': 'VALIDE',
                'color': 'green',
                'data': {
                    'passenger': gopass.passenger_name,
                    'passport': gopass.passenger_passport
                }
            }

        return {
            'status': 'error',
            'code': 'UNKNOWN',
            'message': 'ERREUR INCONNUE',
            'color': 'red'
        }
