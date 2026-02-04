"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for api.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from models import User, Flight, GoPass, AccessLog, AppConfig, PaymentGateway, db
from services import FlightService, GoPassService, FinanceService
from security import agent_required, admin_required
from datetime import datetime
from sqlalchemy.orm import joinedload
import os
from werkzeug.utils import secure_filename
import stripe
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/me')
@login_required
def me():
    return jsonify(current_user.to_dict())

@api_bp.route('/airports')
@login_required
def get_airports():
    # In a real app, we might have an Airport model.
    # For now, we extract distinct airports from Flights or hardcode the RVA list.
    # Spec mentions: FIH, FBM, GOM
    airports = [
        {'code': 'FIH', 'name': "N'Djili International"},
        {'code': 'FBM', 'name': "Lubumbashi International"},
        {'code': 'GOM', 'name': "Goma International"},
        {'code': 'FKI', 'name': "Kisangani Bangoka"},
    ]
    return jsonify(airports)

@api_bp.route('/flights')
@login_required
def get_flights():
    airport_code = request.args.get('airport_code')
    date_str = request.args.get('date') # YYYY-MM-DD

    if not airport_code:
        return jsonify({'error': 'Airport code required'}), 400

    date = None
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            pass

    flights = FlightService.get_flights(airport_code=airport_code, date=date)
    return jsonify([f.to_dict() for f in flights])

@api_bp.route('/scan', methods=['POST'])
@login_required
def scan_pass():
    data = request.get_json()
    token = data.get('token')
    flight_id = data.get('flight_id')
    location = data.get('location') # Airport code
    
    if not token or not flight_id:
        return jsonify({'error': 'Token and Flight ID required'}), 400

    result = GoPassService.validate_gopass(
        token=token,
        flight_id=flight_id,
        agent_id=current_user.id,
        location=location or current_user.location
    )
    
    return jsonify(result)

@api_bp.route('/passes/search')
@login_required
def search_passes():
    query = request.args.get('q', '')
    passes = GoPass.query.options(joinedload(GoPass.flight)).filter(
        GoPass.token.ilike(f'%{query}%')
    ).limit(10).all()

    return jsonify([p.to_dict() for p in passes])

@api_bp.route('/validations/recent')
@login_required
def recent_validations():
    limit = request.args.get('limit', 10, type=int)
    validations = AccessLog.query.options(
        joinedload(AccessLog.pass_record).joinedload(GoPass.flight),
        joinedload(AccessLog.validator)
    ).order_by(
        AccessLog.validation_time.desc()
    ).limit(limit).all()

    return jsonify([v.to_dict() for v in validations])

