"""
SQLAlchemy ORM Models for the Resume Analyzer database.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Table, Float, Boolean
)
from sqlalchemy.orm import relationship
from database.database import Base


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime.

    Uses timezone-aware ``datetime.now(timezone.utc)`` (``datetime.utcnow`` is
    deprecated from Python 3.12) but strips tzinfo to keep storage consistent
    with the existing naive-UTC values in the SQLite database.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """User model for authentication and profile management."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="Job Seeker")
    phone = Column(String(15), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, name='{self.name}', email='{self.email}')>"


class Resume(Base):
    """Resume model for storing uploaded resume data."""
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=utcnow)
    resume_text = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    # Recruiter / candidate management fields
    candidate_name = Column(String(150), nullable=True)
    candidate_email = Column(String(150), nullable=True)
    status = Column(String(50), default="New")  # New, Under Review, Shortlisted, Rejected
    file_hash = Column(String(64), nullable=True)  # for duplicate detection
    education = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)
    projects = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="resumes")
    analysis_results = relationship("AnalysisResult", back_populates="resume", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="resume_skills", back_populates="resumes")

    def __repr__(self) -> str:
        return f"<Resume(resume_id={self.resume_id}, file_name='{self.file_name}')>"


class JobDescription(Base):
    """Job Description model for storing job postings."""
    __tablename__ = "job_descriptions"

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    job_title = Column(String(100), nullable=False)
    job_description_text = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=False)

    # Extended recruiter fields
    company_name = Column(String(150), nullable=True)
    experience_required = Column(String(100), nullable=True)
    education_requirement = Column(String(150), nullable=True)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    # Relationships
    analysis_results = relationship("AnalysisResult", back_populates="job_description", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<JobDescription(job_id={self.job_id}, title='{self.job_title}')>"


class AnalysisResult(Base):
    """Analysis Result model for storing resume analysis outcomes."""
    __tablename__ = "analysis_results"

    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    ats_score = Column(Integer, nullable=False)
    # Nullable: a "Resume Only" analysis has no job match percentage.
    job_match_percentage = Column(Integer, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.resume_id"), nullable=False)
    # Nullable: a "Resume Only" analysis is not tied to a job description.
    job_id = Column(Integer, ForeignKey("job_descriptions.job_id"), nullable=True)
    # Workflow type: "Resume Only" | "Resume + Job Description"
    analysis_type = Column(String(30), default="Resume + Job Description")
    # Overall resume quality score (0-100), primarily for Resume Only analyses.
    quality_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    # Component match scores (for ranking)
    skill_match = Column(Integer, default=0)
    experience_match = Column(Integer, default=0)
    education_match = Column(Integer, default=0)
    certification_match = Column(Integer, default=0)
    keyword_match = Column(Integer, default=0)
    rank_score = Column(Float, default=0.0)

    # Relationships
    resume = relationship("Resume", back_populates="analysis_results")
    job_description = relationship("JobDescription", back_populates="analysis_results")

    def __repr__(self) -> str:
        return f"<AnalysisResult(analysis_id={self.analysis_id}, ats_score={self.ats_score})>"


class Skill(Base):
    """Skill model for the skills database."""
    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(100), nullable=False, unique=True)
    skill_type = Column(String(50), nullable=False)

    # Relationships
    resumes = relationship("Resume", secondary="resume_skills", back_populates="skills")

    def __repr__(self) -> str:
        return f"<Skill(skill_id={self.skill_id}, name='{self.skill_name}')>"


# Association table for Resume-Skills many-to-many relationship
resume_skills_table = Table(
    "resume_skills",
    Base.metadata,
    Column("resume_id", Integer, ForeignKey("resumes.resume_id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.skill_id"), primary_key=True),
)


class AuditLog(Base):
    """Audit log for tracking sensitive administrative actions."""
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    action = Column(Text, nullable=False)
    target_user_id = Column(Integer, nullable=True)
    ip_address = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=utcnow)

    def __repr__(self) -> str:
        return f"<AuditLog(log_id={self.log_id}, action='{self.action}')>"


class AILog(Base):
    """Log of AI/NLP analysis requests for monitoring."""
    __tablename__ = "ai_logs"

    ai_log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    resume_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)        # e.g., "ATS Analysis"
    status = Column(String(20), default="success")       # success | failed
    processing_ms = Column(Integer, default=0)           # processing time in ms
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    def __repr__(self) -> str:
        return f"<AILog(id={self.ai_log_id}, action='{self.action}', status='{self.status}')>"


class Feedback(Base):
    """User feedback: reviews, bug reports, feature requests, support tickets."""
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    category = Column(String(30), default="Review")      # Review | Bug | Feature | Ticket
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)              # 1-5 for reviews
    status = Column(String(20), default="Open")          # Open | Resolved | Closed
    admin_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    def __repr__(self) -> str:
        return f"<Feedback(id={self.feedback_id}, category='{self.category}', status='{self.status}')>"


class SystemSetting(Base):
    """Key/value store for configurable system settings."""
    __tablename__ = "system_settings"

    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    category = Column(String(50), default="General")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"
