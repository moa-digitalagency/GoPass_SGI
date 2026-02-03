from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from services import FlightService, GoPassService
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
import qrcode
import tempfile
import os
import base64

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

        # In a real app we'd filter by flight number too if provided
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            flights = FlightService.get_flights(date=date)
            # Filter in python for flight number match if needed
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

        # Simulate payment
        # ... payment logic ...

        gopass = GoPassService.create_gopass(
            flight_id=flight.id,
            passenger_name=passenger_name,
            passenger_passport=passport
        )

        return redirect(url_for('public.confirmation', id=gopass.id))

    return render_template('public/checkout.html', flight=flight)

@public_bp.route('/confirmation/<int:id>')
def confirmation(id):
    gopass = GoPassService.get_gopass(id)
    if not gopass:
        return redirect(url_for('public.index'))

    # Generate QR Base64 for display
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(gopass.token)
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

    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(gopass.token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR to temp file to draw on PDF
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name)
        qr_path = tmp.name

    # Generate PDF
    buffer = io.BytesIO()

    fmt = request.args.get('format')
    if fmt == 'thermal':
        # 80mm width layout
        width = 80 * mm
        height = 160 * mm # Fixed height for receipt
        p = canvas.Canvas(buffer, pagesize=(width, height))

        # Helper for centering
        def draw_centered(text, y, font="Helvetica", size=10):
            p.setFont(font, size)
            text_width = p.stringWidth(text, font, size)
            p.drawString((width - text_width) / 2, y, text)

        y = height - 10 * mm
        draw_centered("RÉPUBLIQUE DÉMOCRATIQUE DU CONGO", y, "Helvetica-Bold", 10)
        y -= 5 * mm
        draw_centered("RVA - IDEF (GoPass)", y, "Helvetica-Bold", 12)

        y -= 10 * mm
        p.setLineWidth(1)
        p.line(5*mm, y, width - 5*mm, y)
        y -= 5 * mm

        draw_centered(f"VOL: {gopass.flight.flight_number}", y, "Helvetica-Bold", 12)
        y -= 5 * mm
        draw_centered(f"{gopass.flight.departure_time.strftime('%d/%m/%Y %H:%M')}", y, "Helvetica", 10)

        y -= 10 * mm
        draw_centered("PASSAGER", y, "Helvetica", 8)
        y -= 5 * mm
        draw_centered(gopass.passenger_name, y, "Helvetica-Bold", 12)
        y -= 5 * mm
        draw_centered(f"DOC: {gopass.passenger_passport}", y, "Helvetica", 10)

        # QR Code
        qr_size = 40 * mm
        y -= (qr_size + 5 * mm)
        p.drawImage(qr_path, (width - qr_size) / 2, y, width=qr_size, height=qr_size)

        y -= 5 * mm
        draw_centered(f"Ref: {gopass.payment_ref}", y, "Helvetica", 8)
        y -= 4 * mm
        draw_centered("Reçu Client - Copie", y, "Helvetica-Oblique", 8)

    else:
        # A4 Layout (Default)
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Logo header (Text for now)
        p.setFont("Helvetica-Bold", 24)
        p.drawString(2*cm, height - 2*cm, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
        p.setFont("Helvetica", 16)
        p.drawString(2*cm, height - 3*cm, "RVA - Redevance IDEF (GoPass)")

        # Flight Info
        p.setFont("Helvetica-Bold", 14)
        p.drawString(2*cm, height - 5*cm, f"VOL: {gopass.flight.flight_number}")
        p.drawString(2*cm, height - 6*cm, f"DATE: {gopass.flight.departure_time.strftime('%d/%m/%Y %H:%M')}")
        p.drawString(2*cm, height - 7*cm, f"PASSAGER: {gopass.passenger_name}")
        p.drawString(2*cm, height - 8*cm, f"PASSEPORT: {gopass.passenger_passport}")

        # Draw QR
        p.drawImage(qr_path, 12*cm, height - 9*cm, width=6*cm, height=6*cm)

        p.setFont("Helvetica", 10)
        p.drawString(2*cm, height - 10*cm, f"Ref Paiement: {gopass.payment_ref}")
        p.drawString(2*cm, height - 11*cm, f"Ce document doit être présenté lors du contrôle.")

    p.showPage()
    p.save()

    os.unlink(qr_path)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"GoPass_{gopass.id}.pdf", mimetype='application/pdf')
