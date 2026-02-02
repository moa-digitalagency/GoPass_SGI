from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from services import PassService
from security import agent_required

validation_bp = Blueprint('validation', __name__, url_prefix='/validation')

@validation_bp.route('/')
@login_required
@agent_required
def index():
    return render_template('validation/index.html')

@validation_bp.route('/check', methods=['POST'])
@login_required
@agent_required
def check():
    data = request.get_json()
    pass_number = data.get('pass_number', '').strip().upper()
    location = data.get('location', '')
    
    if not pass_number:
        return jsonify({
            'valid': False,
            'status': 'error',
            'message': 'Numéro de pass requis'
        })
    
    result = PassService.validate_pass(
        pass_number=pass_number,
        validator_id=current_user.id,
        location=location
    )
    
    return jsonify(result)

@validation_bp.route('/scan')
@login_required
@agent_required
def scan():
    return render_template('validation/scan.html')
