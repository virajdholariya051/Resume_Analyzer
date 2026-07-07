"""Tests for the two analysis workflows and dashboard aggregation."""

from backend.services.analysis_service import (
    AnalysisService,
    ANALYSIS_TYPE_RESUME_ONLY,
    ANALYSIS_TYPE_RESUME_JOB,
)
from backend.services.job_service import JobService


def test_resume_only_analysis(sample_resume_id):
    svc = AnalysisService()
    res = svc.analyze_resume_only(sample_resume_id, force=True)
    assert res["success"] is True
    assert res["analysis_type"] == ANALYSIS_TYPE_RESUME_ONLY
    assert 0 <= res["ats_score"]["overall_score"] <= 100
    assert 0 <= res["quality_score"] <= 100
    assert "recommendations" in res and isinstance(res["recommendations"], list)
    assert "job_match" not in res  # hidden for resume-only


def test_resume_job_analysis(sample_resume_id):
    job_svc = JobService()
    created = job_svc.create_job(
        "Python Engineer", "Need Python, AWS, Docker, SQL developer.", "Python, AWS, Docker, SQL"
    )
    svc = AnalysisService()
    res = svc.analyze_resume(sample_resume_id, created["job_id"], force=True)
    assert res["success"] is True
    assert res["analysis_type"] == ANALYSIS_TYPE_RESUME_JOB
    assert 0 <= res["job_match"]["overall_match"] <= 100
    assert "candidate_compatibility" in res
    assert "skill_gap" in res["job_match"]


def test_evaluate_resume_quality():
    svc = AnalysisService()
    assert svc.evaluate_resume_quality({}) == 0
    score = svc.evaluate_resume_quality({
        "format_score": 80, "section_completeness": 90,
        "experience_relevance": 70, "education_match": 60,
    })
    assert 0 <= score <= 100


def test_generate_recommendations_non_empty():
    svc = AnalysisService()
    recs = svc.generate_recommendations(
        ["No professional summary or objective section", "Lacks quantifiable achievements"],
        {"format_score": 40, "section_completeness": 40},
    )
    assert recs and all(isinstance(r, str) for r in recs)


def test_dashboard_stats_structure(sample_resume_id, job_seeker_id):
    svc = AnalysisService()
    svc.analyze_resume_only(sample_resume_id, force=True)
    stats = svc.get_dashboard_stats(job_seeker_id)
    for key in [
        "total_resumes", "total_analyses", "average_ats_score",
        "latest_ats_score", "latest_match_percentage",
        "ats_history", "upload_timeline", "top_skills", "recent_analyses",
    ]:
        assert key in stats
    assert stats["total_resumes"] >= 1
    assert isinstance(stats["upload_timeline"]["labels"], list)


def test_analysis_history_includes_type(sample_resume_id, job_seeker_id):
    svc = AnalysisService()
    svc.analyze_resume_only(sample_resume_id, force=True)
    history = svc.get_analysis_history(job_seeker_id)
    assert history
    assert all("analysis_type" in h for h in history)


def test_resume_only_cached_path(sample_resume_id):
    svc = AnalysisService()
    svc.analyze_resume_only(sample_resume_id, force=True)
    cached = svc.analyze_resume_only(sample_resume_id, force=False)
    assert cached["success"] is True
    assert cached.get("cached") is True
    assert cached["analysis_type"] == ANALYSIS_TYPE_RESUME_ONLY


def test_analyze_missing_resume():
    svc = AnalysisService()
    res = svc.analyze_resume_only(999999, force=True)
    assert res["success"] is False


def test_analyze_missing_job(sample_resume_id):
    svc = AnalysisService()
    res = svc.analyze_resume(sample_resume_id, 999999, force=True)
    assert res["success"] is False
