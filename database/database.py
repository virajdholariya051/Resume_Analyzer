"""
Database connection and session management using SQLAlchemy.
"""

import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

# Database file path
# On Streamlit Cloud, use /tmp since the app directory may not be writable
if os.environ.get("STREAMLIT_SERVER_HEADLESS"):
    DB_PATH = os.path.join(tempfile.gettempdir(), "resume_analyzer.db")
else:
    DB_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(DB_DIR, "resume_analyzer.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db() -> Session:
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def init_db() -> None:
    """Initialize the database by creating all tables and seeding initial data."""
    from database.schema import User, Resume, JobDescription, AnalysisResult, Skill, resume_skills_table  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _seed_initial_data()


def _seed_initial_data() -> None:
    """Seed essential data if the database is empty (handles ephemeral Streamlit Cloud storage)."""
    from database.schema import Skill, JobDescription, User
    from backend.auth.auth_service import hash_password

    db = SessionLocal()
    try:
        # Only seed if skills table is empty (first run or fresh DB)
        if db.query(Skill).count() > 0:
            return

        # Seed skills
        skills_data = [
            ("Python", "Technical"), ("Java", "Technical"), ("JavaScript", "Technical"),
            ("React", "Technical"), ("Node.js", "Technical"), ("SQL", "Technical"),
            ("MongoDB", "Technical"), ("AWS", "Technical"), ("Docker", "Technical"),
            ("Kubernetes", "Technical"), ("Git", "Technical"), ("Machine Learning", "Technical"),
            ("Data Science", "Technical"), ("HTML", "Technical"), ("CSS", "Technical"),
            ("TypeScript", "Technical"), ("C++", "Technical"), ("C#", "Technical"),
            ("Ruby", "Technical"), ("PHP", "Technical"), ("Swift", "Technical"),
            ("Kotlin", "Technical"), ("Go", "Technical"), ("Rust", "Technical"),
            ("R", "Technical"), ("TensorFlow", "Technical"), ("PyTorch", "Technical"),
            ("Django", "Technical"), ("Flask", "Technical"), ("Spring Boot", "Technical"),
            ("Angular", "Technical"), ("Vue.js", "Technical"), ("PostgreSQL", "Technical"),
            ("MySQL", "Technical"), ("Redis", "Technical"), ("Elasticsearch", "Technical"),
            ("Apache Kafka", "Technical"), ("CI/CD", "Technical"), ("Jenkins", "Technical"),
            ("Terraform", "Technical"), ("Azure", "Technical"), ("GCP", "Technical"),
            ("Linux", "Technical"), ("REST API", "Technical"), ("GraphQL", "Technical"),
            ("Microservices", "Technical"), ("Agile", "Technical"), ("Scrum", "Technical"),
            ("DevOps", "Technical"),
            ("Communication", "Soft"), ("Leadership", "Soft"), ("Problem Solving", "Soft"),
            ("Teamwork", "Soft"), ("Time Management", "Soft"), ("Critical Thinking", "Soft"),
            ("Creativity", "Soft"), ("Adaptability", "Soft"), ("Project Management", "Soft"),
            ("Analytical Skills", "Soft"), ("Attention to Detail", "Soft"),
            ("Decision Making", "Soft"), ("Conflict Resolution", "Soft"),
            ("Presentation Skills", "Soft"), ("Negotiation", "Soft"),
        ]
        for skill_name, skill_type in skills_data:
            db.add(Skill(skill_name=skill_name, skill_type=skill_type))

        # Seed admin user
        admin = User(
            name="Admin",
            email="admin@resumeanalyzer.com",
            password=hash_password("admin123"),
            role="Admin",
            phone="0000000000",
        )
        db.add(admin)

        # Seed sample job descriptions
        sample_jobs = [
            ("Python Developer",
             "We are looking for a Python Developer with experience in Django/Flask, REST APIs, SQL databases, and cloud services.",
             "Python, Django, Flask, REST API, SQL, PostgreSQL, AWS, Docker, Git, Problem Solving"),
            ("Data Scientist",
             "Seeking a Data Scientist proficient in Python, Machine Learning, TensorFlow/PyTorch, and statistical analysis.",
             "Python, Machine Learning, Data Science, TensorFlow, PyTorch, SQL, R, Communication, Analytical Skills"),
            ("Full Stack Developer",
             "Full Stack Developer needed with expertise in React, Node.js, MongoDB, and cloud deployment.",
             "JavaScript, React, Node.js, MongoDB, HTML, CSS, TypeScript, AWS, Docker, Git, Agile"),
        ]
        for title, desc, skills in sample_jobs:
            db.add(JobDescription(job_title=title, job_description_text=desc, required_skills=skills))

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
