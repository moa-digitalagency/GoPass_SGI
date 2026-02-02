from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User
from services import UserService
from security import admin_required, log_audit

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    if role:
        query = query.filter_by(role=role)

    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('users/index.html', users=users, search=search, current_role=role)

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
        else:
            try:
                user = UserService.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
                log_audit('create_user', 'user', user.id, f'Utilisateur {username} créé')
                flash(f'Utilisateur {username} créé avec succès.', 'success')
                return redirect(url_for('users.index'))
            except Exception as e:
                flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template('users/create.html')

@users_bp.route('/<int:id>')
@login_required
@admin_required
def view(id):
    user = User.query.get_or_404(id)
    # passes = Pass.query.filter_by(holder_id=id).all()
    passes = [] # Placeholder until we have GoPass logic
    
    return render_template('users/view.html', user=user, passes=passes)

@users_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role = request.form.get('role')
        user.phone = request.form.get('phone')

        password = request.form.get('password')
        if password:
            user.set_password(password)
            
        db.session.commit()
        log_audit('update_user', 'user', user.id, 'Profil mis à jour')
        flash('Utilisateur mis à jour avec succès.', 'success')
        return redirect(url_for('users.view', id=user.id))

    return render_template('users/edit.html', user=user)

@users_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle(id):
    if id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'danger')
        return redirect(url_for('users.index'))

    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activé' if user.is_active else 'désactivé'
    log_audit('toggle_user', 'user', user.id, f'Compte {status}')
    flash(f'Compte utilisateur {status}.', 'info')
    return redirect(url_for('users.index'))
