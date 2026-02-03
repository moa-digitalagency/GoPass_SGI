from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.pass_service import PassService
from services.user_service import UserService
from datetime import datetime, timedelta
from models import AccessLog, GoPass, db
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

    return render_template('dashboard/index.html',
        pass_stats=pass_stats,
        user_stats=user_stats,
        recent_validations=recent_validations,
        recent_passes=recent_passes,
        pass_type_stats=[],
        daily_validations=daily_validations
    )
