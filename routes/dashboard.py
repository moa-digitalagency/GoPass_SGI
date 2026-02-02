from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.pass_service import PassService
from services.user_service import UserService
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    pass_stats = PassService.get_statistics()
    user_stats = UserService.get_statistics()
    
    return render_template('dashboard/index.html',
        pass_stats=pass_stats,
        user_stats=user_stats,
        recent_validations=[],
        recent_passes=[],
        pass_type_stats=[],
        daily_validations=[]
    )
