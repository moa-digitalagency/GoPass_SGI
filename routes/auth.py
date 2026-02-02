from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from security import log_audit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Votre compte est désactivé.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user)
            log_audit('login', 'user', user.id, f'Connexion réussie')
            flash('Connexion réussie!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit('logout', 'user', current_user.id, 'Déconnexion')
    logout_user()
    flash('Déconnexion réussie.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        
        new_password = request.form.get('new_password')
        if new_password:
            current_password = request.form.get('current_password')
            if current_user.check_password(current_password):
                current_user.set_password(new_password)
                flash('Mot de passe mis à jour.', 'success')
            else:
                flash('Mot de passe actuel incorrect.', 'danger')
                return render_template('auth/profile.html')
        
        db.session.commit()
        flash('Profil mis à jour avec succès.', 'success')
    
    return render_template('auth/profile.html')
