"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for __init__.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from .auth import auth_bp
from .dashboard import dashboard_bp
from .users import users_bp
from .api import api_bp

__all__ = ['auth_bp', 'dashboard_bp', 'users_bp', 'api_bp']
