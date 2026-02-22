from flask import Blueprint, request, jsonify
import logging
import traceback
from app.services.auth_service import AuthService

# Configure logger
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint
    Expected payload: { "name": "John Doe", "email": "john@example.com", "password": "secret123" }
    """
    try:
        # Log raw request
        logger.info("📥 INCOMING REQUEST: POST /api/auth/register")
        
        # Check if request has JSON
        if not request.is_json:
            logger.warning("❌ REGISTER FAILED: Request is not JSON")
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Log payload (without password for security)
        safe_payload = {**data} if data else {}
        if 'password' in safe_payload:
            safe_payload['password'] = '********'
        logger.info(f"📦 REQUEST PAYLOAD: {safe_payload}")
        
        # Validate required fields
        if not data:
            logger.warning("❌ REGISTER FAILED: Empty request body")
            return jsonify({
                'success': False,
                'error': 'Request body cannot be empty'
            }), 400
            
        if not data.get('name'):
            logger.warning("❌ REGISTER FAILED: Missing name field")
            return jsonify({
                'success': False,
                'error': 'name is required'
            }), 400
            
        if not data.get('email'):
            logger.warning("❌ REGISTER FAILED: Missing email field")
            return jsonify({
                'success': False,
                'error': 'email is required'
            }), 400
            
        if not data.get('password'):
            logger.warning("❌ REGISTER FAILED: Missing password field")
            return jsonify({
                'success': False,
                'error': 'password is required'
            }), 400
        
        # Call service
        result, error = AuthService.register_user(
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            password=data['password']
        )
        
        if error:
            logger.warning(f"❌ REGISTER FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # Log response
        logger.info(f"📤 RESPONSE: Registration successful for user {result['user']['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'data': result
        }), 201
        
    except Exception as e:
        logger.error(f"❌ REGISTER ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    Expected payload: { "email": "john@example.com", "password": "secret123" }
    """
    try:
        # Log raw request
        logger.info("📥 INCOMING REQUEST: POST /api/auth/login")
        
        # Check if request has JSON
        if not request.is_json:
            logger.warning("❌ LOGIN FAILED: Request is not JSON")
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Log payload (without password)
        safe_payload = {**data} if data else {}
        if 'password' in safe_payload:
            safe_payload['password'] = '********'
        logger.info(f"📦 REQUEST PAYLOAD: {safe_payload}")
        
        # Validate required fields
        if not data:
            logger.warning("❌ LOGIN FAILED: Empty request body")
            return jsonify({
                'success': False,
                'error': 'Request body cannot be empty'
            }), 400
            
        if not data.get('email'):
            logger.warning("❌ LOGIN FAILED: Missing email field")
            return jsonify({
                'success': False,
                'error': 'email is required'
            }), 400
            
        if not data.get('password'):
            logger.warning("❌ LOGIN FAILED: Missing password field")
            return jsonify({
                'success': False,
                'error': 'password is required'
            }), 400
        
        # Call service
        result, error = AuthService.login_user(
            email=data['email'].strip().lower(),
            password=data['password']
        )
        
        if error:
            logger.warning(f"❌ LOGIN FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 401
        
        # Log response
        logger.info(f"📤 RESPONSE: Login successful for user {result['user']['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"❌ LOGIN ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500