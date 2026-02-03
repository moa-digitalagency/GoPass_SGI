"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for qr_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
import os
from datetime import datetime

class QRService:
    UPLOAD_FOLDER = 'statics/uploads/qrcodes'
    
    @staticmethod
    def ensure_upload_folder():
        if not os.path.exists(QRService.UPLOAD_FOLDER):
            os.makedirs(QRService.UPLOAD_FOLDER)
    
    @staticmethod
    def generate_qr_code(data, filename=None):
        QRService.ensure_upload_folder()
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"qr_{data}_{timestamp}.png"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            fill_color="#1E3A8A",
            back_color="white"
        )
        
        filepath = os.path.join(QRService.UPLOAD_FOLDER, filename)
        img.save(filepath)
        
        return filename
    
    @staticmethod
    def get_qr_path(filename):
        return os.path.join(QRService.UPLOAD_FOLDER, filename)
    
    @staticmethod
    def delete_qr_code(filename):
        filepath = os.path.join(QRService.UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
