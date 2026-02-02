from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Pass, PassType, User, AccessLog
from services import PassService
from security import agent_required, admin_required, log_audit
from datetime import datetime

passes_bp = Blueprint('passes', __name__, url_prefix='/passes')

@passes_bp.route('/')
@login_required
@agent_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Pass.query
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.join(User, Pass.holder_id == User.id).filter(
            (Pass.pass_number.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    passes = query.order_by(Pass.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    pass_types = PassType.query.filter_by(is_active=True).all()
    
    return render_template('passes/index.html', 
        passes=passes,
        pass_types=pass_types,
        current_status=status,
        search=search
    )

@passes_bp.route('/create', methods=['GET', 'POST'])
@login_required
@agent_required
def create():
    if request.method == 'POST':
        holder_id = request.form.get('holder_id')
        type_id = request.form.get('type_id')
        notes = request.form.get('notes')
        
        try:
            new_pass = PassService.create_pass(
                holder_id=holder_id,
                type_id=type_id,
                issued_by=current_user.id,
                notes=notes
            )
            log_audit('create_pass', 'pass', new_pass.id, f'Pass {new_pass.pass_number} créé')
            flash(f'Pass {new_pass.pass_number} créé avec succès!', 'success')
            return redirect(url_for('passes.view', id=new_pass.id))
        except Exception as e:
            flash(f'Erreur lors de la création du pass: {str(e)}', 'danger')
    
    holders = User.query.filter_by(role='holder', is_active=True).all()
    pass_types = PassType.query.filter_by(is_active=True).all()
    
    return render_template('passes/create.html', 
        holders=holders, 
        pass_types=pass_types
    )

@passes_bp.route('/<int:id>')
@login_required
def view(id):
    pass_record = Pass.query.get_or_404(id)
    
    if current_user.role == 'holder' and pass_record.holder_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    validations = AccessLog.query.filter_by(pass_id=id).order_by(
        AccessLog.validation_time.desc()
    ).limit(20).all()
    
    return render_template('passes/view.html', 
        pass_record=pass_record,
        validations=validations
    )

@passes_bp.route('/<int:id>/suspend', methods=['POST'])
@login_required
@agent_required
def suspend(id):
    if PassService.suspend_pass(id):
        log_audit('suspend_pass', 'pass', id, 'Pass suspendu')
        flash('Pass suspendu avec succès.', 'warning')
    else:
        flash('Erreur lors de la suspension du pass.', 'danger')
    return redirect(url_for('passes.view', id=id))

@passes_bp.route('/<int:id>/activate', methods=['POST'])
@login_required
@agent_required
def activate(id):
    if PassService.activate_pass(id):
        log_audit('activate_pass', 'pass', id, 'Pass activé')
        flash('Pass activé avec succès.', 'success')
    else:
        flash('Erreur lors de l\'activation du pass.', 'danger')
    return redirect(url_for('passes.view', id=id))

@passes_bp.route('/<int:id>/revoke', methods=['POST'])
@login_required
@admin_required
def revoke(id):
    if PassService.revoke_pass(id):
        log_audit('revoke_pass', 'pass', id, 'Pass révoqué')
        flash('Pass révoqué avec succès.', 'danger')
    else:
        flash('Erreur lors de la révocation du pass.', 'danger')
    return redirect(url_for('passes.view', id=id))

@passes_bp.route('/types')
@login_required
@admin_required
def types():
    pass_types = PassType.query.all()
    return render_template('passes/types.html', pass_types=pass_types)

@passes_bp.route('/types/create', methods=['POST'])
@login_required
@admin_required
def create_type():
    name = request.form.get('name')
    description = request.form.get('description')
    validity_days = request.form.get('validity_days', 365, type=int)
    color = request.form.get('color', '#3B82F6')
    
    pass_type = PassType(
        name=name,
        description=description,
        validity_days=validity_days,
        color=color
    )
    db.session.add(pass_type)
    db.session.commit()
    
    log_audit('create_pass_type', 'pass_type', pass_type.id, f'Type {name} créé')
    flash(f'Type de pass "{name}" créé avec succès.', 'success')
    return redirect(url_for('passes.types'))

@passes_bp.route('/types/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_type(id):
    pass_type = PassType.query.get_or_404(id)
    pass_type.is_active = not pass_type.is_active
    db.session.commit()
    
    status = 'activé' if pass_type.is_active else 'désactivé'
    flash(f'Type de pass {status}.', 'info')
    return redirect(url_for('passes.types'))

@passes_bp.route('/my-passes')
@login_required
def my_passes():
    passes = Pass.query.filter_by(holder_id=current_user.id).order_by(
        Pass.created_at.desc()
    ).all()
    return render_template('passes/my_passes.html', passes=passes)
