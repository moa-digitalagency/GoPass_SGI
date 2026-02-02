from models import db, User
from datetime import datetime

class UserService:
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
        return user
    
    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        db.session.delete(user)
        db.session.commit()
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
        total_users = User.query.count()
        admins = User.query.filter_by(role='admin').count()
        agents = User.query.filter_by(role='agent').count()
        holders = User.query.filter_by(role='holder').count()
        active_users = User.query.filter_by(is_active=True).count()
        
        return {
            'total_users': total_users,
            'admins': admins,
            'agents': agents,
            'holders': holders,
            'active_users': active_users
        }
