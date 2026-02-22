from app.extensions import db
from datetime import datetime

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Input data
    job_description = db.Column(db.Text, nullable=False)
    
    # Generated data
    generated_json = db.Column(db.JSON, nullable=True)  # AI generated JSON
    pdf_path = db.Column(db.String(500), nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('resumes', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_description': self.job_description[:200] + '...' if len(self.job_description) > 200 else self.job_description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'pdf_url': f'/api/resumes/download/{self.id}' if self.pdf_path else None
        }
    
    def to_dict_full(self):
        """Full details including generated JSON"""
        data = self.to_dict()
        data['generated_json'] = self.generated_json
        return data