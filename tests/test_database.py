"""Database schema, migration, and integrity tests."""

from sqlalchemy import inspect
from database.database import engine, init_db, get_db
from database.schema import AnalysisResult, Resume


def test_core_tables_exist():
    tables = set(inspect(engine).get_table_names())
    for t in ["users", "resumes", "job_descriptions", "analysis_results",
              "skills", "feedback", "system_settings", "audit_logs", "ai_logs"]:
        assert t in tables


def test_analysis_results_nullable_columns():
    """job_id and job_match_percentage must be nullable for Resume Only flow."""
    cols = {c["name"]: c for c in inspect(engine).get_columns("analysis_results")}
    assert cols["job_id"]["nullable"] is True
    assert cols["job_match_percentage"]["nullable"] is True
    assert "analysis_type" in cols
    assert "quality_score" in cols


def test_init_db_is_idempotent():
    """Running init_db repeatedly must not error or duplicate the schema."""
    init_db()
    init_db()
    tables = set(inspect(engine).get_table_names())
    assert "analysis_results" in tables
    # No leftover rebuild temp table
    assert "analysis_results_old" not in tables


def test_resume_only_row_persists_null_job(make_user, make_resume):
    uid = make_user("DBNull", "dbnull@example.com", "Password1")
    rid = make_resume(uid, "n.pdf", "Skills\nPython")
    db = get_db()
    try:
        row = AnalysisResult(ats_score=50, job_match_percentage=None, resume_id=rid,
                             job_id=None, analysis_type="Resume Only", quality_score=40)
        db.add(row)
        db.commit()
        db.refresh(row)
        assert row.analysis_id is not None
        assert row.job_id is None
    finally:
        db.close()


def test_default_admin_seeded():
    db = get_db()
    try:
        from database.schema import User
        admin = db.query(User).filter(User.role == "Admin").first()
        assert admin is not None
    finally:
        db.close()
