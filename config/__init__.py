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

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
