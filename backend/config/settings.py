"""
Application configuration settings.
"""

import os
import tempfile

# Application settings
APP_NAME = "Resume Analyzer"
APP_VERSION = "1.0.0"

# Determine project root (works both locally and on Streamlit Cloud)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))

# File upload settings
# On Streamlit Cloud, the filesystem is ephemeral. Use /tmp for reliability.
if os.environ.get("STREAMLIT_SERVER_HEADLESS"):
    # Running on Streamlit Cloud
    UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "resume_analyzer_uploads")
    REPORTS_DIR = os.path.join(tempfile.gettempdir(), "resume_analyzer_reports")
else:
    # Running locally
    UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
    REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ATS scoring weights
ATS_WEIGHTS = {
    "format_score": 0.15,
    "keyword_density": 0.25,
    "skills_coverage": 0.25,
    "experience_relevance": 0.15,
    "education_match": 0.10,
    "section_completeness": 0.10,
}

# Job match weights
JOB_MATCH_WEIGHTS = {
    "skill_match": 0.40,
    "keyword_match": 0.30,
    "experience_match": 0.20,
    "education_match": 0.10,
}
