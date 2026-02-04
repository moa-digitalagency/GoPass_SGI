"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for gopass_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from models import db, GoPass, Flight, User, AccessLog, AppConfig, Transaction
from datetime import datetime
import json
import hashlib
import uuid
from services.qr_service import QRService
import io
import qrcode
import tempfile
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from flask import current_app
from utils.i18n import get_text

class GoPassService:
    @staticmethod
    def create_gopass(flight_id, passenger_name, passenger_passport, passenger_document_type='Passeport', price=50.0, currency='USD', payment_ref=None, payment_method='Cash', sold_by=None, sales_channel='counter', verification_source='manual', flight_details=None, commit=True, transaction_id=None):
        flight = Flight.query.get(flight_id)
        if not flight:
            raise ValueError("Vol invalide")

        # Generate unique token
        token_data = {
            'flight_id': flight_id,
            'passport': passenger_passport,
            'timestamp': datetime.utcnow().isoformat(),
            'nonce': str(uuid.uuid4())
        }
        token_string = json.dumps(token_data, sort_keys=True)
        token_hash = hashlib.sha256(token_string.encode()).hexdigest()

        # Create Transaction Record for Audit
        # Check if sold_by is valid (it should be an ID)
        if not transaction_id and sold_by:
            transaction = Transaction(
                agent_id=sold_by,
                amount_collected=price,
                currency=currency,
                payment_method=payment_method,
                provider_ref=payment_ref or f"PAY-{uuid.uuid4().hex[:8].upper()}",
                status='completed',
                verification_source=verification_source,
                flight_details=flight_details
            )
            db.session.add(transaction)
            db.session.flush() # Generate ID
            transaction_id = transaction.id

        # In a real system, we would sign this with a private key.
        # For now, the hash acts as the secure token stored in DB.

        gopass = GoPass(
            token=token_hash,
            flight_id=flight_id,
            passenger_name=passenger_name,
            passenger_passport=passenger_passport,
            passenger_document_type=passenger_document_type,
            price=price,
            currency=currency,
            payment_status='paid', # Assuming payment success for now
            payment_ref=payment_ref or f"PAY-{uuid.uuid4().hex[:8].upper()}",
            payment_method=payment_method,
            sold_by=sold_by,
            sales_channel=sales_channel,
            status='valid',
            transaction_id=transaction_id
        )

        db.session.add(gopass)
        if commit:
            db.session.commit()

        return gopass

    @staticmethod
    def get_gopass(gopass_id):
        return GoPass.query.get(gopass_id)

    @staticmethod
    def get_gopass_by_token(token):
        return GoPass.query.filter_by(token=token).first()

    @staticmethod
    def validate_gopass(token, flight_id, agent_id, location):
        """
        Logic for validation (Cas A, B, C, D)
        """
        if not token or len(token) > 4096:
            return {
                'status': 'error',
                'code': 'INVALID_TOKEN',
                'message': 'TOKEN INVALIDE',
                'color': 'red',
                'data': None
            }

        # Try to parse token as JSON if it matches the new format
        lookup_token = token
        try:
            if token and token.strip().startswith('{'):
                token_data = json.loads(token)
                if 'hash_signature' in token_data:
                    lookup_token = token_data['hash_signature']
        except Exception:
            pass # Use original token string

        # Check if flight is closed
        target_flight = Flight.query.get(flight_id)
        if target_flight and target_flight.status == 'closed':
             return {
                'status': 'error',
                'code': 'FLIGHT_CLOSED',
                'message': 'VOL CLÔTURÉ',
                'color': 'red',
                'data': None
            }

        try:
            # Locking row to prevent race conditions (double scan)
            gopass = GoPass.query.filter_by(token=lookup_token).with_for_update().first()
        except Exception:
            # Fallback for databases not supporting row-level locking (e.g. older SQLite)
            gopass = GoPass.query.filter_by(token=lookup_token).first()

        # Cas D: Invalide (Document non reconnu)
        if not gopass:
            # Log attempt even if invalid doc (if possible to track, but pass_id is null)
            # We might want to track who tried to scan it.
            # But AccessLog expects pass_id. If we want to log invalid docs, AccessLog might need to be nullable or use a dummy.
            # For now, let's assume we can't log "INVALID" easily in AccessLog if pass_id is FK.
            # Or we can create a record without pass_id if the model allows.
            # AccessLog.pass_id is nullable (default SQLAlchemy behavior unless nullable=False).
            # models/__init__.py: pass_id = db.Column(db.Integer, db.ForeignKey('gopasses.id'))
            # It is nullable by default.

            log = AccessLog(
                pass_id=None,
                validator_id=agent_id,
                validation_time=datetime.utcnow(),
                status='INVALID'
            )
            db.session.add(log)
            db.session.commit()

            return {
                'status': 'error',
                'code': 'INVALID',
                'message': 'DOCUMENT NON RECONNU',
                'color': 'red',
                'data': None
            }

        # Cas B: Déjà utilisé
        if gopass.status == 'consumed':
            log = AccessLog(
                pass_id=gopass.id,
                validator_id=agent_id,
                validation_time=datetime.utcnow(),
                status='ALREADY_SCANNED'
            )
            db.session.add(log)
            db.session.commit()

            original_scan = {
                'scan_date': gopass.scan_date.strftime('%Y-%m-%d %H:%M:%S') if gopass.scan_date else 'N/A',
                'scanned_by': gopass.scanner.username if gopass.scanner else 'Inconnu',
                'location': gopass.scan_location
            }
            return {
                'status': 'error',
                'code': 'ALREADY_SCANNED',
                'message': 'DÉJÀ SCANNÉ',
                'color': 'red',
                'data': {
                    'passenger': gopass.passenger_name,
                    'flight': gopass.flight.flight_number,
                    'original_scan': original_scan
                }
            }

        # Cas C: Mauvais Vol
        if str(gopass.flight_id) != str(flight_id):
            gopass_date = gopass.flight.departure_time.date()
            target_date = target_flight.departure_time.date() if target_flight else datetime.now().date()

            # Sous-Cas: Date Différente -> ROUGE (Expiré)
            if gopass_date != target_date:
                log = AccessLog(
                    pass_id=gopass.id,
                    validator_id=agent_id,
                    validation_time=datetime.utcnow(),
                    status='EXPIRED'
                )
                db.session.add(log)
                db.session.commit()

                return {
                    'status': 'error',
                    'code': 'EXPIRED',
                    'message': 'BILLET EXPIRÉ',
                    'color': 'red',
                    'data': {
                        'valid_for_date': gopass.flight.departure_time.strftime('%d/%m/%Y'),
                        'expected_date': target_flight.departure_time.strftime('%d/%m/%Y') if target_flight else 'N/A',
                        'flight': gopass.flight.flight_number
                    }
                }

            # Sous-Cas: Même Date, Mauvais Vol -> ORANGE
            log = AccessLog(
                pass_id=gopass.id,
                validator_id=agent_id,
                validation_time=datetime.utcnow(),
                status='WRONG_FLIGHT'
            )
            db.session.add(log)
            db.session.commit()

            return {
                'status': 'warning',
                'code': 'WRONG_FLIGHT',
                'message': 'MAUVAIS VOL',
                'color': 'orange',
                'data': {
                    'valid_for': gopass.flight.flight_number,
                    'date': gopass.flight.departure_time.strftime('%Y-%m-%d')
                }
            }

        # Cas A: Succès
        if gopass.status == 'valid':
            # Mark as consumed
            gopass.status = 'consumed'
            gopass.scanned_by = agent_id
            gopass.scan_date = datetime.utcnow()
            gopass.scan_location = location

            log = AccessLog(
                pass_id=gopass.id,
                validator_id=agent_id,
                validation_time=gopass.scan_date,
                status='VALID'
            )
            db.session.add(log)

            db.session.commit()

            return {
                'status': 'success',
                'code': 'VALID',
                'message': 'VALIDE',
                'color': 'green',
                'data': {
                    'passenger': gopass.passenger_name,
                    'passport': gopass.passenger_passport,
                    'document_type': gopass.passenger_document_type
                }
            }

        return {
            'status': 'error',
            'code': 'UNKNOWN',
            'message': 'ERREUR INCONNUE',
            'color': 'red'
        }

    @staticmethod
    def _draw_gopass_on_canvas(p, gopass, width, height, qr_path, fmt, lang='fr'):
        t = lambda k: get_text(k, lang)

        if fmt == 'thermal':
            # MODULE B: THERMAL TICKET (80mm)

            def draw_centered(text, y, font="Helvetica", size=10):
                p.setFont(font, size)
                text_width = p.stringWidth(text, font, size)
                p.drawString((width - text_width) / 2, y, text)

            y = height - 5 * mm

            # 1. En-tête Compact
            # Logo RVA (Monochrome)
            rva_conf = AppConfig.query.get('logo_rva_url')
            logo_rva = None
            if rva_conf and rva_conf.value:
                # Convert URL to path
                if rva_conf.value.startswith('/static/'):
                    logo_rva = os.path.join(current_app.static_folder, rva_conf.value.replace('/static/', '', 1))

            if not logo_rva or not os.path.exists(logo_rva):
                logo_rva = os.path.join(current_app.static_folder, 'img/logo_rva.png')

            if os.path.exists(logo_rva):
                img_w, img_h = 20*mm, 20*mm
                p.drawImage(logo_rva, (width - img_w)/2, y - img_h, width=img_w, height=img_h)
                y -= (img_h + 2*mm)

            draw_centered("RVA - GO PASS", y, "Helvetica-Bold", 12)
            y -= 4 * mm
            draw_centered(t('ticket_pdf.receipt_title'), y, "Helvetica", 8)
            y -= 6 * mm

            # Separator
            p.setLineWidth(1)
            p.line(2*mm, y, width - 2*mm, y)
            y -= 6 * mm

            # 2. Détails du Vol
            draw_centered(f"{t('ticket_pdf.flight_label')} : {gopass.flight.flight_number}", y, "Helvetica-Bold", 16)
            y -= 6 * mm
            draw_centered(f"{t('ticket_pdf.date_label')} : {gopass.flight.departure_time.strftime('%d/%m/%Y')}", y, "Helvetica-Bold", 10)
            y -= 5 * mm
            draw_centered(f"DEP : {gopass.flight.departure_airport}", y, "Helvetica-Bold", 10)
            y -= 8 * mm

            # 3. Détails Passager
            passenger_name = gopass.passenger_name.upper() if gopass.passenger_name else t('ticket_pdf.passenger_label')
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
            terminal_id = "POS-001" # Placeholder
            issue_time = gopass.issue_date.strftime('%H:%M:%S') if gopass.issue_date else "N/A"

            p.drawString(left_margin, y, f"{t('ticket_pdf.agent_id')} : {agent_name}")
            y -= line_height
            p.drawString(left_margin, y, f"{t('ticket_pdf.terminal')} : {terminal_id}")
            y -= line_height
            p.drawString(left_margin, y, f"{t('ticket_pdf.time')} : {issue_time}")
            y -= line_height
            p.drawString(left_margin, y, f"{t('ticket_pdf.trans')} : {gopass.payment_ref or 'N/A'}")
            y -= line_height
            p.drawString(left_margin, y, f"{t('ticket_pdf.payment')} : {gopass.payment_method or 'CASH'}")
            y -= 8 * mm

            # 6. Pied de Ticket
            draw_centered(t('ticket_pdf.keep_ticket'), y, "Helvetica-Oblique", 7)
            y -= 4 * mm
            draw_centered("www.rva.cd", y, "Helvetica", 8)

        else:
            # MODULE A: A4 PDF (E-GoPass)

            # 1. En-tête (Header)
            # Fetch Logos from Config
            rva_conf = AppConfig.query.get('logo_rva_url')
            logo_rva = None
            if rva_conf and rva_conf.value and rva_conf.value.startswith('/static/'):
                 logo_rva = os.path.join(current_app.static_folder, rva_conf.value.replace('/static/', '', 1))

            if not logo_rva or not os.path.exists(logo_rva):
                logo_rva = os.path.join(current_app.static_folder, 'img/logo_rva.png')

            gopass_conf = AppConfig.query.get('logo_gopass_ticket_url')
            if not gopass_conf or not gopass_conf.value:
                # Fallback to general platform logo if ticket specific one is not set
                gopass_conf = AppConfig.query.get('logo_gopass_url')

            logo_gopass = None
            if gopass_conf and gopass_conf.value and gopass_conf.value.startswith('/static/'):
                 logo_gopass = os.path.join(current_app.static_folder, gopass_conf.value.replace('/static/', '', 1))

            if not logo_gopass or not os.path.exists(logo_gopass):
                logo_gopass = os.path.join(current_app.static_folder, 'img/logo_gopass.png')

            # Logo Gauche: RVA
            if os.path.exists(logo_rva):
                p.drawImage(logo_rva, 2*cm, height - 3.5*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True)

            # Logo Droite: GoPass
            if os.path.exists(logo_gopass):
                p.drawImage(logo_gopass, width - 4.5*cm, height - 3.5*cm, width=2.5*cm, height=2.5*cm, preserveAspectRatio=True)

            # Titre Central
            title_y = height - 2*cm
            p.setFont("Helvetica-Bold", 14)
            p.drawCentredString(width/2, title_y, t('ticket_pdf.header_title'))
            # p.drawCentredString(width/2, title_y - 0.6*cm, "INFRASTRUCTURES AÉROPORTUAIRES (IDEF)") # Included in header_title key usually or split if needed.
            # I merged it in JSON as one line, but PDF draws 2 lines. I should probably split it or use wrap.
            # For simplicity, assuming one line or short title. "Infrastructure Development Fee (IDEF)" fits.

            p.setFont("Helvetica", 10)
            p.drawCentredString(width/2, title_y - 1.5*cm, t('ticket_pdf.subtitle_a4'))

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
            p.drawString(text_x, current_y, t('ticket_pdf.passenger_label'))
            p.setFont("Helvetica", 14)
            p.drawString(text_x + 3*cm, current_y, gopass.passenger_name.upper())

            current_y -= 1.5*cm

            # VOL
            p.setFont("Helvetica-Bold", 10)
            p.drawString(text_x, current_y, t('ticket_pdf.flight_label'))
            p.setFont("Helvetica-Bold", 24)
            p.drawString(text_x + 3*cm, current_y, gopass.flight.flight_number)

            current_y -= 1.5*cm

            # DATE
            p.setFont("Helvetica-Bold", 10)
            p.drawString(text_x, current_y, t('ticket_pdf.date_label'))
            p.setFont("Helvetica", 14)
            date_str = gopass.flight.departure_time.strftime('%d/%m/%Y')
            p.drawString(text_x + 3*cm, current_y, date_str)

            current_y -= 1.5*cm

            # ITINÉRAIRE
            p.setFont("Helvetica-Bold", 10)
            p.drawString(text_x, current_y, t('ticket_pdf.itin_label'))
            p.setFont("Helvetica", 14)
            itin = f"{gopass.flight.departure_airport}  ➔  {gopass.flight.arrival_airport}"
            p.drawString(text_x + 3*cm, current_y, itin)

            # 3. Zone de Sécurité (QR Code)
            qr_y = box_top - box_height - 5*cm
            qr_size = 4*cm
            p.drawImage(qr_path, (width - qr_size)/2, qr_y, width=qr_size, height=qr_size)

            p.setFont("Helvetica", 8)
            p.drawCentredString(width/2, qr_y - 0.5*cm, t('ticket_pdf.security_warning'))

            # 4. Pied de page (Footer)
            footer_y = 3*cm

            # Prix & Paiement
            p.setFont("Helvetica-Bold", 12)
            price_text = f"{gopass.price} {gopass.currency}"
            p.drawCentredString(width/2, footer_y + 1*cm, f"{t('ticket_pdf.price_label')} : {price_text}")

            p.setFont("Helvetica", 10)
            payment_mode = gopass.payment_method or "Mobile Money / Carte Bancaire"
            p.drawCentredString(width/2, footer_y + 0.5*cm, f"{t('ticket_pdf.payment_mode_label')} : {payment_mode}")

            # Disclaimer
            p.setFont("Helvetica-Oblique", 8)
            p.drawCentredString(width/2, footer_y - 0.5*cm, t('ticket_pdf.disclaimer'))

            # Branding
            p.setFont("Helvetica", 6)
            p.drawCentredString(width/2, 1*cm, t('ticket_pdf.powered_by'))


    @staticmethod
    def _create_qr_temp(gopass):
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
            return tmp.name

    @staticmethod
    def generate_pdf_bytes(gopass, fmt='a4', lang='fr'):
        """
        Generates PDF for a GoPass. Returns bytes.
        """
        qr_path = GoPassService._create_qr_temp(gopass)
        buffer = io.BytesIO()

        if fmt == 'thermal':
            width = 80 * mm
            height = 180 * mm
        else:
            width, height = A4

        p = canvas.Canvas(buffer, pagesize=(width, height))
        GoPassService._draw_gopass_on_canvas(p, gopass, width, height, qr_path, fmt, lang)

        p.showPage()
        p.save()

        try:
            os.unlink(qr_path)
        except:
            pass

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_bulk_pdf(gopass_list, lang='fr'):
        """
        Generates a single PDF containing all GoPasses in the list (one per page).
        """
        buffer = io.BytesIO()
        width, height = A4 # Bulk PDF assumes A4 for now
        p = canvas.Canvas(buffer, pagesize=(width, height))

        qr_paths = []

        for gopass in gopass_list:
            qr_path = GoPassService._create_qr_temp(gopass)
            qr_paths.append(qr_path)

            GoPassService._draw_gopass_on_canvas(p, gopass, width, height, qr_path, 'a4', lang)
            p.showPage()

        p.save()

        # Cleanup
        for path in qr_paths:
            try:
                os.unlink(path)
            except:
                pass

        buffer.seek(0)
        return buffer.getvalue()
