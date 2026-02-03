from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
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

    # Generate QR Content
    qr_payload = {
        "id_billet": gopass.id,
        "vol": gopass.flight.flight_number,
        "date": gopass.flight.departure_time.strftime('%Y-%m-%d'),
        "hash_signature": gopass.token
    }
    qr_data = json.dumps(qr_payload)

    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name)
        qr_path = tmp.name

    buffer = io.BytesIO()
    fmt = request.args.get('format')

    if fmt == 'thermal':
        # MODULE B: THERMAL TICKET (80mm)
        width = 80 * mm
        # Calculate dynamic height? Or fixed. Thermal printers cut anywhere.
        # Let's start with a reasonable length.
        height = 180 * mm
        p = canvas.Canvas(buffer, pagesize=(width, height))

        def draw_centered(text, y, font="Helvetica", size=10):
            p.setFont(font, size)
            text_width = p.stringWidth(text, font, size)
            p.drawString((width - text_width) / 2, y, text)

        y = height - 5 * mm

        # 1. En-tête Compact
        # Logo RVA (Monochrome)
        logo_rva = os.path.join(current_app.static_folder, 'img/logo_rva.png')
        if os.path.exists(logo_rva):
            img_w, img_h = 20*mm, 20*mm
            p.drawImage(logo_rva, (width - img_w)/2, y - img_h, width=img_w, height=img_h)
            y -= (img_h + 2*mm)

        draw_centered("RVA - GO PASS", y, "Helvetica-Bold", 12)
        y -= 4 * mm
        draw_centered("Reçu de Paiement & Titre de Passage", y, "Helvetica", 8)
        y -= 6 * mm

        # Separator
        p.setLineWidth(1)
        p.line(2*mm, y, width - 2*mm, y)
        y -= 6 * mm

        # 2. Détails du Vol
        draw_centered(f"VOL : {gopass.flight.flight_number}", y, "Helvetica-Bold", 16)
        y -= 6 * mm
        draw_centered(f"DATE : {gopass.flight.departure_time.strftime('%d/%m/%Y')}", y, "Helvetica-Bold", 10)
        y -= 5 * mm
        draw_centered(f"DEP : {gopass.flight.departure_airport}", y, "Helvetica-Bold", 10)
        y -= 8 * mm

        # 3. Détails Passager
        passenger_name = gopass.passenger_name.upper() if gopass.passenger_name else "PASSAGER"
        draw_centered(passenger_name, y, "Helvetica", 10)
        y -= 8 * mm

        # 4. QR Code
        qr_size = 40 * mm
        p.drawImage(qr_path, (width - qr_size)/2, y - qr_size, width=qr_size, height=qr_size)
        y -= (qr_size + 5 * mm)

        # 5. Audit & Traçabilité
        p.setFont("Helvetica", 8)
        left_margin = 5 * mm
        line_height = 4 * mm

        agent_name = gopass.seller.username if gopass.seller else "Automate"
        terminal_id = "POS-001" # Placeholder as per discussion
        issue_time = gopass.issue_date.strftime('%H:%M:%S') if gopass.issue_date else "N/A"

        p.drawString(left_margin, y, f"ID Agent : {agent_name}")
        y -= line_height
        p.drawString(left_margin, y, f"Terminal : {terminal_id}")
        y -= line_height
        p.drawString(left_margin, y, f"Heure : {issue_time}")
        y -= line_height
        p.drawString(left_margin, y, f"Trans : {gopass.payment_ref or 'N/A'}")
        y -= line_height
        p.drawString(left_margin, y, f"Paiement : {gopass.payment_method or 'CASH'}")
        y -= 8 * mm

        # 6. Pied de Ticket
        draw_centered("Conservez ce ticket jusqu'à l'embarquement.", y, "Helvetica-Oblique", 7)
        y -= 4 * mm
        draw_centered("www.rva.cd", y, "Helvetica", 8)

    else:
        # MODULE A: A4 PDF (E-GoPass)
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # 1. En-tête (Header)
        # Logo Gauche: RVA
        logo_rva = os.path.join(current_app.static_folder, 'img/logo_rva.png')
        if os.path.exists(logo_rva):
            p.drawImage(logo_rva, 2*cm, height - 3.5*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True)

        # Logo Droite: GoPass
        logo_gopass = os.path.join(current_app.static_folder, 'img/logo_gopass.png')
        if os.path.exists(logo_gopass):
            p.drawImage(logo_gopass, width - 4.5*cm, height - 3.5*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True)

        # Titre Central
        title_y = height - 2*cm
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width/2, title_y, "REDEVANCE DE DÉVELOPPEMENT DES")
        p.drawCentredString(width/2, title_y - 0.6*cm, "INFRASTRUCTURES AÉROPORTUAIRES (IDEF)")

        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, title_y - 1.5*cm, "E-GoPass RDC - Titre de Voyage Numérique")

        # 2. Zone Information "Flight-Bound"
        # Draw box
        box_top = height - 5*cm
        box_height = 8*cm
        box_width = width - 4*cm
        p.setStrokeColor(colors.black)
        p.setFillColor(colors.whitesmoke)
        p.rect(2*cm, box_top - box_height, box_width, box_height, fill=1)
        p.setFillColor(colors.black)

        text_x = 3*cm
        current_y = box_top - 1.5*cm

        # PASSAGER
        p.setFont("Helvetica-Bold", 10)
        p.drawString(text_x, current_y, "PASSAGER")
        p.setFont("Helvetica", 14)
        p.drawString(text_x + 3*cm, current_y, gopass.passenger_name.upper())

        current_y -= 1.5*cm

        # VOL
        p.setFont("Helvetica-Bold", 10)
        p.drawString(text_x, current_y, "VOL")
        p.setFont("Helvetica-Bold", 24)
        p.drawString(text_x + 3*cm, current_y, gopass.flight.flight_number)

        current_y -= 1.5*cm

        # DATE
        p.setFont("Helvetica-Bold", 10)
        p.drawString(text_x, current_y, "DATE")
        p.setFont("Helvetica", 14)
        date_str = gopass.flight.departure_time.strftime('%d/%m/%Y')
        p.drawString(text_x + 3*cm, current_y, date_str)

        current_y -= 1.5*cm

        # ITINÉRAIRE
        p.setFont("Helvetica-Bold", 10)
        p.drawString(text_x, current_y, "ITINÉRAIRE")
        p.setFont("Helvetica", 14)
        itin = f"{gopass.flight.departure_airport}  ➔  {gopass.flight.arrival_airport}"
        p.drawString(text_x + 3*cm, current_y, itin)

        # 3. Zone de Sécurité (QR Code)
        # Position: Centre ou Haut Droite. Requirement says "Centre ou Haut Droite".
        # Let's put it Centered below the box.

        qr_y = box_top - box_height - 5*cm
        qr_size = 4*cm
        p.drawImage(qr_path, (width - qr_size)/2, qr_y, width=qr_size, height=qr_size)

        p.setFont("Helvetica", 8)
        p.drawCentredString(width/2, qr_y - 0.5*cm, "Signature Numérique Inviolable - Ce document est unique")

        # 4. Pied de page (Footer)
        footer_y = 3*cm

        # Prix & Paiement
        p.setFont("Helvetica-Bold", 12)
        price_text = f"{gopass.price} {gopass.currency}"
        p.drawCentredString(width/2, footer_y + 1*cm, f"Prix : {price_text}")

        p.setFont("Helvetica", 10)
        payment_mode = gopass.payment_method or "Mobile Money / Carte Bancaire"
        p.drawCentredString(width/2, footer_y + 0.5*cm, f"Mode de Paiement : {payment_mode}")

        # Disclaimer
        p.setFont("Helvetica-Oblique", 8)
        p.drawCentredString(width/2, footer_y - 0.5*cm, "Valide uniquement pour le vol et la date indiqués. Non remboursable une fois scanné.")

        # Branding
        p.setFont("Helvetica", 6)
        p.drawCentredString(width/2, 1*cm, "Powered by MOA Digital Agency - SGI-GP System")

    p.showPage()
    p.save()

    os.unlink(qr_path)
    buffer.seek(0)

    filename = f"GoPass_{gopass.flight.flight_number}_{gopass.id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
