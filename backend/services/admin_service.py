"""
Admin analytics service - aggregations for the enterprise admin dashboard.

Provides KPI computation, time-series analytics, skills analytics, recruiter
performance, and system/database status information.
"""

import os
from typing import Dict, List
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from database.database import get_db, DB_PATH
from database.schema import User, Resume, AnalysisResult, JobDescription, AILog
from backend.nlp.skill_extractor import SkillExtractor


class AdminService:
    """Aggregations and analytics for the admin panel."""

    def __init__(self):
        self.skill_extractor = SkillExtractor()

    # ------------------------------------------------------------------ #
    # Overview KPIs
    # ------------------------------------------------------------------ #
    def get_overview_kpis(self) -> Dict:
        """Compute the top-level KPI cards with day-over-day trend indicators."""
        db = get_db()
        try:
            users = db.query(User).all()
            resumes = db.query(Resume).all()
            analyses = db.query(AnalysisResult).all()

            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)

            def _count_on(items, attr, day):
                return sum(1 for i in items if getattr(i, attr) and getattr(i, attr).date() == day)

            # Trends: today vs yesterday
            users_today = _count_on(users, "created_at", today)
            users_yesterday = _count_on(users, "created_at", yesterday)
            resumes_today = _count_on(resumes, "upload_date", today)
            resumes_yesterday = _count_on(resumes, "upload_date", yesterday)

            role_counts = Counter(u.role for u in users)
            avg_ats = round(sum(a.ats_score for a in analyses) / len(analyses), 1) if analyses else 0
            avg_match = round(sum(a.job_match_percentage for a in analyses) / len(analyses), 1) if analyses else 0

            # "Active users today" — users created today as a proxy for activity
            active_today = users_today

            return {
                "total_users": len(users),
                "total_recruiters": role_counts.get("Recruiter", 0),
                "total_admins": role_counts.get("Admin", 0),
                "total_job_seekers": role_counts.get("Job Seeker", 0),
                "total_resumes": len(resumes),
                "total_analyses": len(analyses),
                "average_ats_score": avg_ats,
                "average_match_percentage": avg_match,
                "active_users_today": active_today,
                "trends": {
                    "users": self._trend(users_today, users_yesterday),
                    "resumes": self._trend(resumes_today, resumes_yesterday),
                },
            }
        finally:
            db.close()

    @staticmethod
    def _trend(current: int, previous: int) -> Dict:
        """Return a trend dict with direction and percentage change."""
        if previous == 0:
            pct = 100.0 if current > 0 else 0.0
        else:
            pct = round(((current - previous) / previous) * 100, 1)
        direction = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        return {"direction": direction, "pct": abs(pct)}

    # ------------------------------------------------------------------ #
    # Time-series analytics
    # ------------------------------------------------------------------ #
    def get_user_growth(self, days: int = 30) -> Dict[str, List]:
        """Cumulative user growth over the last N days."""
        db = get_db()
        try:
            users = db.query(User).order_by(User.created_at).all()
            return self._cumulative_series([u.created_at for u in users], days)
        finally:
            db.close()

    def get_upload_trend(self, days: int = 30) -> Dict[str, List]:
        """Daily resume upload counts over the last N days."""
        db = get_db()
        try:
            resumes = db.query(Resume).all()
            return self._daily_series([r.upload_date for r in resumes], days)
        finally:
            db.close()

    def get_daily_analysis_count(self, days: int = 30) -> Dict[str, List]:
        """Daily analysis counts over the last N days."""
        db = get_db()
        try:
            analyses = db.query(AnalysisResult).all()
            return self._daily_series([a.created_at for a in analyses], days)
        finally:
            db.close()

    def get_score_distributions(self) -> Dict[str, List[int]]:
        """ATS and match score lists for distribution charts."""
        db = get_db()
        try:
            analyses = db.query(AnalysisResult).all()
            return {
                "ats_scores": [a.ats_score for a in analyses],
                "match_scores": [a.job_match_percentage for a in analyses],
            }
        finally:
            db.close()

    def _daily_series(self, dates: List, days: int) -> Dict[str, List]:
        """Build a daily count series for the last N days."""
        today = datetime.utcnow().date()
        buckets = defaultdict(int)
        for d in dates:
            if d:
                buckets[d.date()] += 1
        labels, values = [], []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            labels.append(day.strftime("%m-%d"))
            values.append(buckets.get(day, 0))
        return {"labels": labels, "values": values}

    def _cumulative_series(self, dates: List, days: int) -> Dict[str, List]:
        """Build a cumulative count series for the last N days."""
        today = datetime.utcnow().date()
        start = today - timedelta(days=days - 1)
        # Count items created before the window starts
        base = sum(1 for d in dates if d and d.date() < start)
        daily = defaultdict(int)
        for d in dates:
            if d and d.date() >= start:
                daily[d.date()] += 1
        labels, values = [], []
        running = base
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            running += daily.get(day, 0)
            labels.append(day.strftime("%m-%d"))
            values.append(running)
        return {"labels": labels, "values": values}

    # ------------------------------------------------------------------ #
    # Skills analytics
    # ------------------------------------------------------------------ #
    def get_skills_analytics(self, top_n: int = 20) -> Dict:
        """Top skills found in resumes and most-requested skills in jobs (gap)."""
        db = get_db()
        try:
            resumes = db.query(Resume).all()
            jobs = db.query(JobDescription).all()

            resume_skill_counts = Counter()
            for r in resumes:
                for s in self.skill_extractor.extract_skills(r.resume_text):
                    resume_skill_counts[s] += 1

            job_skill_counts = Counter()
            for j in jobs:
                for s in [x.strip() for x in (j.required_skills or "").split(",") if x.strip()]:
                    job_skill_counts[s] += 1

            # Missing skills: requested by jobs but rarely present in resumes
            missing = []
            for skill, demand in job_skill_counts.most_common():
                supply = resume_skill_counts.get(skill, 0)
                if supply < demand:
                    missing.append((skill, demand - supply))
            missing.sort(key=lambda x: x[1], reverse=True)

            return {
                "top_skills": resume_skill_counts.most_common(top_n),
                "requested_skills": job_skill_counts.most_common(top_n),
                "missing_skills": missing[:top_n],
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Recruiter performance
    # ------------------------------------------------------------------ #
    def get_recruiter_performance(self) -> List[Dict]:
        """Per-recruiter activity and performance metrics."""
        db = get_db()
        try:
            recruiters = db.query(User).filter(User.role == "Recruiter").all()
            result = []
            for rec in recruiters:
                resumes = db.query(Resume).filter(Resume.user_id == rec.user_id).all()
                resume_ids = [r.resume_id for r in resumes]
                analyses = (
                    db.query(AnalysisResult).filter(AnalysisResult.resume_id.in_(resume_ids)).all()
                    if resume_ids else []
                )
                shortlisted = sum(1 for r in resumes if r.status == "Shortlisted")
                avg_ats = round(sum(a.ats_score for a in analyses) / len(analyses), 1) if analyses else 0
                result.append({
                    "recruiter": rec.name,
                    "email": rec.email,
                    "candidates": len(resumes),
                    "analyses": len(analyses),
                    "shortlisted": shortlisted,
                    "avg_ats": avg_ats,
                    "active": getattr(rec, "is_active", True),
                })
            result.sort(key=lambda x: x["candidates"], reverse=True)
            return result
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # System / database status
    # ------------------------------------------------------------------ #
    def get_system_status(self) -> Dict:
        """Database size, storage usage, and table row counts."""
        db = get_db()
        try:
            db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0

            from backend.config.settings import UPLOAD_DIR, REPORTS_DIR
            upload_size = self._dir_size(UPLOAD_DIR)
            reports_size = self._dir_size(REPORTS_DIR)

            counts = {
                "users": db.query(User).count(),
                "resumes": db.query(Resume).count(),
                "analyses": db.query(AnalysisResult).count(),
                "jobs": db.query(JobDescription).count(),
                "ai_logs": db.query(AILog).count(),
            }

            return {
                "db_path": DB_PATH,
                "db_size_kb": round(db_size / 1024, 1),
                "upload_size_kb": round(upload_size / 1024, 1),
                "reports_size_kb": round(reports_size / 1024, 1),
                "total_storage_kb": round((db_size + upload_size + reports_size) / 1024, 1),
                "table_counts": counts,
            }
        finally:
            db.close()

    @staticmethod
    def _dir_size(path: str) -> int:
        """Total size of files in a directory (bytes)."""
        total = 0
        if path and os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
        return total
