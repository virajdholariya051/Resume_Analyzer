"""Tests for job, settings, feedback, export, and file-validation services."""

from backend.services.job_service import JobService
from backend.services.settings_service import SettingsService
from backend.services.feedback_service import FeedbackService
from backend.services.export_service import ExportService
from backend.utils.file_parser import validate_file


# ---------------------------------------------------------------------------
# JobService
# ---------------------------------------------------------------------------
def test_job_crud():
    svc = JobService()
    created = svc.create_job("QA Engineer", "Testing with Selenium and Python.", "Selenium, Python")
    assert created["success"] is True
    job_id = created["job_id"]

    fetched = svc.get_job_by_id(job_id)
    assert fetched["job_title"] == "QA Engineer"

    updated = svc.update_job(job_id, "QA Lead", "Lead QA.", "Selenium, Python, Leadership")
    assert updated["success"] is True
    assert svc.get_job_by_id(job_id)["job_title"] == "QA Lead"

    deleted = svc.delete_job(job_id)
    assert deleted["success"] is True
    assert svc.get_job_by_id(job_id) is None


def test_job_requires_title_and_description():
    svc = JobService()
    assert svc.create_job("", "desc")["success"] is False


def test_job_auto_extracts_skills():
    svc = JobService()
    created = svc.create_job("Dev", "We use Python, Docker and AWS heavily.", "")
    job = svc.get_job_by_id(created["job_id"])
    assert "Python" in job["required_skills"]
    svc.delete_job(created["job_id"])


# ---------------------------------------------------------------------------
# SettingsService
# ---------------------------------------------------------------------------
def test_settings_set_get():
    svc = SettingsService()
    svc.set("unit_test_key", "42")
    assert svc.get("unit_test_key") == "42"
    assert svc.get("missing_key_xyz", "default") == "default"


def test_settings_set_many_and_all():
    svc = SettingsService()
    svc.set_many({"k1_test": "a", "k2_test": "b"})
    allv = svc.get_all()
    assert allv.get("k1_test") == "a"
    assert allv.get("k2_test") == "b"


# ---------------------------------------------------------------------------
# FeedbackService
# ---------------------------------------------------------------------------
def test_feedback_submit_and_counts(job_seeker_id):
    svc = FeedbackService()
    res = svc.submit(job_seeker_id, "Bug", "Crash", "The app crashed", rating=None)
    assert res["success"] is True
    counts = svc.get_counts()
    assert counts["Bug"] >= 1


def test_feedback_invalid_category(job_seeker_id):
    svc = FeedbackService()
    assert svc.submit(job_seeker_id, "Nonsense", "x", "y")["success"] is False


def test_feedback_requires_message(job_seeker_id):
    svc = FeedbackService()
    assert svc.submit(job_seeker_id, "Review", "subj", "")["success"] is False


def test_feedback_reply_and_status(job_seeker_id):
    svc = FeedbackService()
    svc.submit(job_seeker_id, "Feature", "Add dark mode", "Please add it")
    items = svc.get_by_category("Feature")
    fid = items[0]["feedback_id"]
    assert svc.reply(fid, "Thanks!")["success"] is True
    assert svc.update_status(fid, "Closed")["success"] is True


# ---------------------------------------------------------------------------
# ExportService
# ---------------------------------------------------------------------------
_CANDIDATES = [
    {"rank": 1, "candidate_name": "Alice", "ats_score": 88,
     "job_match_percentage": 80, "rank_score": 84.2, "status": "Shortlisted"},
    {"rank": 2, "candidate_name": "Bob", "ats_score": 70,
     "job_match_percentage": 65, "rank_score": 68.0, "status": "New"},
]


def test_export_csv():
    data = ExportService().to_csv(_CANDIDATES)
    assert isinstance(data, bytes)
    assert b"Alice" in data


def test_export_excel():
    data = ExportService().to_excel(_CANDIDATES)
    assert isinstance(data, bytes) and len(data) > 0


def test_export_pdf():
    data = ExportService().to_pdf(_CANDIDATES, "Test Report")
    assert isinstance(data, bytes) and len(data) > 0
    assert data[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# File validation (black-box)
# ---------------------------------------------------------------------------
def test_validate_file_rejects_unsupported():
    assert validate_file("resume.txt", 100)["valid"] is False
    assert validate_file("resume.exe", 100)["valid"] is False


def test_validate_file_accepts_supported():
    assert validate_file("resume.pdf", 100)["valid"] is True
    assert validate_file("resume.docx", 100)["valid"] is True


def test_validate_file_rejects_too_large():
    huge = 50 * 1024 * 1024  # 50 MB
    assert validate_file("resume.pdf", huge)["valid"] is False
