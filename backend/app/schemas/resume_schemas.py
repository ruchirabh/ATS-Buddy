from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date

# ============================================
# User Profile Schemas
# ============================================

class EducationSchema(BaseModel):
    institution: str = Field(..., min_length=1, max_length=200)
    degree: str = Field(..., min_length=1, max_length=100)
    field_of_study: str = Field(..., min_length=1, max_length=100)
    start_date: str = Field(..., pattern=r'^\d{4}(-\d{2})?$')  # YYYY or YYYY-MM
    end_date: Optional[str] = Field(None, pattern=r'^\d{4}(-\d{2})?$')
    current: bool = False
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date cannot be before start_date')
        return v

class ExperienceSchema(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=100)
    start_date: str = Field(..., pattern=r'^\d{4}(-\d{2})?$')
    end_date: Optional[str] = Field(None, pattern=r'^\d{4}(-\d{2})?$')
    current: bool = False
    description: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date cannot be before start_date')
        return v

class SkillSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    level: Optional[str] = Field(None, pattern='^(Beginner|Intermediate|Advanced|Expert)$')
    years: Optional[float] = Field(None, ge=0, le=50)

class CertificateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    issuer: str = Field(..., min_length=1, max_length=200)
    date: str = Field(..., pattern=r'^\d{4}(-\d{2})?$')
    url: Optional[str] = Field(None, max_length=500)
    expires: Optional[str] = Field(None, pattern=r'^\d{4}(-\d{2})?$')

class UserProfileSchema(BaseModel):
    summary: Optional[str] = Field(None, max_length=2000)
    education: List[EducationSchema] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    skills: List[SkillSchema] = Field(default_factory=list)
    certificates: List[CertificateSchema] = Field(default_factory=list)
    phone: Optional[str] = Field(None, pattern=r'^[\d\+\-\s\(\)]{10,20}$')
    location: Optional[str] = Field(None, max_length=200)
    linkedin: Optional[str] = Field(None, max_length=500)
    github: Optional[str] = Field(None, max_length=500)
    portfolio: Optional[str] = Field(None, max_length=500)

# ============================================
# Resume Generation Schemas
# ============================================

class ResumeGenerationRequestSchema(BaseModel):
    job_description: str = Field(..., min_length=50, max_length=10000)
    profile_data: UserProfileSchema

class ResumeGenerationResponseSchema(BaseModel):
    id: int
    status: str
    message: str
    estimated_time: Optional[int] = None

# ============================================
# AI Response Schema (what Gemini should return)
# ============================================

class AIResumeExperienceSchema(BaseModel):
    company: str
    title: str
    dates: str
    achievements: List[str]

class AIResumeEducationSchema(BaseModel):
    institution: str
    degree: str
    dates: str
    details: Optional[str] = None

class AIResumeSchema(BaseModel):
    summary: str = Field(..., min_length=50, max_length=500)
    skills: List[str] = Field(..., min_items=3)
    experience: List[AIResumeExperienceSchema]
    education: List[AIResumeEducationSchema]
    certifications: List[str] = Field(default_factory=list)
    ats_keywords: List[str] = Field(..., min_items=5)
    ats_score: int = Field(..., ge=0, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Experienced software engineer with 5+ years...",
                "skills": ["Python", "React", "AWS"],
                "experience": [{
                    "company": "Tech Corp",
                    "title": "Senior Engineer",
                    "dates": "2020 - Present",
                    "achievements": ["Led team of 5", "Improved performance by 40%"]
                }],
                "education": [{
                    "institution": "University",
                    "degree": "B.S. Computer Science",
                    "dates": "2014 - 2018",
                    "details": "GPA 3.8"
                }],
                "certifications": ["AWS Certified"],
                "ats_keywords": ["full-stack", "microservices"],
                "ats_score": 85
            }
        }