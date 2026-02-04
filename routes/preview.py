from flask import Blueprint, render_template
import qrcode
import io
import base64
from datetime import datetime

preview_bp = Blueprint('preview', __name__, url_prefix='/preview')

class MockFlight:
    def __init__(self):
        self.flight_number = 'AF123'
        self.departure_time = datetime(2023, 10, 25, 14, 30)
        self.departure_airport = 'FIH'
        self.arrival_airport = 'CDG'
        self.airline = 'AIR FRANCE'

class MockUser:
    def __init__(self):
        self.username = 'AGENT_007'

class MockGoPass:
    def __init__(self):
        self.flight = MockFlight()
        self.passenger_name = 'JEAN DUPONT'
        self.status = 'valide'
        self.price = 50.0
        self.currency = 'USD'
        self.payment_method = 'Airtel Money'
        self.payment_ref = 'PAY-12345678'
        self.token = 'a1b2c3d4e5f6g7h8i9j0'
        self.sold_by = '101'
        self.seller = MockUser()
        self.issue_date = datetime.now()

@preview_bp.route('/ticket/a4')
def ticket_a4():
    gopass = MockGoPass()

    # Generate QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("MOCK_DATA_FOR_PREVIEW")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode()

    return render_template('tickets/ticket_a4.html', gopass=gopass, qr_code=qr_code)

@preview_bp.route('/ticket/thermal')
def ticket_thermal():
    gopass = MockGoPass()

    # Generate QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("MOCK_DATA_FOR_PREVIEW")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode()

    return render_template('tickets/ticket_thermal.html', gopass=gopass, qr_code=qr_code)
