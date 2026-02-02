from datetime import datetime

def format_date(date, format='%d/%m/%Y'):
    if date:
        return date.strftime(format)
    return ''

def format_datetime(date, format='%d/%m/%Y %H:%M'):
    if date:
        return date.strftime(format)
    return ''

def time_ago(date):
    if not date:
        return ''
    
    now = datetime.utcnow()
    diff = now - date
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "à l'instant"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"il y a {minutes} min"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"il y a {hours}h"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"il y a {days}j"
    else:
        return format_date(date)

def get_status_color(status):
    colors = {
        'active': 'green',
        'expired': 'red',
        'suspended': 'yellow',
        'revoked': 'gray',
        'granted': 'green',
        'denied': 'red'
    }
    return colors.get(status, 'gray')

def get_status_label(status):
    labels = {
        'active': 'Actif',
        'expired': 'Expiré',
        'suspended': 'Suspendu',
        'revoked': 'Révoqué',
        'granted': 'Accordé',
        'denied': 'Refusé'
    }
    return labels.get(status, status)

def get_role_label(role):
    labels = {
        'admin': 'Administrateur',
        'agent': 'Agent',
        'holder': 'Titulaire'
    }
    return labels.get(role, role)
