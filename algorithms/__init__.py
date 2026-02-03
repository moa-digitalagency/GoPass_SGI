"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for __init__.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

"""
Algorithms module for GO-PASS SGI-GP
Contains business logic algorithms for pass management
"""

from datetime import datetime, timedelta

def calculate_pass_validity(issue_date, validity_days):
    """Calculate expiry date based on issue date and validity period"""
    if isinstance(issue_date, str):
        issue_date = datetime.fromisoformat(issue_date)
    return issue_date + timedelta(days=validity_days)

def is_pass_valid(expiry_date, status):
    """Check if a pass is currently valid"""
    if status != 'active':
        return False
    if isinstance(expiry_date, str):
        expiry_date = datetime.fromisoformat(expiry_date)
    return expiry_date >= datetime.utcnow()

def calculate_usage_statistics(validations):
    """Calculate usage statistics from validation logs"""
    if not validations:
        return {
            'total': 0,
            'granted': 0,
            'denied': 0,
            'success_rate': 0
        }
    
    total = len(validations)
    granted = sum(1 for v in validations if v.status == 'granted')
    denied = total - granted
    
    return {
        'total': total,
        'granted': granted,
        'denied': denied,
        'success_rate': round((granted / total) * 100, 2) if total > 0 else 0
    }

def generate_pass_report(passes, start_date=None, end_date=None):
    """Generate statistics report for passes"""
    if start_date:
        passes = [p for p in passes if p.created_at >= start_date]
    if end_date:
        passes = [p for p in passes if p.created_at <= end_date]
    
    total = len(passes)
    by_status = {}
    by_type = {}
    
    for p in passes:
        by_status[p.status] = by_status.get(p.status, 0) + 1
        type_name = p.pass_type.name if p.pass_type else 'Unknown'
        by_type[type_name] = by_type.get(type_name, 0) + 1
    
    return {
        'total': total,
        'by_status': by_status,
        'by_type': by_type
    }
