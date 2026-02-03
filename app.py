#!/usr/bin/env python3
"""
GO-PASS SGI-GP - Systeme de Gestion Integree GO-PASS
Main Application Entry Point
"""

import os
from flask import Flask, redirect, url_for
from flask_login import current_user

from config import config
from models import db
from security import login_manager
from utils import format_date, format_datetime, time_ago, get_status_color, get_status_label, get_role_label


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__, 
                static_folder='statics',
                static_url_path='/static')
    
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    login_manager.init_app(app)
    
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['status_color'] = get_status_color
    app.jinja_env.filters['status_label'] = get_status_label
    app.jinja_env.filters['role_label'] = get_role_label
    
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
        return response
    
    return app


app = create_app()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
