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
    role = db.Column(db.String(20), default='holder')  # admin, agent, holder
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    passes = db.relationship('Pass', backref='holder', lazy='dynamic', foreign_keys='Pass.holder_id')
    issued_passes = db.relationship('Pass', backref='issuer', lazy='dynamic', foreign_keys='Pass.issued_by')
    
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
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PassType(db.Model):
    __tablename__ = 'pass_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    validity_days = db.Column(db.Integer, default=365)
    color = db.Column(db.String(7), default='#3B82F6')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    passes = db.relationship('Pass', backref='pass_type', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'validity_days': self.validity_days,
            'color': self.color,
            'is_active': self.is_active
        }

class Pass(db.Model):
    __tablename__ = 'passes'
    
    id = db.Column(db.Integer, primary_key=True)
    pass_number = db.Column(db.String(20), unique=True, nullable=False)
    qr_code = db.Column(db.String(255))
    holder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('pass_types.id'), nullable=False)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, expired, suspended, revoked
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    validations = db.relationship('AccessLog', backref='pass_record', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'pass_number': self.pass_number,
            'qr_code': self.qr_code,
            'holder': self.holder.to_dict() if self.holder else None,
            'pass_type': self.pass_type.to_dict() if self.pass_type else None,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status,
            'notes': self.notes
        }

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey('passes.id'), nullable=False)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    validation_time = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20))  # granted, denied
    reason = db.Column(db.String(255))
    
    validator = db.relationship('User', foreign_keys=[validated_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'pass_id': self.pass_id,
            'pass_number': self.pass_record.pass_number if self.pass_record else None,
            'validated_by': self.validator.username if self.validator else None,
            'validation_time': self.validation_time.isoformat() if self.validation_time else None,
            'location': self.location,
            'status': self.status,
            'reason': self.reason
        }

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
