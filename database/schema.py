"""
SQLAlchemy ORM Models for the Resume Analyzer database.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from database.database import Base


class User(Base):
    """User model for authentication and profile management."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="Job Seeker")
    phone = Column(String(15), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, name='{self.name}', email='{self.email}')>"


class Resume(Base):
    """Resume model for storing uploaded resume data."""
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    resume_text = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

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

    # Relationships
    analysis_results = relationship("AnalysisResult", back_populates="job_description", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<JobDescription(job_id={self.job_id}, title='{self.job_title}')>"


class AnalysisResult(Base):
    """Analysis Result model for storing resume analysis outcomes."""
    __tablename__ = "analysis_results"

    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    ats_score = Column(Integer, nullable=False)
    job_match_percentage = Column(Integer, nullable=False)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.resume_id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_descriptions.job_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
