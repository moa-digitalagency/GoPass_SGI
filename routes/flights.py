"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for flights.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Flight, db
from services import FlightService
from security import admin_required, agent_required
from datetime import datetime

flights_bp = Blueprint('flights', __name__, url_prefix='/flights')

@flights_bp.route('/')
@login_required
@agent_required
def index():
    page = request.args.get('page', 1, type=int)
    airport_code = request.args.get('airport_code', '')
    date_str = request.args.get('date', '')

    query = Flight.query

    if airport_code:
        query = query.filter_by(departure_airport=airport_code)

    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            # Filter by date range (start of day to end of day)
            # Or just >= date
            query = query.filter(Flight.departure_time >= date)
        except:
            pass

    flights = query.order_by(Flight.departure_time.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('flights/index.html', flights=flights, airport_code=airport_code, date=date_str)

@flights_bp.route('/create', methods=['GET', 'POST'])
@login_required
@agent_required
def create():
    if request.method == 'POST':
        flight_number = request.form.get('flight_number')
        airline = request.form.get('airline')
        dep_airport = request.form.get('dep_airport')
        arr_airport = request.form.get('arr_airport')
        dep_time_str = request.form.get('dep_time')
        arr_time_str = request.form.get('arr_time')
        capacity = request.form.get('capacity', 0, type=int)
        aircraft_registration = request.form.get('aircraft_registration')

        try:
            dep_time = datetime.strptime(dep_time_str, '%Y-%m-%dT%H:%M')
            arr_time = datetime.strptime(arr_time_str, '%Y-%m-%dT%H:%M') if arr_time_str else None

            FlightService.create_manual_flight(
                flight_number=flight_number,
                airline=airline,
                dep_airport=dep_airport,
                arr_airport=arr_airport,
                dep_time=dep_time,
                arr_time=arr_time,
                capacity=capacity,
                aircraft_registration=aircraft_registration
            )

            flash(f'Vol {flight_number} créé avec succès.', 'success')
            return redirect(url_for('flights.index'))

        except Exception as e:
            flash(f'Erreur: {str(e)}', 'danger')

    return render_template('flights/create.html')

@flights_bp.route('/sync')
@login_required
@agent_required
def sync():
    airport = request.args.get('airport', 'FIH')
    date_str = request.args.get('date')
    date = None

    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash('Format de date invalide.', 'warning')

    try:
        count = FlightService.sync_flights_from_api(airport, date=date)
        msg_date = date_str if date_str else "Aujourd'hui"
        flash(f'{count} vols synchronisés depuis l\'API pour {airport} ({msg_date}).', 'success')
    except Exception as e:
        flash(f'Erreur de synchronisation: {str(e)}', 'danger')

    return redirect(url_for('flights.index'))

@flights_bp.route('/<int:id>')
@login_required
@agent_required
def view(id):
    flight = Flight.query.get_or_404(id)
    return render_template('flights/view.html', flight=flight)

@flights_bp.route('/manifest/<int:id>', methods=['POST'])
@login_required
@agent_required
def upload_manifest(id):
    if 'manifest_file' not in request.files:
        flash('Aucun fichier sélectionné', 'danger')
        return redirect(url_for('flights.index'))

    file = request.files['manifest_file']
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'danger')
        return redirect(url_for('flights.index'))

    try:
        count = FlightService.import_manifest(id, file)
        flash(f'Manifeste importé avec succès. {count} passagers détectés.', 'success')
    except Exception as e:
        flash(f'Erreur lors de l\'import: {str(e)}', 'danger')

    return redirect(url_for('flights.index'))

@flights_bp.route('/status/<int:id>', methods=['POST'])
@login_required
@agent_required
def update_status(id):
    status = request.form.get('status')
    if not status:
        flash('Statut invalide', 'danger')
        return redirect(url_for('flights.index'))

    try:
        FlightService.update_status(id, status)
        flash(f'Statut du vol mis à jour: {status}', 'success')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')

    return redirect(url_for('flights.index'))
