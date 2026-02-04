"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for public.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from services import FlightService, GoPassService, MockPaymentService
from models import PaymentGateway, GoPass, db
from datetime import datetime
import io
import qrcode
import base64
import json
import uuid

public_bp = Blueprint('public', __name__)

@public_bp.route('/set-lang/<lang>')
def set_language(lang):
    if lang in ['fr', 'en']:
        from flask import session
        session['lang'] = lang
    return redirect(request.referrer or url_for('public.index'))

@public_bp.route('/')
def index():
    return render_template('public/index.html', now=datetime.now())

@public_bp.route('/aide')
def aide():
    return render_template('public/aide.html', now=datetime.now())

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

    # Check active payment methods
    gateways = PaymentGateway.query.all()
    stripe_active = any(g.provider == 'STRIPE' and g.is_active for g in gateways)
    mobile_active = any(g.provider == 'MOBILE_MONEY_AGGREGATOR' and g.is_active for g in gateways)

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')

        if payment_method == 'STRIPE' and not stripe_active:
             flash("Le paiement par Stripe est désactivé.", "danger")
             return redirect(url_for('public.checkout', flight_id=flight_id))

        if payment_method == 'MOBILE_MONEY' and not mobile_active:
             flash("Le paiement par Mobile Money est désactivé.", "danger")
             return redirect(url_for('public.checkout', flight_id=flight_id))

        # Multi-pax parsing
        passenger_names = request.form.getlist('passenger_name[]')
        passports = request.form.getlist('passport[]')
        doc_types = request.form.getlist('document_type[]')

        if not passenger_names:
            # Fallback for single pax (legacy form)
            p_name = request.form.get('passenger_name')
            if p_name:
                passenger_names = [p_name]
                passports = [request.form.get('passport')]
                doc_types = [request.form.get('document_type', 'Passeport')]

        if not passenger_names:
             flash("Veuillez ajouter au moins un passager.", "danger")
             return redirect(url_for('public.checkout', flight_id=flight_id))

        batch_ref = None
        enable_demo_payment = current_app.config.get('ENABLE_DEMO_PAYMENT', False)

        if enable_demo_payment:
            mock_data = {
                'card_number': request.form.get('card_number'),
                'mobile_number': request.form.get('mobile_number')
            }
            result = MockPaymentService.process_payment(payment_method, mock_data)

            if not result['success']:
                flash(result['message'], "danger")
                return redirect(url_for('public.checkout', flight_id=flight_id))

            batch_ref = result['transaction_id']
        else:
            # Generate a batch Payment Ref
            # Using a mock Stripe-like ID if Stripe, else generic
            ref_prefix = "ch_" if payment_method == 'STRIPE' else "WEB-"
            batch_ref = f"{ref_prefix}{uuid.uuid4().hex[:12]}" if payment_method == 'STRIPE' else f"WEB-{uuid.uuid4().hex[:8].upper()}"

        source_metadata = {
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "platform": "Web Store"
        }

        try:
            for i in range(len(passenger_names)):
                name = passenger_names[i]
                passport = passports[i]
                dtype = doc_types[i] if i < len(doc_types) else 'Passeport'

                if name and passport:
                    GoPassService.create_gopass(
                        flight_id=flight.id,
                        passenger_name=name,
                        passenger_passport=passport,
                        passenger_document_type=dtype,
                        payment_method=payment_method,
                        payment_ref=batch_ref,
                        sales_channel='WEB',
                        payment_reference=batch_ref,
                        source_metadata=source_metadata,
                        commit=False
                    )

            db.session.commit()
            return redirect(url_for('public.confirmation_batch', ref=batch_ref))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating passes: {e}")
            flash("Une erreur est survenue lors de la création des billets.", "danger")
            return redirect(url_for('public.checkout', flight_id=flight_id))

    enable_demo_payment = current_app.config.get('ENABLE_DEMO_PAYMENT', False)
    return render_template('public/checkout.html', flight=flight, stripe_active=stripe_active, mobile_active=mobile_active, enable_demo_payment=enable_demo_payment)

@public_bp.route('/confirmation/batch/<ref>')
def confirmation_batch(ref):
    gopasses = GoPass.query.filter_by(payment_ref=ref).all()
    if not gopasses:
        flash("Aucun billet trouvé.", "warning")
        return redirect(url_for('public.index'))

    passes_data = []
    for gp in gopasses:
        qr_payload = {
            "id_billet": gp.id,
            "vol": gp.flight.flight_number,
            "date": gp.flight.departure_time.strftime('%Y-%m-%d'),
            "hash_signature": gp.token
        }
        qr_data = json.dumps(qr_payload)

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        passes_data.append({'gopass': gp, 'qr_base64': qr_base64})

    return render_template('public/confirmation.html', passes=passes_data, batch_ref=ref)

@public_bp.route('/confirmation/<int:id>')
def confirmation(id):
    # Backward compatibility redirect
    gopass = GoPassService.get_gopass(id)
    if not gopass:
        return redirect(url_for('public.index'))
    return redirect(url_for('public.confirmation_batch', ref=gopass.payment_ref))

@public_bp.route('/download/<int:id>')
def download_pdf(id):
    gopass = GoPassService.get_gopass(id)
    if not gopass:
        return "Pass non trouvé", 404

    fmt = request.args.get('format', 'a4')
    from flask import session
    lang = session.get('lang', 'fr')
    pdf_bytes = GoPassService.generate_pdf_bytes(gopass, fmt=fmt, lang=lang)

    buffer = io.BytesIO(pdf_bytes)
    filename = f"GoPass_{gopass.flight.flight_number}_{gopass.id}.pdf"

    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@public_bp.route('/download/batch/<ref>')
def download_batch(ref):
    gopasses = GoPass.query.filter_by(payment_ref=ref).all()
    if not gopasses:
        return "Billets introuvables", 404

    from flask import session
    lang = session.get('lang', 'fr')
    pdf_bytes = GoPassService.generate_bulk_pdf(gopasses, lang=lang)

    buffer = io.BytesIO(pdf_bytes)
    filename = f"GoPasses_{ref}.pdf"

    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
