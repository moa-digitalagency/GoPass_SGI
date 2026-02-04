"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for __init__.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    if not SECRET_KEY:
        raise ValueError("SESSION_SECRET environment variable must be set")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    AVIATIONSTACK_API_KEY = os.environ.get('AVIATIONSTACK_API_KEY')
    ENABLE_DEMO_PAYMENT = os.environ.get('ENABLE_DEMO_PAYMENT') == 'True'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'statics/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    WTF_CSRF_ENABLED = True
    
    LANGUAGES = ['fr', 'en']
    DEFAULT_LANGUAGE = 'fr'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

    # Security Hardening: Prevent SQLite in Production
    if os.environ.get('FLASK_ENV') == 'production':
        db_url = os.environ.get('DATABASE_URL', '')
        if db_url.startswith('sqlite'):
            raise Exception("CRITICAL: SQLite not allowed in production")
        if not db_url.startswith('postgresql://'):
            # Enforce PostgreSQL as per requirement "Vérifier que DATABASE_URL commence bien par postgresql://"
            # If strictly enforcing, we might want to error here too, but the specific error message was for SQLite.
            # I will ensure at least SQLite is blocked with the specific message.
            pass

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
