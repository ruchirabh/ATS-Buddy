import google.generativeai as genai
import json
import logging
import time
from typing import Dict, Any, Optional
from flask import current_app
from app.schemas.resume_schemas import AIResumeSchema
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google's Gemini API"""
    
    def __init__(self):
        self.model = None
        self.api_key = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Gemini with API key"""
        try:
            self.api_key = current_app.config.get('GEMINI_API_KEY')
            if not self.api_key:
                logger.warning("⚠️ GEMINI_API_KEY not found in config")
                return
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("✅ Gemini API initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
    
    def generate_resume_json(self, job_description: str, profile_data: Dict[str, Any]) -> tuple:
        """
        Generate resume JSON using Gemini
        
        Returns:
            tuple: (resume_json, error_message)
        """
        try:
            if not self.model:
                logger.warning("⚠️ Gemini not initialized, using mock response")
                return self._get_mock_response(job_description, profile_data), None
            
            # Build prompt
            prompt = self._build_prompt(job_description, profile_data)
            
            # Log prompt (truncated)
            logger.info(f"🤖 Sending prompt to Gemini (length: {len(prompt)} chars)")
            
            # Call Gemini with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    
                    if not response.text:
                        logger.warning(f"⚠️ Gemini returned empty response on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return None, "AI returned empty response"
                    
                    # Parse JSON from response
                    result = self._parse_response(response.text)
                    
                    # Validate against schema
                    validated = AIResumeSchema(**result)
                    
                    logger.info(f"✅ Gemini generated resume successfully (ATS score: {validated.ats_score})")
                    return validated.dict(), None
                    
                except ValidationError as e:
                    logger.error(f"❌ Validation error: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None, f"AI response validation failed: {str(e)}"
                    
                except Exception as e:
                    logger.error(f"❌ Gemini attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise
            
            return None, "All retry attempts failed"
            
        except Exception as e:
            logger.error(f"❌ Resume generation failed: {str(e)}")
            return None, str(e)
    
    def _build_prompt(self, job_description: str, profile_data: Dict[str, Any]) -> str:
        """Build prompt for Gemini"""
        return f"""
        You are an expert ATS (Applicant Tracking System) resume optimizer. 
        Create a tailored, ATS-friendly resume based on the job description and candidate profile.

        JOB DESCRIPTION:
        {job_description}

        CANDIDATE PROFILE:
        {json.dumps(profile_data, indent=2)}

        INSTRUCTIONS:
        1. Create a compelling professional summary (3-4 lines) that highlights relevant experience
        2. List relevant skills (both technical and soft) that match the job description
        3. For each experience, write 2-4 quantified achievements using the STAR method
        4. Keep all factual information from the candidate profile - DO NOT HALLUCINATE
        5. Naturally incorporate keywords from the job description
        6. Calculate an ATS compatibility score (0-100) based on keyword match
        7. Format dates consistently (e.g., "Jan 2020 - Present" or "2019 - 2022")

        IMPORTANT RULES:
        - NEVER add fake experience or education
        - NEVER change company names, job titles, or institutions
        - Use the candidate's actual skills, just rephrase them to match the job
        - Quantify achievements with numbers where possible (%, $, time saved, etc.)
        - The ATS score should reflect how well the resume matches the job description

        OUTPUT MUST BE VALID JSON WITH THIS EXACT STRUCTURE:
        {{
            "summary": "string - professional summary",
            "skills": ["skill1", "skill2", ...],
            "experience": [
                {{
                    "company": "string",
                    "title": "string",
                    "dates": "string",
                    "achievements": ["achievement1", "achievement2", ...]
                }}
            ],
            "education": [
                {{
                    "institution": "string",
                    "degree": "string",
                    "dates": "string",
                    "details": "string (optional)"
                }}
            ],
            "certifications": ["cert1", "cert2", ...],
            "ats_keywords": ["keyword1", "keyword2", ...],
            "ats_score": 85
        }}

        Return ONLY the JSON, no additional text or explanation.
        """
    
    def _parse_response(self, text: str) -> Dict:
        """Parse Gemini response to extract JSON"""
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        # Parse JSON
        return json.loads(text.strip())
    
    def _get_mock_response(self, job_description: str, profile_data: Dict) -> Dict:
        """Mock response for development/fallback"""
        logger.info("📋 Using mock resume response")
        
        # Extract some info from profile
        skills = []
        if profile_data.get('skills'):
            skills = [s['name'] for s in profile_data['skills'][:8]]
        else:
            skills = ["Python", "JavaScript", "React", "Flask", "SQL", "Git"]
        
        return {
            "summary": "Experienced software engineer with a proven track record of delivering scalable solutions. Passionate about clean code and mentoring junior developers. Seeking to leverage technical expertise in a challenging role.",
            "skills": skills,
            "experience": [
                {
                    "company": exp['company'],
                    "title": exp['title'],
                    "dates": f"{exp['start_date']} - {exp.get('end_date', 'Present')}",
                    "achievements": [
                        "Led development of key features resulting in 30% user engagement increase",
                        "Improved application performance by 40% through code optimization",
                        "Mentored 3 junior developers who were promoted within a year"
                    ]
                } for exp in profile_data.get('experience', [])[:2]
            ] or [{
                "company": "Example Corp",
                "title": "Software Engineer",
                "dates": "2020 - Present",
                "achievements": [
                    "Developed RESTful APIs serving 100K+ daily users",
                    "Implemented CI/CD pipeline reducing deployment time by 50%"
                ]
            }],
            "education": [
                {
                    "institution": edu['institution'],
                    "degree": edu['degree'],
                    "dates": f"{edu['start_date']} - {edu.get('end_date', 'Present')}",
                    "details": edu.get('description', '')
                } for edu in profile_data.get('education', [])[:1]
            ] or [{
                "institution": "University of Technology",
                "degree": "B.S. Computer Science",
                "dates": "2014 - 2018",
                "details": "GPA: 3.8/4.0"
            }],
            "certifications": [c['name'] for c in profile_data.get('certificates', [])[:3]],
            "ats_keywords": ["full-stack", "microservices", "API", "Python", "Agile"],
            "ats_score": 82
        }

# Singleton instance
gemini_service = GeminiService()