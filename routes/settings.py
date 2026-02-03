from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.settings_service import SettingsService

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.before_request
@login_required
def before_request():
    if current_user.role not in ['admin', 'tech']:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard.index'))

@settings_bp.route('/general')
def general():
    return render_template('settings/general.html')

@settings_bp.route('/tariffs', methods=['GET', 'POST'])
def tariffs():
    if request.method == 'POST':
        # Handle update
        # Form data expected: price_{id}
        for key, value in request.form.items():
            if key.startswith('price_'):
                try:
                    tariff_id = key.split('_')[1]
                    SettingsService.update_tariff(tariff_id, value)
                except Exception as e:
                    pass # Continue or log error
        flash('Tarifs mis à jour avec succès.', 'success')
        return redirect(url_for('settings.tariffs'))

    tariffs = SettingsService.get_all_tariffs()
    return render_template('settings/tariffs.html', tariffs=tariffs)

@settings_bp.route('/airports', methods=['GET', 'POST'])
def airports():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            data = {
                'iata_code': request.form.get('iata_code'),
                'city': request.form.get('city'),
                'type': request.form.get('type')
            }
            if SettingsService.create_airport(data):
                flash('Aéroport ajouté.', 'success')
            else:
                flash('Erreur lors de l\'ajout (Code IATA existant ?).', 'danger')
        elif action == 'update':
            airport_id = request.form.get('id')
            data = {
                'iata_code': request.form.get('iata_code'),
                'city': request.form.get('city'),
                'type': request.form.get('type')
            }
            if SettingsService.update_airport(airport_id, data):
                flash('Aéroport modifié.', 'success')
            else:
                flash('Erreur lors de la modification.', 'danger')
        elif action == 'delete':
            airport_id = request.form.get('id')
            if SettingsService.delete_airport(airport_id):
                flash('Aéroport supprimé.', 'success')
            else:
                flash('Erreur lors de la suppression.', 'danger')

        return redirect(url_for('settings.airports'))

    airports = SettingsService.get_all_airports()
    return render_template('settings/airports.html', airports=airports)

@settings_bp.route('/airlines', methods=['GET', 'POST'])
def airlines():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            data = {
                'name': request.form.get('name'),
                'is_active': request.form.get('is_active') == 'on'
            }
            logo = request.files.get('logo')
            if SettingsService.create_airline(data, logo):
                flash('Compagnie ajoutée.', 'success')
            else:
                flash('Erreur lors de l\'ajout.', 'danger')
        elif action == 'update':
            airline_id = request.form.get('id')
            data = {
                'name': request.form.get('name'),
                'is_active': request.form.get('is_active') == 'on'
            }
            logo = request.files.get('logo')
            if SettingsService.update_airline(airline_id, data, logo):
                flash('Compagnie modifiée.', 'success')
            else:
                flash('Erreur lors de la modification.', 'danger')
        elif action == 'delete':
            airline_id = request.form.get('id')
            if SettingsService.delete_airline(airline_id):
                flash('Compagnie supprimée.', 'success')
            else:
                flash('Erreur lors de la suppression.', 'danger')

        return redirect(url_for('settings.airlines'))

    airlines = SettingsService.get_all_airlines()
    return render_template('settings/airlines.html', airlines=airlines)
