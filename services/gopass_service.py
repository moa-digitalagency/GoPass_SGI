from models import db, GoPass, Flight, User, AccessLog
from datetime import datetime
import json
import hashlib
import uuid
from services.qr_service import QRService

class GoPassService:
    @staticmethod
    def create_gopass(flight_id, passenger_name, passenger_passport, price=50.0, currency='USD', payment_ref=None, payment_method='Cash', sold_by=None, sales_channel='counter'):
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
            payment_method=payment_method,
            sold_by=sold_by,
            sales_channel=sales_channel,
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
        # Check if flight is closed
        target_flight = Flight.query.get(flight_id)
        if target_flight and target_flight.status == 'closed':
             return {
                'status': 'error',
                'code': 'FLIGHT_CLOSED',
                'message': 'VOL CLÔTURÉ',
                'color': 'red',
                'data': None
            }

        gopass = GoPass.query.filter_by(token=token).first()

        # Cas D: Invalide (Document non reconnu)
        if not gopass:
            # Log attempt even if invalid doc (if possible to track, but pass_id is null)
            # We might want to track who tried to scan it.
            # But AccessLog expects pass_id. If we want to log invalid docs, AccessLog might need to be nullable or use a dummy.
            # For now, let's assume we can't log "INVALID" easily in AccessLog if pass_id is FK.
            # Or we can create a record without pass_id if the model allows.
            # AccessLog.pass_id is nullable (default SQLAlchemy behavior unless nullable=False).
            # models/__init__.py: pass_id = db.Column(db.Integer, db.ForeignKey('gopasses.id'))
            # It is nullable by default.

            log = AccessLog(
                pass_id=None,
                validator_id=agent_id,
                validation_time=datetime.utcnow(),
                status='INVALID'
            )
            db.session.add(log)
            db.session.commit()

            return {
                'status': 'error',
                'code': 'INVALID',
                'message': 'DOCUMENT NON RECONNU',
                'color': 'red',
                'data': None
            }

        # Cas B: Déjà utilisé
        if gopass.status == 'consumed':
            log = AccessLog(
                pass_id=gopass.id,
                validator_id=agent_id,
                validation_time=datetime.utcnow(),
                status='ALREADY_SCANNED'
            )
            db.session.add(log)
            db.session.commit()

            original_scan = {
                'scan_date': gopass.scan_date.strftime('%Y-%m-%d %H:%M:%S') if gopass.scan_date else 'N/A',
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
            log = AccessLog(
                pass_id=gopass.id,
                validator_id=agent_id,
                validation_time=datetime.utcnow(),
                status='WRONG_FLIGHT'
            )
            db.session.add(log)
            db.session.commit()

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

            log = AccessLog(
                pass_id=gopass.id,
                validator_id=agent_id,
                validation_time=gopass.scan_date,
                status='VALID'
            )
            db.session.add(log)

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
