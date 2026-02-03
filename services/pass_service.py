"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for pass_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from models import GoPass, AccessLog
from datetime import datetime, timedelta

class PassService:
    _stats_cache = None
    _stats_cache_expiry = None
    _CACHE_DURATION = timedelta(seconds=60)

    @staticmethod
    def get_statistics():
        now = datetime.now()

        if (PassService._stats_cache is not None and
            PassService._stats_cache_expiry is not None and
            now < PassService._stats_cache_expiry):
            return PassService._stats_cache

        total_passes = GoPass.query.count()
        # Mapping: active -> valid, suspended -> cancelled
        active_passes = GoPass.query.filter_by(status='valid').count()
        expired_passes = GoPass.query.filter_by(status='expired').count()
        suspended_passes = GoPass.query.filter_by(status='cancelled').count()

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_validations = AccessLog.query.filter(AccessLog.validation_time >= today_start).count()

        stats = {
            'total_passes': total_passes,
            'active_passes': active_passes,
            'expired_passes': expired_passes,
            'suspended_passes': suspended_passes,
            'today_validations': today_validations
        }

        PassService._stats_cache = stats
        PassService._stats_cache_expiry = now + PassService._CACHE_DURATION

        return stats
