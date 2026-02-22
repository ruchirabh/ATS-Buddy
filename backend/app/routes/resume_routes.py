from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import traceback
import os

from app.schemas.resume_schemas import ResumeGenerationRequestSchema
from app.services.resume_service import resume_service
from pydantic import ValidationError

logger = logging.getLogger(__name__)

resume_bp = Blueprint('resume', __name__, url_prefix='/api/resumes')

# ============================================
# Profile Management
# ============================================

@resume_bp.route('/profile', methods=['POST', 'PUT'])
@jwt_required()
def save_profile():
    """Save or update user profile"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"📥 INCOMING REQUEST: {request.method} /api/resumes/profile - User: {user_id}")
        
        # Check if request has JSON
        if not request.is_json:
            logger.warning("❌ PROFILE FAILED: Request is not JSON")
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        logger.info(f"📦 REQUEST PAYLOAD: Profile data received")
        
        # Validate profile data using Pydantic
        try:
            from app.schemas.resume_schemas import UserProfileSchema
            validated_profile = UserProfileSchema(**data)
        except ValidationError as e:
            logger.warning(f"❌ PROFILE VALIDATION FAILED: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': e.errors()
            }), 400
        
        # Save profile
        profile, error = resume_service.save_user_profile(
            user_id=user_id,
            profile_data=validated_profile.dict()
        )
        
        if error:
            logger.warning(f"❌ PROFILE SAVE FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        logger.info(f"📤 RESPONSE: Profile saved successfully for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile saved successfully',
            'data': profile.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ PROFILE ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"📥 INCOMING REQUEST: GET /api/resumes/profile - User: {user_id}")
        
        profile, error = resume_service.get_user_profile(user_id)
        
        if error:
            logger.warning(f"❌ PROFILE FETCH FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        logger.info(f"📤 RESPONSE: Profile fetched for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': profile.to_dict() if profile else None
        }), 200
        
    except Exception as e:
        logger.error(f"❌ PROFILE FETCH ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# ============================================
# Resume Generation
# ============================================

@resume_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_resume():
    """Generate a new resume"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"📥 INCOMING REQUEST: POST /api/resumes/generate - User: {user_id}")
        
        # Check if request has JSON
        if not request.is_json:
            logger.warning("❌ GENERATE FAILED: Request is not JSON")
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Log payload summary (not full data to avoid huge logs)
        logger.info(f"📦 REQUEST: Resume generation requested - JD length: {len(data.get('job_description', ''))}")
        
        # Validate request
        try:
            validated = ResumeGenerationRequestSchema(**data)
        except ValidationError as e:
            logger.warning(f"❌ VALIDATION FAILED: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': e.errors()
            }), 400
        
        # Create resume job
        resume, error = resume_service.create_resume_job(
            user_id=user_id,
            job_description=validated.job_description,
            profile_data=validated.profile_data.dict()
        )
        
        if error:
            logger.warning(f"❌ JOB CREATION FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # Process generation (in production, this would be a background job)
        # For simplicity, we'll do it synchronously
        processed_resume, error = resume_service.process_resume_generation(resume.id)
        
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'data': {'resume_id': resume.id}
            }), 500
        
        logger.info(f"📤 RESPONSE: Resume generated successfully - ID: {resume.id}")
        
        return jsonify({
            'success': True,
            'message': 'Resume generated successfully',
            'data': processed_resume.to_dict_full()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ GENERATE ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# ============================================
# Resume Download & History
# ============================================

@resume_bp.route('/download/<int:resume_id>', methods=['GET'])
@jwt_required()
def download_resume(resume_id):
    """Download generated resume PDF"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"📥 INCOMING REQUEST: GET /api/resumes/download/{resume_id} - User: {user_id}")
        
        # Get resume with ownership check
        resume, error = resume_service.get_resume_by_id(resume_id, user_id)
        
        if error:
            logger.warning(f"❌ DOWNLOAD FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 404
        
        if resume.status != 'completed':
            logger.warning(f"❌ DOWNLOAD FAILED: Resume not ready - Status: {resume.status}")
            return jsonify({
                'success': False,
                'error': f'Resume is {resume.status}, not ready for download'
            }), 400
        
        if not resume.pdf_path or not os.path.exists(resume.pdf_path):
            logger.warning(f"❌ DOWNLOAD FAILED: PDF file not found")
            return jsonify({
                'success': False,
                'error': 'PDF file not found'
            }), 404
        
        logger.info(f"📤 RESPONSE: Sending PDF file for resume {resume_id}")
        
        return send_file(
            resume.pdf_path,
            as_attachment=True,
            download_name=f"resume_{resume_id}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"❌ DOWNLOAD ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_bp.route('/history', methods=['GET'])
@jwt_required()
def get_resume_history():
    """Get user's resume generation history"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"📥 INCOMING REQUEST: GET /api/resumes/history - User: {user_id}")
        
        resumes, error = resume_service.get_user_resumes(user_id)
        
        if error:
            logger.warning(f"❌ HISTORY FETCH FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        logger.info(f"📤 RESPONSE: History fetched - {len(resumes)} resumes")
        
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in resumes]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ HISTORY ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_bp.route('/<int:resume_id>', methods=['GET'])
@jwt_required()
def get_resume_details(resume_id):
    """Get detailed resume information"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"📥 INCOMING REQUEST: GET /api/resumes/{resume_id} - User: {user_id}")
        
        resume, error = resume_service.get_resume_by_id(resume_id, user_id)
        
        if error:
            logger.warning(f"❌ DETAILS FETCH FAILED: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 404
        
        logger.info(f"📤 RESPONSE: Details fetched for resume {resume_id}")
        
        return jsonify({
            'success': True,
            'data': resume.to_dict_full()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ DETAILS ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500