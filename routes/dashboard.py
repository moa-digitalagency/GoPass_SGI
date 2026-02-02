from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.pass_service import PassService
from services.user_service import UserService
from datetime import datetime, timedelta
from models import AccessLog, GoPass
from sqlalchemy.orm import joinedload

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

    return render_template('dashboard/index.html',
        pass_stats=pass_stats,
        user_stats=user_stats,
        recent_validations=recent_validations,
        recent_passes=recent_passes,
        pass_type_stats=[],
        daily_validations=[]
    )
