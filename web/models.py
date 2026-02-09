"""
Database models for Vibe CV Resume Builder
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cv_masters = db.relationship('CVMaster', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    cv_variants = db.relationship('CVVariant', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='scrypt')
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class CVMaster(db.Model):
    """User's master CV template"""
    __tablename__ = 'cv_masters'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    latex_content = db.Column(db.Text, nullable=False)
    original_filename = db.Column(db.String(255))
    version = db.Column(db.Integer, default=1)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    def __repr__(self):
        return f'<CVMaster user_id={self.user_id} version={self.version}>'


class CVVariant(db.Model):
    """CV variant tailored for specific job"""
    __tablename__ = 'cv_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    folder_name = db.Column(db.String(255), nullable=False, index=True)
    company = db.Column(db.String(255))
    role = db.Column(db.String(255))
    job_description = db.Column(db.Text)
    match_score = db.Column(db.Integer, nullable=True)  # AI match percentage (0-100)
    has_tex = db.Column(db.Boolean, default=False)
    has_pdf = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'folder_name', name='_user_folder_uc'),
    )
    
    def __repr__(self):
        return f'<CVVariant {self.folder_name} user_id={self.user_id}>'
