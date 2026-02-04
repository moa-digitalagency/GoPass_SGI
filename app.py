#!/usr/bin/env python3
"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for app.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

"""
GO-PASS SGI-GP - Systeme de Gestion Integree GO-PASS
Main Application Entry Point
"""

import os
from flask import Flask, redirect, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect

from config import config
from models import db
from security import login_manager
from utils import format_date, format_datetime, time_ago, get_status_color, get_status_label, get_role_label
from utils.i18n import get_text, load_translations
from flask import session

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__, 
                static_folder='statics',
                static_url_path='/static')
    
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf = CSRFProtect(app)
    
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['status_color'] = get_status_color
    app.jinja_env.filters['status_label'] = get_status_label
    app.jinja_env.filters['role_label'] = get_role_label
    
    # Initialize translations
    with app.app_context():
        load_translations()

    @app.context_processor
    def inject_i18n():
        return dict(
            t=get_text,
            current_lang=session.get('lang', 'fr')
        )

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.users import users_bp
    from routes.api import api_bp
    from routes.public import public_bp
    from routes.flights import flights_bp
    from routes.finance import finance_bp
    from routes.reports import reports_bp
    from routes.infrastructure import infrastructure_bp
    from routes.settings import settings_bp
    from routes.ops import ops_bp
    from routes.telegram import telegram_bp
    from routes.preview import preview_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(public_bp) # Mount at root
    app.register_blueprint(flights_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(infrastructure_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(ops_bp)
    app.register_blueprint(telegram_bp)
    app.register_blueprint(preview_bp)

    # CSRF Exemption for Webhooks
    csrf.exempt(app.view_functions['telegram.webhook'])
    
    @app.route('/login-check')
    def login_check():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'

        # CyberConfiance Security Headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval';"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = "geolocation=(self), microphone=()"
        return response
    
    return app


app = create_app()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
