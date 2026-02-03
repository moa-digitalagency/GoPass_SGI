from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import User, Flight, GoPass, AccessLog
from services import FlightService, GoPassService, FinanceService
from security import agent_required, admin_required
from datetime import datetime
from sqlalchemy.orm import joinedload
import os

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
