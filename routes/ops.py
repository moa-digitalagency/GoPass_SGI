"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for ops.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

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
    flight_mode = data.get('flight_mode', 'today')

    flight_id = data.get('flight_id')

    # New fields for verification
    verification_source = data.get('verification_source', 'manual')
    flight_details = data.get('flight_details')
    unit_price = float(data.get('price', 50.0))

    if flight_mode == 'manual':
        manual_date_str = data.get('manual_flight_date')
        manual_number = data.get('manual_flight_number')

        if not manual_date_str or not manual_number:
             return jsonify({'error': 'Informations de vol manquantes'}), 400

        try:
            manual_date = datetime.strptime(manual_date_str, '%Y-%m-%d').date()
        except ValueError:
             return jsonify({'error': 'Format de date invalide'}), 400

        # Create or Get Flight
        airport_code = current_user.location or 'FIH'
        flight = FlightService.get_or_create_manual_flight(manual_number, manual_date, airport_code)
        flight_id = flight.id
    else:
        if not flight_id:
            return jsonify({'error': 'Vol non sélectionné'}), 400

    # Handle Passengers (Bulk or Single Legacy)
    passengers = data.get('passengers', [])
    if not passengers:
        # Backward compatibility
        p_name = data.get('passenger_name')
        p_doc = data.get('passenger_passport')
        p_type = data.get('passenger_document_type', 'Passeport')
        if p_name and p_doc:
            passengers.append({
                'name': p_name,
                'doc_num': p_doc,
                'doc_type': p_type
            })

    if not passengers:
        return jsonify({'error': 'Aucun passager spécifié'}), 400

    created_tickets = []
    total_price = 0.0

    try:
        for p in passengers:
            name = p.get('name') or p.get('passenger_name')
            doc_num = p.get('doc_num') or p.get('passenger_passport')
            doc_type = p.get('doc_type') or p.get('passenger_document_type', 'Passeport')

            if not name or not doc_num:
                raise ValueError("Données passager incomplètes")

            # Generate Metadata
            terminal_id = "POS-01" # In real app, from config or cookie
            session_ref = f"SES-{int(datetime.now().timestamp())}"
            payment_ref_str = f"{terminal_id}-{session_ref}"

            source_metadata = {
                "terminal_id": terminal_id,
                "session_id": session_ref,
                "agent_name": current_user.username
            }

            gopass = GoPassService.create_gopass(
                flight_id=flight_id,
                passenger_name=name,
                passenger_passport=doc_num,
                passenger_document_type=doc_type,
                price=unit_price,
                payment_method='Cash',
                payment_ref=payment_ref_str, # Use Session/Trans ID as payment_ref too
                sold_by=current_user.id,
                sales_channel='DESK',
                payment_reference=payment_ref_str,
                source_metadata=source_metadata,
                verification_source=verification_source,
                flight_details=flight_details,
                commit=False
            )
            created_tickets.append(gopass)
            total_price += unit_price

        # Commit all transactions at once
        db.session.commit()

        # Prepare Response
        response_tickets = []
        last_gopass = None
        for gp in created_tickets:
            last_gopass = gp
            response_tickets.append({
                'gopass_id': gp.id,
                'pdf_url': url_for('public.download_pdf', id=gp.id, format='thermal'),
                'passenger_name': gp.passenger_name,
                'price': gp.price
            })

        issue_time = datetime.now().strftime('%H:%M')

        return jsonify({
            'success': True,
            'tickets': response_tickets,
            'total_price': total_price,
            'time': issue_time,
            'flight_number': last_gopass.flight.flight_number if last_gopass else "",
            'status': 'Payé'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ops_bp.route('/scanner')
@role_required('admin', 'controller')
def scanner():
    # Similar to POS, get today's flights for selection
    airport_code = current_user.location
    today = datetime.now().date()

    flights = FlightService.get_flights(airport_code=airport_code, date=today)

    return render_template('ops/scanner.html', flights=flights, today=today)
