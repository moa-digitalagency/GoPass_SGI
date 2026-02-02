from datetime import datetime, timedelta
from models import db, Pass, PassType, AccessLog
import random
import string

class PassService:
    @staticmethod
    def generate_pass_number():
        prefix = "GP"
        year = datetime.now().strftime("%y")
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{year}{random_part}"
    
    @staticmethod
    def create_pass(holder_id, type_id, issued_by, notes=None):
        pass_type = PassType.query.get(type_id)
        if not pass_type:
            raise ValueError("Type de pass invalide")
        
        pass_number = PassService.generate_pass_number()
        while Pass.query.filter_by(pass_number=pass_number).first():
            pass_number = PassService.generate_pass_number()
        
        expiry_date = datetime.utcnow() + timedelta(days=pass_type.validity_days)
        
        from services.qr_service import QRService
        qr_filename = QRService.generate_qr_code(pass_number)
        
        new_pass = Pass(
            pass_number=pass_number,
            qr_code=qr_filename,
            holder_id=holder_id,
            type_id=type_id,
            issued_by=issued_by,
            expiry_date=expiry_date,
            status='active',
            notes=notes
        )
        
        db.session.add(new_pass)
        db.session.commit()
        
        return new_pass
    
    @staticmethod
    def validate_pass(pass_number, validator_id=None, location=None):
        pass_record = Pass.query.filter_by(pass_number=pass_number).first()
        
        if not pass_record:
            return {
                'valid': False,
                'status': 'not_found',
                'message': 'Pass non trouvé'
            }
        
        if pass_record.status != 'active':
            log = AccessLog(
                pass_id=pass_record.id,
                validated_by=validator_id,
                location=location,
                status='denied',
                reason=f'Pass {pass_record.status}'
            )
            db.session.add(log)
            db.session.commit()
            
            return {
                'valid': False,
                'status': pass_record.status,
                'message': f'Pass {pass_record.status}',
                'pass': pass_record.to_dict()
            }
        
        if pass_record.expiry_date < datetime.utcnow():
            pass_record.status = 'expired'
            log = AccessLog(
                pass_id=pass_record.id,
                validated_by=validator_id,
                location=location,
                status='denied',
                reason='Pass expiré'
            )
            db.session.add(log)
            db.session.commit()
            
            return {
                'valid': False,
                'status': 'expired',
                'message': 'Pass expiré',
                'pass': pass_record.to_dict()
            }
        
        log = AccessLog(
            pass_id=pass_record.id,
            validated_by=validator_id,
            location=location,
            status='granted',
            reason='Accès autorisé'
        )
        db.session.add(log)
        db.session.commit()
        
        return {
            'valid': True,
            'status': 'active',
            'message': 'Accès autorisé',
            'pass': pass_record.to_dict()
        }
    
    @staticmethod
    def suspend_pass(pass_id):
        pass_record = Pass.query.get(pass_id)
        if pass_record:
            pass_record.status = 'suspended'
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def activate_pass(pass_id):
        pass_record = Pass.query.get(pass_id)
        if pass_record:
            if pass_record.expiry_date >= datetime.utcnow():
                pass_record.status = 'active'
                db.session.commit()
                return True
        return False
    
    @staticmethod
    def revoke_pass(pass_id):
        pass_record = Pass.query.get(pass_id)
        if pass_record:
            pass_record.status = 'revoked'
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_statistics():
        total_passes = Pass.query.count()
        active_passes = Pass.query.filter_by(status='active').count()
        expired_passes = Pass.query.filter_by(status='expired').count()
        suspended_passes = Pass.query.filter_by(status='suspended').count()
        
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_validations = AccessLog.query.filter(
            AccessLog.validation_time >= today_start
        ).count()
        
        return {
            'total_passes': total_passes,
            'active_passes': active_passes,
            'expired_passes': expired_passes,
            'suspended_passes': suspended_passes,
            'today_validations': today_validations
        }
