from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import User, Flight, GoPass, AccessLog
from services import FlightService, GoPassService
from security import agent_required
from datetime import datetime
from sqlalchemy.orm import joinedload

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
