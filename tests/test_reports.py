"""Tests for PDF report generation (report_service)."""

import os
from backend.services.report_service import ReportService


def _resume_job_result():
    return {
        "analysis_type": "Resume + Job Description",
        "ats_score": {"overall_score": 82, "grade": "A",
                      "component_scores": {"format_score": 80, "skills_coverage": 75}},
        "job_match": {
            "overall_match": 78,
            "skill_gap": {"matched": ["Python"], "missing": ["Kubernetes"], "extra": ["Flask"]},
        },
        "strengths": ["Strong technical skill set"],
        "weaknesses": ["No certifications"],
    }


def _resume_only_result():
    return {
        "analysis_type": "Resume Only",
        "ats_score": {"overall_score": 65, "grade": "B",
                      "component_scores": {"format_score": 70}},
        "strengths": ["Well-structured resume"],
        "weaknesses": ["Lacks quantifiable achievements"],
    }


def test_generate_ats_report_resume_job():
    path = ReportService().generate_ats_report(_resume_job_result(), "john.pdf")
    assert os.path.exists(path)
    assert path.endswith(".pdf")
    os.remove(path)


def test_generate_ats_report_resume_only():
    """Resume-only results have no job_match; report should still generate."""
    path = ReportService().generate_ats_report(_resume_only_result(), "jane.pdf")
    assert os.path.exists(path)
    os.remove(path)


def test_generate_skill_gap_report():
    gap = {"matched": ["Python"], "missing": ["AWS"], "extra": ["Flask"]}
    path = ReportService().generate_skill_gap_report(gap, "john.pdf", "Python Dev")
    assert os.path.exists(path)
    os.remove(path)