@api_bp.route('/sales/cash-drop', methods=['POST'])
@login_required
def cash_drop():
    if current_user.role != 'admin':
         return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    agent_id = data.get('agent_id')
    amount = data.get('amount')
    notes = data.get('notes', '')

    if not agent_id or amount is None:
        return jsonify({'error': 'Agent ID and Amount required'}), 400

    try:
        deposit = FinanceService.record_deposit(
            agent_id=agent_id,
            supervisor_id=current_user.id,
            amount=float(amount),
            notes=notes
        )
        return jsonify({'message': 'Deposit recorded', 'id': deposit.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/flights/manual', methods=['POST'])
@login_required
def create_manual_flight():
    if current_user.role not in ['admin', 'agent']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    try:
        # Handle dep_time parsing from ISO format likely sent by JSON
        dep_time = datetime.fromisoformat(data.get('dep_time').replace('Z', '+00:00')) if data.get('dep_time') else None
        arr_time = datetime.fromisoformat(data.get('arr_time').replace('Z', '+00:00')) if data.get('arr_time') else None

        if not dep_time:
             return jsonify({'error': 'Departure time required'}), 400

        flight = FlightService.create_manual_flight(
            flight_number=data.get('flight_number'),
            airline=data.get('airline'),
            dep_airport=data.get('dep_airport'),
            arr_airport=data.get('arr_airport'),
            dep_time=dep_time,
            arr_time=arr_time,
            capacity=data.get('capacity', 0),
            aircraft_registration=data.get('aircraft_registration')
        )
        return jsonify(flight.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/manifest/upload', methods=['POST'])
@login_required
def upload_manifest():
    if current_user.role not in ['admin', 'agent']:
        return jsonify({'error': 'Unauthorized'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    flight_id = request.form.get('flight_id')

    if not flight_id:
         return jsonify({'error': 'Flight ID required'}), 400

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        count = FlightService.import_manifest(flight_id, file)
        return jsonify({'message': 'Manifest uploaded', 'passenger_count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/settings/upload-logo', methods=['POST'])
@login_required
def upload_logo():
    if current_user.role not in ['admin', 'tech']:
        return jsonify({'error': 'Unauthorized'}), 403

    if 'logo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['logo']
    key = request.form.get('key') # e.g., 'logo_rva_url' or 'logo_gopass_url'

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not key:
        return jsonify({'error': 'Key required'}), 400

    if file:
        filename = secure_filename(f"uploaded_{key}_{file.filename}")
        save_path = os.path.join(current_app.static_folder, 'img', filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)

        # Update AppConfig
        url_path = f"/static/img/{filename}" # Assuming static route maps there.

        config_entry = AppConfig.query.get(key)
        if not config_entry:
            config_entry = AppConfig(key=key)
            db.session.add(config_entry)

        config_entry.value = url_path
        config_entry.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Logo uploaded', 'url': url_path})

@api_bp.route('/settings/public')
def public_settings():
    # fetch logos
    rva = AppConfig.query.get('logo_rva_url')
    gopass = AppConfig.query.get('logo_gopass_url')
    gopass_ticket = AppConfig.query.get('logo_gopass_ticket_url')

    # fetch stripe status
    stripe_gw = PaymentGateway.query.filter_by(provider='STRIPE').first()
    stripe_enabled = stripe_gw.is_active if stripe_gw else False

    return jsonify({
        'rva_logo': rva.value if rva else None,
        'gopass_logo': gopass.value if gopass else None,
        'gopass_ticket_logo': gopass_ticket.value if gopass_ticket else None,
        'stripe_enabled': stripe_enabled
    })

@api_bp.route('/payment/toggle/<provider>', methods=['POST'])
@login_required
def toggle_payment_provider(provider):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    gateway = PaymentGateway.query.filter_by(provider=provider).first()
    if not gateway:
        return jsonify({'error': 'Provider not found'}), 404

    # Toggle
    gateway.is_active = not gateway.is_active
    db.session.commit()

    return jsonify({'message': f'{provider} is now {"active" if gateway.is_active else "inactive"}', 'is_active': gateway.is_active})

@api_bp.route('/payment/create-intent', methods=['POST'])
def create_payment_intent():
    # Check if Stripe is active
    stripe_gw = PaymentGateway.query.filter_by(provider='STRIPE').first()
    if not stripe_gw or not stripe_gw.is_active:
        return jsonify({'error': 'Service désactivé'}), 403

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not stripe.api_key:
         return jsonify({'error': 'Stripe configuration error'}), 500

    data = request.get_json()
    try:
        flight_id = data.get('flight_id')
        passenger_name = data.get('passenger_name')
        try:
            quantity = int(data.get('quantity', 1))
        except:
            quantity = 1

        # Calculate amount server-side
        # Default price 50 USD if not found
        price_conf = AppConfig.query.get('idef_price_int')
        price = float(price_conf.value) if price_conf else 50.0

        # Amount in cents
        amount = int(price * quantity * 100)
        currency = 'usd'

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata={
                'flight_id': flight_id,
                'passenger_name': passenger_name,
                'quantity': quantity,
                # storing passport in metadata if provided
                'passport': data.get('passport', 'UNKNOWN')
            }
        )
        return jsonify({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/payment/stripe-webhook', methods=['POST'])
def stripe_webhook():
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    event = None

    try:
        if not endpoint_secret:
            current_app.logger.error("STRIPE_WEBHOOK_SECRET is not set")
            return 'Configuration error', 500

        if not sig_header:
            return 'Missing signature', 400

        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        metadata = intent.get('metadata', {})

        flight_id = metadata.get('flight_id')
        passenger_name = metadata.get('passenger_name')
        try:
            quantity = int(metadata.get('quantity', 1))
        except:
            quantity = 1
        passport = metadata.get('passport', 'UNKNOWN')

        for i in range(quantity):
            gopass = GoPassService.create_gopass(
                flight_id=flight_id,
                passenger_name=passenger_name,
                passenger_passport=passport,
                payment_method='STRIPE',
                payment_ref=intent['id'],
                sales_channel='web'
            )

            # Generate PDF
            pdf_bytes = GoPassService.generate_pdf_bytes(gopass)

            # Send Email (Stub)
            print(f"STUB: Sending email to customer for Ticket {gopass.pass_number}")

    return jsonify(success=True)


@api_bp.route('/external/verify-flight', methods=['POST'])
@login_required
def verify_flight():
    data = request.get_json()
    flight_number = data.get('flight_number')
    flight_date = data.get('flight_date')

    if not flight_number or not flight_date:
        return jsonify({'error': 'Missing flight_number or flight_date'}), 400

    flight_data = FlightService.verify_flight_with_api(flight_number, flight_date)

    if not flight_data:
        # Returning 200 with found=False is easier for frontend than 404, but requirement says "Retourner 404".
        # But wait, step 1 description says: "Si aucun vol trouvé : Retourner 404."
        # Step 2 Frontend says: "Si le vol n'est pas trouvé ... afficher un message ... Permettre tout de même une Saisie Forcée".
        # So I will return 404.
        return jsonify({'found': False, 'message': 'Vol introuvable dans la base globale.'}), 404

    # Pricing Logic
    # Règle : Si Dep_Country == 'CD' ET Arr_Country == 'CD' => TARIF DOMESTIQUE (ex: 15$).
    # Sinon => TARIF INTERNATIONAL (ex: 55$).

    dep_country = flight_data['departure'].get('country_iso2')
    arr_country = flight_data['arrival'].get('country_iso2')

    price = 55.00
    pricing_type = "INTERNATIONAL"

    # Logic: Both must be CD for Domestic
    # We treat None as Non-CD (International) for revenue safety.
    if dep_country == 'CD' and arr_country == 'CD':
        price = 15.00
        pricing_type = "DOMESTIQUE"

    return jsonify({
        'found': True,
        'flight_data': flight_data,
        'pricing': {
            'type': pricing_type,
            'amount': price,
            'currency': 'USD'
        }
    })
