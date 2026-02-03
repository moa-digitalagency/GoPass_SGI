from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, Device, Printer, SecurityKey
from datetime import datetime

infrastructure_bp = Blueprint('infrastructure', __name__, url_prefix='/infrastructure')

@infrastructure_bp.before_request
@login_required
def before_request():
    # Only admin and maybe technical support should access this
    if current_user.role not in ['admin', 'tech']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))

@infrastructure_bp.route('/devices')
def devices():
    devices_list = Device.query.all()
    # Logic for status indicator (Green if online < 1h, Grey otherwise)
    # We can handle this in the template using time_ago filter or similar logic
    return render_template('infrastructure/devices.html', devices=devices_list, now=datetime.utcnow())

@infrastructure_bp.route('/printers')
def printers():
    printers_list = Printer.query.all()
    return render_template('infrastructure/printers.html', printers=printers_list)

@infrastructure_bp.route('/security-keys')
def security_keys():
    keys_list = SecurityKey.query.all()
    return render_template('infrastructure/security_keys.html', keys=keys_list)

# API endpoints for updates (optional, if we want to update from UI)
@infrastructure_bp.route('/api/devices/ping/<unique_id>', methods=['POST'])
def device_ping(unique_id):
    device = Device.query.filter_by(unique_id=unique_id).first()
    if device:
        device.last_ping = datetime.utcnow()
        data = request.json
        if data:
            if 'battery_level' in data:
                device.battery_level = data['battery_level']
            if 'app_version' in data:
                device.app_version = data['app_version']
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Device not found'}), 404
