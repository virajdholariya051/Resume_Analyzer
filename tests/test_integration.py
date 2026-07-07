"""Integration & system tests covering end-to-end role workflows."""

from backend.auth.auth_service import register_user, login_user
from backend.services.analysis_service import AnalysisService
from backend.services.job_service import JobService
from backend.services.recruiter_service import RecruiterService
from backend.services.user_service import UserService


def test_job_seeker_end_to_end(make_resume):
    """Register -> login -> upload (persisted) -> analyze -> dashboard reflects it."""
    reg = register_user("E2E Seeker", "e2e_seeker@example.com", "Password1")
    assert reg["success"]
    uid = reg["user_id"]

    login = login_user("e2e_seeker@example.com", "Password1")
    assert login["success"] and login["user"]["role"] == "Job Seeker"

    resume_id = make_resume(uid, "e2e.pdf",
                            "Jane\njane@x.com\nSkills\nPython, SQL, AWS\nExperience\nBuilt systems.")
    analysis = AnalysisService()
    res = analysis.analyze_resume_only(resume_id, force=True)
    assert res["success"]

    stats = analysis.get_dashboard_stats(uid)
    assert stats["total_resumes"] == 1
    assert stats["total_analyses"] >= 1


def test_recruiter_ranking_end_to_end(make_user, make_resume):
    """Recruiter uploads candidates, creates a job, ranks candidates."""
    rec_id = make_user("E2E Rec", "e2e_rec@example.com", "Password1", role="Recruiter")

    make_resume(rec_id, "cand1.pdf",
                "Cand One\nc1@x.com\nSkills\nPython, AWS, Docker, SQL\nExperience\nLed teams.",
                candidate_name="Cand One")
    make_resume(rec_id, "cand2.pdf",
                "Cand Two\nc2@x.com\nSkills\nJava\nExperience\nJunior developer.",
                candidate_name="Cand Two")

    job = JobService().create_job("Backend Dev", "Python AWS Docker SQL required.",
                                  "Python, AWS, Docker, SQL")
    recruiter = RecruiterService()
    ranked = recruiter.rank_candidates(rec_id, job["job_id"], auto_analyze=True)

    assert len(ranked) == 2
    # Highest rank_score should be first, and ranks assigned sequentially
    assert ranked[0]["rank"] == 1
    assert ranked[0]["rank_score"] >= ranked[1]["rank_score"]
    # The Python/AWS candidate should outrank the Java-only candidate
    assert ranked[0]["candidate_name"] == "Cand One"


def test_recruiter_filter_candidates(make_user, make_resume):
    rec_id = make_user("Filter Rec", "filter_rec@example.com", "Password1", role="Recruiter")
    make_resume(rec_id, "f1.pdf", "A\na@x.com\nSkills\nPython, AWS, SQL", candidate_name="A")
    job = JobService().create_job("Dev2", "Python SQL", "Python, SQL")
    recruiter = RecruiterService()
    ranked = recruiter.rank_candidates(rec_id, job["job_id"], auto_analyze=True)
    filtered = recruiter.filter_candidates(ranked, {"min_ats": 0, "min_match": 0, "status": "All"})
    assert len(filtered) == len(ranked)
    none = recruiter.filter_candidates(ranked, {"min_ats": 101})
    assert none == []


def test_admin_user_management_integration(admin_id):
    """Admin creates a recruiter then disables it."""
    svc = UserService()
    created = svc.create_privileged_user(
        admin_id, "Managed Rec", "managed_rec@example.com", "Password1", "", "Recruiter"
    )
    assert created["success"]
    new_id = created["user_id"]
    assert svc.set_active(admin_id, new_id, False)["success"]
    # A disabled user cannot log in
    assert login_user("managed_rec@example.com", "Password1")["success"] is False
