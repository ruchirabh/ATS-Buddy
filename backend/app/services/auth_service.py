import bcrypt
import jwt
import logging
from datetime import datetime, timedelta, timezone
from flask import current_app
from app.models.user import User
from app.extensions import db

# Configure logger
logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))
    
    @staticmethod
    def generate_token(user_id: int) -> str:
        """Generate JWT token"""
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.now(timezone.utc) + timedelta(days=7),
                'iat': datetime.now(timezone.utc)
            }
            # Ensure SECRET_KEY is a string
            secret_key = str(current_app.config['SECRET_KEY'])
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            return token
        except Exception as e:
            logger.error(f"❌ TOKEN GENERATION ERROR: {str(e)}")
            raise
    
    @classmethod
    def register_user(cls, name: str, email: str, password: str) -> tuple:
        """
        Register a new user
        
        Returns:
            tuple: (user_data, error_message)
        """
        try:
            # Log incoming request (sanitized)
            logger.info(f"📝 REGISTER REQUEST: Creating new user with email: {email}, name: {name}")
            
            # Validate input
            if not name or not email or not password:
                logger.warning(f"❌ REGISTER FAILED: Missing required fields - email: {email}")
                return None, "All fields are required"
            
            # Check if user exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                logger.warning(f"❌ REGISTER FAILED: Email already exists - {email}")
                return None, "Email already registered"
            
            # Create new user
            user = User(
                name=name,
                email=email,
                password_hash=cls.hash_password(password)
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Generate token
            token = cls.generate_token(user.id)
            
            # Get user dict with proper serialization
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'is_active': user.is_active
            }
            
            # Log success
            logger.info(f"✅ REGISTER SUCCESS: User created - ID: {user.id}, Email: {email}")
            
            return {
                'user': user_data,
                'token': token
            }, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ REGISTER ERROR: {str(e)}")
            return None, f"Registration failed: {str(e)}"
    
    @classmethod
    def login_user(cls, email: str, password: str) -> tuple:
        """
        Login user
        
        Returns:
            tuple: (user_data, error_message)
        """
        try:
            # Log incoming request (sanitized)
            logger.info(f"🔐 LOGIN REQUEST: User attempting login with email: {email}")
            
            # Validate input
            if not email or not password:
                logger.warning(f"❌ LOGIN FAILED: Missing credentials - email: {email}")
                return None, "Email and password are required"
            
            # Find user
            user = User.query.filter_by(email=email).first()
            
            if not user:
                logger.warning(f"❌ LOGIN FAILED: User not found - email: {email}")
                return None, "Invalid email or password"
            
            # Verify password
            if not cls.verify_password(password, user.password_hash):
                logger.warning(f"❌ LOGIN FAILED: Invalid password - email: {email}, user_id: {user.id}")
                return None, "Invalid email or password"
            
            # Check if account is active
            if not user.is_active:
                logger.warning(f"❌ LOGIN FAILED: Account deactivated - email: {email}, user_id: {user.id}")
                return None, "Account is deactivated"
            
            # Generate token
            token = cls.generate_token(user.id)
            
            # Update last login (optional)
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            # Get user dict with proper serialization
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'is_active': user.is_active
            }
            
            # Log success
            logger.info(f"✅ LOGIN SUCCESS: User logged in - ID: {user.id}, Email: {email}")
            
            return {
                'user': user_data,
                'token': token
            }, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ LOGIN ERROR: {str(e)}")
            return None, f"Login failed: {str(e)}"