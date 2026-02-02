from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import User, Pass, AccessLog, PassType
from services import PassService, UserService
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    pass_stats = PassService.get_statistics()
    user_stats = UserService.get_statistics()
    
    recent_validations = AccessLog.query.order_by(
        AccessLog.validation_time.desc()
    ).limit(10).all()
    
    recent_passes = Pass.query.order_by(
        Pass.created_at.desc()
    ).limit(5).all()
    
    pass_types = PassType.query.filter_by(is_active=True).all()
    pass_type_stats = []
    for pt in pass_types:
        count = Pass.query.filter_by(type_id=pt.id, status='active').count()
        pass_type_stats.append({
            'name': pt.name,
            'color': pt.color,
            'count': count
        })
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    daily_validations = []
    for i in range(7):
        day = week_ago + timedelta(days=i+1)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = AccessLog.query.filter(
            AccessLog.validation_time >= day_start,
            AccessLog.validation_time <= day_end
        ).count()
        daily_validations.append({
            'date': day.strftime('%d/%m'),
            'count': count
        })
    
    return render_template('dashboard/index.html',
        pass_stats=pass_stats,
        user_stats=user_stats,
        recent_validations=recent_validations,
        recent_passes=recent_passes,
        pass_type_stats=pass_type_stats,
        daily_validations=daily_validations
    )
