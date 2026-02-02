from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='holder')  # admin, agent, holder, controller
    location = db.Column(db.String(50)) # Assigned airport code e.g. FIH
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scanned_gopasses = db.relationship('GoPass', backref='scanner', lazy='dynamic', foreign_keys='GoPass.scanned_by')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PassType(db.Model):
    __tablename__ = 'pass_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), default='#000000')
    is_active = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'is_active': self.is_active,
            'price': self.price
        }

class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), nullable=False) # e.g. CAA-BU1421
    airline = db.Column(db.String(100), nullable=False)
    departure_airport = db.Column(db.String(10), nullable=False)
    arrival_airport = db.Column(db.String(10), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='scheduled') # scheduled, active, landed, cancelled
    source = db.Column(db.String(20), default='manual') # api, manual
    capacity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    gopasses = db.relationship('GoPass', backref='flight', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'airline': self.airline,
            'departure_airport': self.departure_airport,
            'arrival_airport': self.arrival_airport,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'status': self.status,
            'source': self.source,
            'capacity': self.capacity
        }

class GoPass(db.Model):
    __tablename__ = 'gopasses'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False) # The QR content (hashed/signed)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('pass_types.id'))
    holder_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    pass_type = db.relationship('PassType')
    holder = db.relationship('User', foreign_keys=[holder_id])
    
    # Passenger Details
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_passport = db.Column(db.String(50), nullable=False)
    
    # Payment Details
    price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')
    payment_status = db.Column(db.String(20), default='pending') # pending, paid
    payment_ref = db.Column(db.String(100))
    
    # Usage Status
    status = db.Column(db.String(20), default='valid') # valid, consumed, expired, cancelled

    # Scan Details
    scanned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    scan_date = db.Column(db.DateTime)
    scan_location = db.Column(db.String(50))
    
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'flight': self.flight.to_dict() if self.flight else None,
            'passenger_name': self.passenger_name,
            'passenger_passport': self.passenger_passport,
            'status': self.status,
            'payment_status': self.payment_status,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None
        }

class AccessLog(db.Model):
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey('gopasses.id'))
    validator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    validation_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='valid')

    pass_record = db.relationship('GoPass')
    validator = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'validation_time': self.validation_time.isoformat() if self.validation_time else None,
            'pass_record': self.pass_record.to_dict() if self.pass_record else None,
            'validator': self.validator.to_dict() if self.validator else None,
            'status': self.status
        }

# Keeping these for backward compatibility if needed, or we can drop them later.
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id])
