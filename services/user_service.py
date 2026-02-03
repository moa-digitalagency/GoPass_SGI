"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for user_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from models import db, User
from datetime import datetime, timedelta

class UserService:
    _stats_cache = None
    _stats_cache_timestamp = None
    _CACHE_DURATION = timedelta(minutes=5)

    @classmethod
    def _invalidate_stats_cache(cls):
        cls._stats_cache = None
        cls._stats_cache_timestamp = None

    @staticmethod
    def create_user(username, email, password, first_name, last_name, phone=None, role='holder'):
        if User.query.filter_by(username=username).first():
            raise ValueError("Ce nom d'utilisateur existe déjà")
        
        if User.query.filter_by(email=email).first():
            raise ValueError("Cette adresse email existe déjà")
        
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        UserService._invalidate_stats_cache()
        return user
    
    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        if 'username' in kwargs and kwargs['username'] != user.username:
            if User.query.filter_by(username=kwargs['username']).first():
                raise ValueError("Ce nom d'utilisateur existe déjà")
            user.username = kwargs['username']
        
        if 'email' in kwargs and kwargs['email'] != user.email:
            if User.query.filter_by(email=kwargs['email']).first():
                raise ValueError("Cette adresse email existe déjà")
            user.email = kwargs['email']
        
        if 'first_name' in kwargs:
            user.first_name = kwargs['first_name']
        if 'last_name' in kwargs:
            user.last_name = kwargs['last_name']
        if 'phone' in kwargs:
            user.phone = kwargs['phone']
        if 'role' in kwargs:
            user.role = kwargs['role']
        if 'is_active' in kwargs:
            user.is_active = kwargs['is_active']
        if 'password' in kwargs and kwargs['password']:
            user.set_password(kwargs['password'])
        
        db.session.commit()
        UserService._invalidate_stats_cache()
        return user
    
    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        db.session.delete(user)
        db.session.commit()
        UserService._invalidate_stats_cache()
        return True
    
    @staticmethod
    def get_users_by_role(role):
        return User.query.filter_by(role=role, is_active=True).all()
    
    @staticmethod
    def search_users(query):
        search = f"%{query}%"
        return User.query.filter(
            (User.username.ilike(search)) |
            (User.email.ilike(search)) |
            (User.first_name.ilike(search)) |
            (User.last_name.ilike(search))
        ).all()
    
    @staticmethod
    def get_statistics():
        now = datetime.now()
        if (UserService._stats_cache is not None and
            UserService._stats_cache_timestamp is not None and
            now - UserService._stats_cache_timestamp < UserService._CACHE_DURATION):
            return UserService._stats_cache.copy()

        total_users = User.query.count()
        admins = User.query.filter_by(role='admin').count()
        agents = User.query.filter_by(role='agent').count()
        holders = User.query.filter_by(role='holder').count()
        active_users = User.query.filter_by(is_active=True).count()
        
        stats = {
            'total_users': total_users,
            'admins': admins,
            'agents': agents,
            'holders': holders,
            'active_users': active_users
        }

        UserService._stats_cache = stats
        UserService._stats_cache_timestamp = now

        return stats.copy()
