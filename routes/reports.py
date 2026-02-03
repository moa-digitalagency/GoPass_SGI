"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for reports.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models import db, Flight, GoPass, AccessLog
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

AIRPORT_COORDS = {
    'FIH': {'lat': -4.3857, 'lng': 15.4446, 'name': "N'Djili (Kinshasa)"},
    'FBM': {'lat': -11.5913, 'lng': 27.5309, 'name': "Lubumbashi"},
    'GOM': {'lat': -1.6698, 'lng': 29.2382, 'name': "Goma"},
    'FKI': {'lat': 0.4815, 'lng': 25.3380, 'name': "Kisangani"},
    'MDK': {'lat': 0.0469, 'lng': 18.2886, 'name': "Mbandaka"},
    'KGA': {'lat': -5.8666, 'lng': 22.4166, 'name': "Kananga"},
    'MJM': {'lat': -6.1219, 'lng': 23.5714, 'name': "Mbuji-Mayi"},
}

@reports_bp.route('/')
@login_required
def index():
    # 1. Anti-Coulage (Audit)
    # Get recent flights (e.g. last 10)
    flights = Flight.query.order_by(Flight.departure_time.desc()).limit(10).all()
    audit_data = []
    for f in flights:
        # Scanned count: GoPasses for this flight that have been scanned (scan_date is not None)
        scanned_count = GoPass.query.filter_by(flight_id=f.id).filter(GoPass.scan_date != None).count()
        audit_data.append({
            'flight_number': f.flight_number,
            'manifest': f.manifest_pax_count,
            'scanned': scanned_count,
            'alert': scanned_count > f.manifest_pax_count
        })

    # 2. Revenue Distribution
    revenue_query = db.session.query(
        GoPass.payment_method,
        func.sum(GoPass.price)
    ).filter(
        GoPass.payment_status == 'paid'
    ).group_by(
        GoPass.payment_method
    ).all()

    revenue_data = {}
    for method, total in revenue_query:
        if not method: method = 'Inconnu'
        revenue_data[method] = float(total) if total else 0.0

    # Categorize into Cash vs Mobile Money (M-Pesa, Airtel, Orange)
    # The requirement says "Cash vs Mobile Money".
    # Assuming 'Cash' is Cash, others are Mobile Money.
    revenue_chart_data = {
        'Cash': revenue_data.get('Cash', 0) + revenue_data.get('cash', 0), # Handle case sensitivity if needed
        'Mobile Money': 0
    }
    for k, v in revenue_data.items():
        if k.lower() != 'cash':
            revenue_chart_data['Mobile Money'] += v

    # 3. Flight Density Heatmap
    # Volume of tickets issued in last 24h by departure airport
    last_24h = datetime.utcnow() - timedelta(hours=24)
    density_query = db.session.query(
        Flight.departure_airport,
        func.count(GoPass.id)
    ).join(
        Flight
    ).filter(
        GoPass.issue_date >= last_24h
    ).group_by(
        Flight.departure_airport
    ).all()

    heatmap_data = []
    for airport_code, count in density_query:
        coords = AIRPORT_COORDS.get(airport_code)
        if coords:
            heatmap_data.append({
                'lat': coords['lat'],
                'lng': coords['lng'],
                'count': count,
                'name': coords['name']
            })

    # 4. Top Anomalies
    # Last 10 fraud attempts (red or orange or already scanned)
    # Statuses: ALREADY_SCANNED, WRONG_FLIGHT, INVALID, etc.
    # Note: AccessLog status field might store these codes.
    anomalies = AccessLog.query.options(
        joinedload(AccessLog.pass_record),
        joinedload(AccessLog.validator)
    ).filter(
        AccessLog.status.in_(['ALREADY_SCANNED', 'WRONG_FLIGHT', 'INVALID', 'error', 'warning']) # Catch all non-valid
    ).order_by(
        AccessLog.validation_time.desc()
    ).limit(10).all()

    # Pass data to template
    return render_template('reports/index.html',
        audit_data=audit_data,
        revenue_data=revenue_chart_data,
        heatmap_data=heatmap_data,
        anomalies=anomalies
    )

@reports_bp.route('/anomalies')
@login_required
def anomalies():
    # Fetch all anomalies (rejected scans)
    # Limit to 100 most recent for now
    anomalies_list = AccessLog.query.options(
        joinedload(AccessLog.pass_record),
        joinedload(AccessLog.validator)
    ).filter(
        ~AccessLog.status.in_(['valid', 'granted'])
    ).order_by(
        AccessLog.validation_time.desc()
    ).limit(100).all()

    return render_template('reports/anomalies.html', anomalies=anomalies_list)
