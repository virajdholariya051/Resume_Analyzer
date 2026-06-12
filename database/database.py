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
    from database.schema import (  # noqa: F401
        User, Resume, JobDescription, AnalysisResult, Skill, resume_skills_table,
        AuditLog, AILog, Feedback, SystemSetting,
    )
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    _seed_initial_data()
    _seed_default_settings()


def _run_migrations() -> None:
    """Apply lightweight additive migrations for existing SQLite databases.

    SQLAlchemy's create_all does not add new columns to pre-existing tables,
    so we add any missing columns via ALTER TABLE for backward compatibility.
    """
    from sqlalchemy import inspect, text

    # column_name -> column definition (SQLite-compatible DDL)
    migrations = {
        "users": {
            "is_active": "BOOLEAN DEFAULT 1",
        },
        "audit_logs": {
            "ip_address": "VARCHAR(64)",
        },
        "resumes": {
            "candidate_name": "VARCHAR(150)",
            "candidate_email": "VARCHAR(150)",
            "status": "VARCHAR(50) DEFAULT 'New'",
            "file_hash": "VARCHAR(64)",
            "education": "TEXT",
            "experience": "TEXT",
            "certifications": "TEXT",
            "projects": "TEXT",
        },
        "job_descriptions": {
            "company_name": "VARCHAR(150)",
            "experience_required": "VARCHAR(100)",
            "education_requirement": "VARCHAR(150)",
            "created_by": "INTEGER",
        },
        "analysis_results": {
            "skill_match": "INTEGER DEFAULT 0",
            "experience_match": "INTEGER DEFAULT 0",
            "education_match": "INTEGER DEFAULT 0",
            "certification_match": "INTEGER DEFAULT 0",
            "keyword_match": "INTEGER DEFAULT 0",
            "rank_score": "FLOAT DEFAULT 0",
        },
    }

    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        with engine.begin() as conn:
            for table, columns in migrations.items():
                if table not in existing_tables:
                    continue
                existing_cols = {c["name"] for c in inspector.get_columns(table)}
                for col_name, col_def in columns.items():
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
    except Exception:
        # Migrations are best-effort; create_all already built fresh schemas.
        pass


def _seed_initial_data() -> None:
    """Seed essential data if the database is empty (handles ephemeral Streamlit Cloud storage)."""
    from database.schema import Skill, JobDescription, User
    from backend.auth.auth_service import hash_password

    db = SessionLocal()
    try:
        # Always ensure default accounts exist (independent of skills seeding so
        # that pre-existing databases also gain the Recruiter account).
        _ensure_default_users(db, hash_password)

        # Only seed skills/jobs if skills table is empty (first run or fresh DB)
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


def _ensure_default_users(db, hash_password) -> None:
    """Create the default Admin and Recruiter accounts if they don't exist."""
    from database.schema import User

    defaults = [
        ("Admin", "admin@resumeanalyzer.com", "admin123", "Admin", "0000000000"),
        ("Recruiter", "recruiter@resumeanalyzer.com", "recruiter123", "Recruiter", "1111111111"),
    ]
    changed = False
    for name, email, password, role, phone in defaults:
        exists = db.query(User).filter(User.email == email).first()
        if not exists:
            db.add(User(
                name=name,
                email=email,
                password=hash_password(password),
                role=role,
                phone=phone,
            ))
            changed = True
    if changed:
        db.commit()


def _seed_default_settings() -> None:
    """Seed default system settings if they don't already exist."""
    from database.schema import SystemSetting

    defaults = [
        # key, value, category
        ("max_file_size_mb", "10", "Resume Rules"),
        ("allowed_formats", "pdf,docx", "Resume Rules"),
        ("ats_threshold", "70", "AI Settings"),
        ("match_threshold", "75", "AI Settings"),
        ("nlp_model", "en_core_web_sm", "AI Settings"),
        ("smtp_host", "", "Email Settings"),
        ("smtp_port", "587", "Email Settings"),
        ("smtp_user", "", "Email Settings"),
        ("password_min_length", "8", "Security Settings"),
        ("session_timeout_min", "30", "Security Settings"),
        ("login_attempt_limit", "5", "Security Settings"),
        ("backup_frequency", "Daily", "Backup Settings"),
    ]

    db = SessionLocal()
    try:
        existing = {s.key for s in db.query(SystemSetting).all()}
        changed = False
        for key, value, category in defaults:
            if key not in existing:
                db.add(SystemSetting(key=key, value=value, category=category))
                changed = True
        if changed:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
