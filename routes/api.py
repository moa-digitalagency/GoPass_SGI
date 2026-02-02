from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import User, Pass, PassType, AccessLog
from services import PassService
from security import agent_required

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/passes/search')
@login_required
@agent_required
def search_passes():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    passes = Pass.query.filter(
        Pass.pass_number.ilike(f'%{query}%')
    ).limit(10).all()
    
    return jsonify([p.to_dict() for p in passes])

@api_bp.route('/users/search')
@login_required
@agent_required
def search_users():
    query = request.args.get('q', '')
    role = request.args.get('role', '')
    
    if len(query) < 2:
        return jsonify([])
    
    users_query = User.query.filter(
        (User.first_name.ilike(f'%{query}%')) |
        (User.last_name.ilike(f'%{query}%')) |
        (User.email.ilike(f'%{query}%'))
    )
    
    if role:
        users_query = users_query.filter_by(role=role)
    
    users = users_query.limit(10).all()
    
    return jsonify([u.to_dict() for u in users])

@api_bp.route('/holders')
@login_required
@agent_required
def get_holders():
    holders = User.query.filter_by(role='holder', is_active=True).all()
    return jsonify([{
        'id': h.id,
        'name': f'{h.first_name} {h.last_name}',
        'email': h.email
    } for h in holders])

@api_bp.route('/pass-types')
@login_required
def get_pass_types():
    types = PassType.query.filter_by(is_active=True).all()
    return jsonify([t.to_dict() for t in types])

@api_bp.route('/statistics')
@login_required
@agent_required
def get_statistics():
    stats = PassService.get_statistics()
    return jsonify(stats)

@api_bp.route('/validate', methods=['POST'])
@login_required
@agent_required
def validate():
    data = request.get_json()
    pass_number = data.get('pass_number', '').strip()
    location = data.get('location', '')
    
    result = PassService.validate_pass(
        pass_number=pass_number,
        validator_id=current_user.id,
        location=location
    )
    
    return jsonify(result)

@api_bp.route('/recent-validations')
@login_required
@agent_required
def recent_validations():
    limit = request.args.get('limit', 10, type=int)
    validations = AccessLog.query.order_by(
        AccessLog.validation_time.desc()
    ).limit(limit).all()
    
    return jsonify([v.to_dict() for v in validations])
