from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.pass_service import PassService
from services.user_service import UserService
from datetime import datetime, timedelta
from models import AccessLog, PassType, GoPass, db
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

    # Optimized Pass Type Statistics (Single Aggregation Query)
    pass_type_counts = db.session.query(
        PassType,
        func.count(GoPass.id)
    ).outerjoin(
        GoPass,
        (GoPass.type_id == PassType.id) & (GoPass.status == 'valid')
    ).filter(
        PassType.is_active == True
    ).group_by(PassType.id).all()

    pass_type_stats = []
    for pt, count in pass_type_counts:
        pass_type_stats.append({
            'name': pt.name,
            'count': count,
            'color': pt.color
        })

    return render_template('dashboard/index.html',
        pass_stats=pass_stats,
        user_stats=user_stats,
        recent_validations=recent_validations,
        recent_passes=[],
        pass_type_stats=pass_type_stats,
        daily_validations=[]
    )
