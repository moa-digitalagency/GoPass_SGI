from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from services import FlightService, GoPassService
from datetime import datetime
import io
import qrcode
import base64
import json

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    return render_template('public/index.html', now=datetime.now())

@public_bp.route('/search', methods=['GET', 'POST'])
def search():
    flights = []
    if request.method == 'POST':
        date_str = request.form.get('date')
        flight_number = request.form.get('flight_number')

        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            flights = FlightService.get_flights(date=date)
            if flight_number:
                flights = [f for f in flights if flight_number.lower() in f.flight_number.lower()]

    return render_template('public/search.html', flights=flights)

@public_bp.route('/checkout/<int:flight_id>', methods=['GET', 'POST'])
def checkout(flight_id):
    flight = FlightService.get_flight(flight_id)
    if not flight:
        flash('Vol non trouvé', 'danger')
        return redirect(url_for('public.search'))

    if request.method == 'POST':
        passenger_name = request.form.get('passenger_name')
        passport = request.form.get('passport')
        document_type = request.form.get('document_type', 'Passeport')

        gopass = GoPassService.create_gopass(
            flight_id=flight.id,
            passenger_name=passenger_name,
            passenger_passport=passport,
            passenger_document_type=document_type
        )

        return redirect(url_for('public.confirmation', id=gopass.id))

    return render_template('public/checkout.html', flight=flight)

@public_bp.route('/confirmation/<int:id>')
def confirmation(id):
    gopass = GoPassService.get_gopass(id)
    if not gopass:
        return redirect(url_for('public.index'))

    # Generate QR Content
    qr_payload = {
        "id_billet": gopass.id,
        "vol": gopass.flight.flight_number,
        "date": gopass.flight.departure_time.strftime('%Y-%m-%d'),
        "hash_signature": gopass.token
    }
    qr_data = json.dumps(qr_payload)

    # Generate QR Base64 for display
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return render_template('public/confirmation.html', gopass=gopass, qr_base64=qr_base64)

@public_bp.route('/download/<int:id>')
def download_pdf(id):
    gopass = GoPassService.get_gopass(id)
    if not gopass:
        return "Pass non trouvé", 404

    fmt = request.args.get('format', 'a4')
    pdf_bytes = GoPassService.generate_pdf_bytes(gopass, fmt=fmt)

    buffer = io.BytesIO(pdf_bytes)
    filename = f"GoPass_{gopass.flight.flight_number}_{gopass.id}.pdf"

    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
