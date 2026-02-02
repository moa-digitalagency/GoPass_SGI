from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Pass
from services import UserService
from security import admin_required, agent_required, log_audit

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@login_required
@agent_required
def index():
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', '')
    search = request.args.get('search', '')
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('users/index.html',
        users=users,
        current_role=role,
        search=search
    )

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@agent_required
def create():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        role = request.form.get('role', 'holder')
        
        if role in ['admin', 'agent'] and current_user.role != 'admin':
            flash('Seul un administrateur peut créer des agents ou admins.', 'danger')
            return render_template('users/create.html')
        
        try:
            user = UserService.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role
            )
            log_audit('create_user', 'user', user.id, f'Utilisateur {username} créé')
            flash(f'Utilisateur {username} créé avec succès!', 'success')
            return redirect(url_for('users.view', id=user.id))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('users/create.html')

@users_bp.route('/<int:id>')
@login_required
@agent_required
def view(id):
    user = User.query.get_or_404(id)
    passes = Pass.query.filter_by(holder_id=id).order_by(
        Pass.created_at.desc()
    ).all()
    
    return render_template('users/view.html', user=user, passes=passes)

@users_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@agent_required
def edit(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            role = request.form.get('role')
            if role in ['admin', 'agent'] and current_user.role != 'admin':
                flash('Seul un administrateur peut modifier le rôle en admin ou agent.', 'danger')
                return render_template('users/edit.html', user=user)
            
            UserService.update_user(
                user_id=id,
                username=request.form.get('username'),
                email=request.form.get('email'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                phone=request.form.get('phone'),
                role=role,
                password=request.form.get('password') or None
            )
            log_audit('update_user', 'user', id, f'Utilisateur modifié')
            flash('Utilisateur mis à jour avec succès.', 'success')
            return redirect(url_for('users.view', id=id))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('users/edit.html', user=user)

@users_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle(id):
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'danger')
        return redirect(url_for('users.view', id=id))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activé' if user.is_active else 'désactivé'
    log_audit('toggle_user', 'user', id, f'Utilisateur {status}')
    flash(f'Utilisateur {status} avec succès.', 'info')
    return redirect(url_for('users.view', id=id))

@users_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(id):
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('users.view', id=id))
    
    passes_count = Pass.query.filter_by(holder_id=id).count()
    if passes_count > 0:
        flash(f'Impossible de supprimer: {passes_count} pass(s) associé(s).', 'danger')
        return redirect(url_for('users.view', id=id))
    
    username = user.username
    log_audit('delete_user', 'user', id, f'Utilisateur {username} supprimé')
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Utilisateur {username} supprimé avec succès.', 'success')
    return redirect(url_for('users.index'))
