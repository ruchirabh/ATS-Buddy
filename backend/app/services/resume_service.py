import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import current_app

from app.extensions import db
from app.models.resume import Resume
from app.models.user import User
from app.models.user_profile import UserProfile
from app.services.gemini_service import gemini_service
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)

class ResumeService:
    """Service for handling resume generation workflow"""
    
    @staticmethod
    def save_user_profile(user_id: int, profile_data: Dict[str, Any]) -> tuple:
        """
        Save or update user profile
        
        Returns:
            tuple: (profile, error_message)
        """
        try:
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            
            if profile:
                profile.profile_data = profile_data
                profile.updated_at = datetime.utcnow()
                logger.info(f"📝 Updated profile for user {user_id}")
            else:
                profile = UserProfile(
                    user_id=user_id,
                    profile_data=profile_data
                )
                db.session.add(profile)
                logger.info(f"📝 Created new profile for user {user_id}")
            
            db.session.commit()
            return profile, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Failed to save profile: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def get_user_profile(user_id: int) -> tuple:
        """Get user profile"""
        try:
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            return profile, None
        except Exception as e:
            logger.error(f"❌ Failed to get profile: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def create_resume_job(user_id: int, job_description: str, profile_data: Dict[str, Any]) -> tuple:
        """
        Create a resume generation job
        
        Returns:
            tuple: (resume, error_message)
        """
        try:
            # First save/update profile
            profile, error = ResumeService.save_user_profile(user_id, profile_data)
            if error:
                return None, error
            
            # Create resume record
            resume = Resume(
                user_id=user_id,
                job_description=job_description,
                status='pending'
            )
            
            db.session.add(resume)
            db.session.commit()
            
            logger.info(f"📝 Created resume job {resume.id} for user {user_id}")
            return resume, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Failed to create resume job: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def process_resume_generation(resume_id: int) -> tuple:
        """
        Process resume generation (call AI, generate PDF)
        
        Returns:
            tuple: (resume, error_message)
        """
        try:
            resume = Resume.query.get(resume_id)
            if not resume:
                return None, "Resume not found"
            
            # Update status to processing
            resume.status = 'processing'
            db.session.commit()
            
            # Get user and profile
            user = User.query.get(resume.user_id)
            profile = UserProfile.query.filter_by(user_id=resume.user_id).first()
            
            if not profile:
                resume.status = 'failed'
                resume.error_message = "User profile not found"
                db.session.commit()
                return None, "User profile not found"
            
            # Call Gemini to generate resume JSON
            logger.info(f"🤖 Calling Gemini for resume {resume_id}")
            resume_json, error = gemini_service.generate_resume_json(
                job_description=resume.job_description,
                profile_data=profile.profile_data
            )
            
            if error:
                resume.status = 'failed'
                resume.error_message = error
                db.session.commit()
                return None, error
            
            # Generate PDF
            logger.info(f"📄 Generating PDF for resume {resume_id}")
            pdf_path = pdf_service.generate_pdf(
                resume_data=resume_json,
                resume_id=resume_id,
                user_name=user.name
            )
            
            # Update resume record
            resume.generated_json = resume_json
            resume.pdf_path = pdf_path
            resume.status = 'completed'
            resume.completed_at = datetime.utcnow()
            
            # Update user stats
            user = User.query.get(resume.user_id)
            # You could add a counter to User model if needed
            
            db.session.commit()
            
            logger.info(f"✅ Resume {resume_id} generated successfully")
            return resume, None
            
        except Exception as e:
            logger.error(f"❌ Resume processing failed: {str(e)}")
            if resume:
                resume.status = 'failed'
                resume.error_message = str(e)
                db.session.commit()
            return None, str(e)
    
    @staticmethod
    def get_user_resumes(user_id: int, limit: int = 20) -> tuple:
        """Get user's resume history"""
        try:
            resumes = Resume.query.filter_by(user_id=user_id)\
                .order_by(Resume.created_at.desc())\
                .limit(limit)\
                .all()
            return resumes, None
        except Exception as e:
            logger.error(f"❌ Failed to get resumes: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def get_resume_by_id(resume_id: int, user_id: int) -> tuple:
        """Get resume by ID (with ownership check)"""
        try:
            resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
            if not resume:
                return None, "Resume not found"
            return resume, None
        except Exception as e:
            logger.error(f"❌ Failed to get resume: {str(e)}")
            return None, str(e)

# Singleton instance
resume_service = ResumeService()