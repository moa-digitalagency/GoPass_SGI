from flask import Blueprint, jsonify
from services.external_data_sync import ExternalDataSync
from flask_login import login_required, current_user

api_sync_bp = Blueprint('api_sync', __name__, url_prefix='/api/sync')

@api_sync_bp.route('/airports', methods=['POST'])
@login_required
def sync_airports():
    if current_user.role != 'admin':
         return jsonify({"status": "error", "message": "Unauthorized"}), 403

    result = ExternalDataSync.sync_airports()
    return jsonify(result)

@api_sync_bp.route('/airlines', methods=['POST'])
@login_required
def sync_airlines():
    if current_user.role != 'admin':
         return jsonify({"status": "error", "message": "Unauthorized"}), 403

    result = ExternalDataSync.sync_airlines()
    return jsonify(result)
