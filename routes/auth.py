"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for auth.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import db, User
from security import log_audit

auth_bp = Blueprint('auth', __name__)

def is_safe_url(target):
    """
    Ensure the redirect target is safe (local to the application).
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return (not test_url.netloc or test_url.netloc == ref_url.netloc) and \
           (not test_url.scheme or test_url.scheme in ('http', 'https'))

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
            if not next_page or not is_safe_url(next_page):
                if user.role == 'agent':
                    next_page = url_for('ops.pos')
                elif user.role == 'controller':
                    next_page = url_for('ops.scanner')
                else:
                    next_page = url_for('dashboard.index')

            return redirect(next_page)
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
