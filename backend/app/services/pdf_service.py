from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime
import logging
from typing import Dict, Any
from flask import current_app

logger = logging.getLogger(__name__)

class PDFService:
    """Service for generating PDF resumes"""
    
    def __init__(self, output_dir='generated_resumes'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ResumeTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=1  # Center alignment
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#2c3e50'),
            borderWidth=1,
            borderColor=colors.HexColor('#eeeeee'),
            borderPadding=8,
            borderRadius=5,
            backColor=colors.HexColor('#f8f9fa')
        ))
        
        # Company/position style
        self.styles.add(ParagraphStyle(
            name='CompanyStyle',
            parent=self.styles['Normal'],
            fontSize=13,
            spaceBefore=10,
            spaceAfter=2,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#34495e')
        ))
        
        # Date style
        self.styles.add(ParagraphStyle(
            name='DateStyle',
            parent=self.styles['Italic'],
            fontSize=11,
            spaceAfter=5,
            textColor=colors.HexColor('#7f8c8d')
        ))
        
        # Achievement style
        self.styles.add(ParagraphStyle(
            name='AchievementStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=3,
            textColor=colors.HexColor('#2d3436')
        ))
        
        # Skill badge style
        self.styles.add(ParagraphStyle(
            name='SkillStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            backColor=colors.HexColor('#ecf0f1'),
            borderPadding=5,
            borderRadius=3
        ))
        
        # ATS score style
        self.styles.add(ParagraphStyle(
            name='ATSScore',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=2,  # Right alignment
            textColor=colors.HexColor('#27ae60')
        ))
    
    def generate_pdf(self, resume_data: Dict[str, Any], resume_id: int, user_name: str) -> str:
        """
        Generate PDF from resume data
        
        Args:
            resume_data: AI generated resume JSON
            resume_id: Resume ID for filename
            user_name: User's name for title
            
        Returns:
            str: Path to generated PDF
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"resume_{user_name.replace(' ', '_')}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # ============================================
            # Title
            # ============================================
            story.append(Paragraph(user_name, self.styles['ResumeTitle']))
            story.append(Spacer(1, 10))
            
            # ATS Score (if available)
            if resume_data.get('ats_score'):
                story.append(Paragraph(
                    f"ATS Optimization Score: {resume_data['ats_score']}/100",
                    self.styles['ATSScore']
                ))
                story.append(Spacer(1, 15))
            
            # ============================================
            # Professional Summary
            # ============================================
            if resume_data.get('summary'):
                story.append(Paragraph("Professional Summary", self.styles['SectionHeader']))
                story.append(Paragraph(resume_data['summary'], self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            # ============================================
            # Skills
            # ============================================
            if resume_data.get('skills'):
                story.append(Paragraph("Skills", self.styles['SectionHeader']))
                
                # Group skills by category if possible
                skills = resume_data['skills']
                
                # Create a bullet list of skills
                bullet_items = []
                for skill in skills:
                    bullet_items.append(
                        ListItem(Paragraph(f"• {skill}", self.styles['AchievementStyle']))
                    )
                
                story.append(ListFlowable(
                    bullet_items,
                    bulletType='bullet',
                    leftIndent=20
                ))
                story.append(Spacer(1, 10))
            
            # ============================================
            # Professional Experience
            # ============================================
            if resume_data.get('experience'):
                story.append(Paragraph("Professional Experience", self.styles['SectionHeader']))
                
                for exp in resume_data['experience']:
                    # Company and Title
                    story.append(Paragraph(
                        f"<b>{exp.get('title', '')}</b>",
                        self.styles['CompanyStyle']
                    ))
                    story.append(Paragraph(
                        exp.get('company', ''),
                        self.styles['Normal']
                    ))
                    
                    # Dates
                    if exp.get('dates'):
                        story.append(Paragraph(
                            exp['dates'],
                            self.styles['DateStyle']
                        ))
                    
                    # Achievements
                    achievements = exp.get('achievements', [])
                    if achievements:
                        bullet_items = []
                        for achievement in achievements:
                            bullet_items.append(
                                ListItem(Paragraph(f"• {achievement}", self.styles['AchievementStyle']))
                            )
                        
                        story.append(ListFlowable(
                            bullet_items,
                            bulletType='bullet',
                            leftIndent=30
                        ))
                    
                    story.append(Spacer(1, 8))
            
            # ============================================
            # Education
            # ============================================
            if resume_data.get('education'):
                story.append(Paragraph("Education", self.styles['SectionHeader']))
                
                for edu in resume_data['education']:
                    # Degree and Institution
                    story.append(Paragraph(
                        f"<b>{edu.get('degree', '')}</b>",
                        self.styles['CompanyStyle']
                    ))
                    story.append(Paragraph(
                        edu.get('institution', ''),
                        self.styles['Normal']
                    ))
                    
                    # Dates
                    if edu.get('dates'):
                        story.append(Paragraph(
                            edu['dates'],
                            self.styles['DateStyle']
                        ))
                    
                    # Details
                    if edu.get('details'):
                        story.append(Paragraph(
                            edu['details'],
                            self.styles['AchievementStyle']
                        ))
                    
                    story.append(Spacer(1, 5))
            
            # ============================================
            # Certifications
            # ============================================
            if resume_data.get('certifications'):
                story.append(Paragraph("Certifications", self.styles['SectionHeader']))
                
                bullet_items = []
                for cert in resume_data['certifications']:
                    bullet_items.append(
                        ListItem(Paragraph(f"• {cert}", self.styles['AchievementStyle']))
                    )
                
                story.append(ListFlowable(
                    bullet_items,
                    bulletType='bullet',
                    leftIndent=20
                ))
            
            # ============================================
            # ATS Keywords (Optional - can be commented out)
            # ============================================
            if resume_data.get('ats_keywords') and False:  # Disabled by default
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    f"Keywords: {', '.join(resume_data['ats_keywords'])}",
                    self.styles['Italic']
                ))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"✅ PDF generated successfully: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {str(e)}")
            raise
    
    def get_pdf_url(self, filename: str) -> str:
        """Get URL for PDF download"""
        return f"/api/resumes/download/{filename}"

# Singleton instance
pdf_service = PDFService()