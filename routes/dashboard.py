from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.pass_service import PassService
from services.user_service import UserService
from datetime import datetime, timedelta
from models import AccessLog, GoPass, Flight, db
from sqlalchemy.orm import joinedload
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    pass_stats = PassService.get_statistics()
    user_stats = UserService.get_statistics()
    
    recent_validations = AccessLog.query.options(joinedload(AccessLog.pass_record)).order_by(
        AccessLog.validation_time.desc()
    ).limit(10).all()

    recent_passes = GoPass.query.options(
        joinedload(GoPass.holder),
        joinedload(GoPass.pass_type)
    ).order_by(GoPass.issue_date.desc()).limit(5).all()

    # Fetch daily validations for the last 7 days using a single aggregation query
    start_date = datetime.utcnow().date() - timedelta(days=7)

    results = db.session.query(
        func.date(AccessLog.validation_time),
        func.count(AccessLog.id)
    ).filter(
        AccessLog.validation_time >= start_date
    ).group_by(
        func.date(AccessLog.validation_time)
    ).all()

    counts_map = {str(r[0]): r[1] for r in results}

    daily_validations = []
    for i in range(7):
        day = start_date + timedelta(days=i+1)
        day_str = day.strftime('%Y-%m-%d')
        daily_validations.append(counts_map.get(day_str, 0))

    # --- Gap Analysis (Audit) ---
    today = datetime.utcnow().date()
    todays_flights = Flight.query.filter(
        func.date(Flight.departure_time) == today
    ).all()

    audit_data = []
    for f in todays_flights:
        scanned_count = GoPass.query.filter_by(flight_id=f.id).filter(GoPass.scan_date != None).count()
        audit_data.append({
            'flight_number': f.flight_number,
            'declared': f.manifest_pax_count,
            'scanned': scanned_count,
            'alert': scanned_count > f.manifest_pax_count
        })

    # --- Financial Pie Chart (Today's Revenue) ---
    revenue_query = db.session.query(
        GoPass.payment_method,
        func.sum(GoPass.price)
    ).filter(
        GoPass.payment_status == 'paid',
        func.date(GoPass.issue_date) == today
    ).group_by(
        GoPass.payment_method
    ).all()

    financial_data = {'Cash': 0, 'Mobile Money': 0}
    for method, amount in revenue_query:
        if not method: continue
        m_lower = method.lower()
        if 'cash' in m_lower or 'esp' in m_lower:
            financial_data['Cash'] += float(amount)
        else:
            financial_data['Mobile Money'] += float(amount)

    return render_template('dashboard/index.html',
        pass_stats=pass_stats,
        user_stats=user_stats,
        recent_validations=recent_validations,
        recent_passes=recent_passes,
        pass_type_stats=[],
        daily_validations=daily_validations,
        audit_data=audit_data,
        financial_data=financial_data
    )
