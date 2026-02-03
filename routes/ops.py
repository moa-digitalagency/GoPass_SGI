from flask import Blueprint, render_template, request, jsonify, url_for, flash
from flask_login import login_required, current_user
from services.flight_service import FlightService
from services.gopass_service import GoPassService
from models import db, GoPass
from sqlalchemy import func
from security import role_required, agent_required
from datetime import datetime

ops_bp = Blueprint('ops', __name__, url_prefix='/ops')

@ops_bp.route('/pos')
@agent_required
def pos():
    # Get today's flights for the current user's location (if set) or all (if admin/no location)
    # Assuming user.location is airport code like 'FIH'
    airport_code = current_user.location
    today = datetime.now().date()

    flights = FlightService.get_flights(airport_code=airport_code, date=today)

    total_sales = db.session.query(func.sum(GoPass.price)).filter(
        GoPass.sold_by == current_user.id,
        func.date(GoPass.issue_date) == today
    ).scalar() or 0.0

    return render_template('ops/pos.html', flights=flights, today=today, total_sales=total_sales)

@ops_bp.route('/pos/sale', methods=['POST'])
@agent_required
def pos_sale():
    data = request.get_json()
    flight_id = data.get('flight_id')
    passenger_name = data.get('passenger_name')
    passenger_passport = data.get('passenger_passport')
    passenger_document_type = data.get('passenger_document_type', 'Passeport')

    if not flight_id or not passenger_name or not passenger_passport:
        return jsonify({'error': 'Données manquantes'}), 400

    try:
        gopass = GoPassService.create_gopass(
            flight_id=flight_id,
            passenger_name=passenger_name,
            passenger_passport=passenger_passport,
            passenger_document_type=passenger_document_type,
            payment_method='Cash',
            sold_by=current_user.id,
            sales_channel='pos'
        )

        return jsonify({
            'success': True,
            'gopass_id': gopass.id,
            'pdf_url': url_for('public.download_pdf', id=gopass.id, format='thermal'),
            'price': gopass.price
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ops_bp.route('/scanner')
@role_required('admin', 'controller')
def scanner():
    # Similar to POS, get today's flights for selection
    airport_code = current_user.location
    today = datetime.now().date()

    flights = FlightService.get_flights(airport_code=airport_code, date=today)

    return render_template('ops/scanner.html', flights=flights, today=today)
