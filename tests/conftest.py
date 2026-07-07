"""
Pytest configuration and shared fixtures.

Uses an isolated temporary SQLite database (via the RESUME_ANALYZER_DB
environment variable) so tests never touch the real application database.
The environment variable MUST be set before any application module that
imports ``database.database`` is imported.
"""

import os
import sys
import tempfile

# ---------------------------------------------------------------------------
# Isolate the database BEFORE importing any application code.
# ---------------------------------------------------------------------------
_TMP_DIR = tempfile.mkdtemp(prefix="resume_analyzer_test_")
os.environ["RESUME_ANALYZER_DB"] = os.path.join(_TMP_DIR, "test.db")

# Ensure project root is importable.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest  # noqa: E402
from database.database import init_db, get_db  # noqa: E402
from database.schema import User, Resume, utcnow  # noqa: E402
from backend.auth.auth_service import hash_password  # noqa: E402


SAMPLE_RESUME_TEXT = """
John Doe
john.doe@example.com
+1 415 555 2671

Summary
Experienced software engineer with 6 years building scalable web applications.

Skills
Python, Django, Flask, SQL, PostgreSQL, AWS, Docker, Git, REST API, Communication,
Leadership, Problem Solving

Experience
Senior Software Engineer - developed and managed microservices, improved latency by 40%,
led a team of 5 engineers from 2019 - present.

Education
Bachelor of Science in Computer Science, State University, 2015. GPA 3.8

Certifications
AWS Certified Solutions Architect

Projects
Built a real-time analytics dashboard using Python and React.
"""

SPARSE_RESUME_TEXT = "Jane Smith\njane@example.com\nWorked somewhere."


@pytest.fixture(scope="session", autouse=True)
def _initialize_database():
    """Create schema and seed default data once for the whole test session."""
    init_db()
    yield


def _create_user(name, email, password, role="Job Seeker", is_active=True):
    """Insert a user directly and return its id."""
    db = get_db()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return existing.user_id
        user = User(
            name=name, email=email, password=hash_password(password),
            role=role, is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.user_id
    finally:
        db.close()


def _create_resume(user_id, file_name, text, upload_date=None,
                   candidate_name=None, status="New"):
    """Insert a resume directly and return its id."""
    db = get_db()
    try:
        resume = Resume(
            file_name=file_name,
            resume_text=text,
            user_id=user_id,
            candidate_name=candidate_name,
            status=status,
            upload_date=upload_date or utcnow(),
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume.resume_id
    finally:
        db.close()


@pytest.fixture
def admin_id():
    """The seeded default admin's id."""
    db = get_db()
    try:
        admin = db.query(User).filter(User.role == "Admin").first()
        return admin.user_id
    finally:
        db.close()


@pytest.fixture
def job_seeker_id():
    return _create_user("Test Seeker", "seeker_fixture@example.com", "Password1")


@pytest.fixture
def recruiter_id():
    return _create_user("Test Recruiter", "recruiter_fixture@example.com", "Password1", role="Recruiter")


@pytest.fixture
def sample_resume_id(job_seeker_id):
    return _create_resume(job_seeker_id, "john_doe.pdf", SAMPLE_RESUME_TEXT, candidate_name="John Doe")


@pytest.fixture
def make_user():
    """Factory fixture for creating users."""
    return _create_user


@pytest.fixture
def make_resume():
    """Factory fixture for creating resumes."""
    return _create_resume


@pytest.fixture
def sample_text():
    return SAMPLE_RESUME_TEXT


@pytest.fixture
def sparse_text():
    return SPARSE_RESUME_TEXT
