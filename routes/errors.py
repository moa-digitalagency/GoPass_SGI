"""
* Nom de l'application : GoPass SGI-GP
 * Description : Error handlers implementation
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from flask import render_template

def register_error_handlers(app):

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html',
                             whatsapp_number=app.config.get('SUPPORT_WHATSAPP'),
                             lead_magnet_link=app.config.get('LEAD_MAGNET_LINK')), 404

    @app.errorhandler(451)
    def unavailable_for_legal_reasons(e):
        return render_template('errors/451.html',
                             whatsapp_number=app.config.get('SUPPORT_WHATSAPP'),
                             lead_magnet_link=app.config.get('LEAD_MAGNET_LINK')), 451

    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html',
                             whatsapp_number=app.config.get('SUPPORT_WHATSAPP'),
                             lead_magnet_link=app.config.get('LEAD_MAGNET_LINK')), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html',
                             whatsapp_number=app.config.get('SUPPORT_WHATSAPP'),
                             lead_magnet_link=app.config.get('LEAD_MAGNET_LINK')), 403
