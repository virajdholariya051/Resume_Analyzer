"""
Recruiter service: dashboard analytics, candidate ranking, filtering,
comparison, and AI-style insights for the Recruiter role.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import Resume, AnalysisResult, JobDescription
from backend.nlp.skill_extractor import SkillExtractor
from backend.services.analysis_service import AnalysisService


class RecruiterService:
    """Service powering recruiter-specific features."""

    def __init__(self):
        self.skill_extractor = SkillExtractor()
        self.analysis_service = AnalysisService()

    # ------------------------------------------------------------------ #
    # Dashboard
    # ------------------------------------------------------------------ #
    def get_dashboard_stats(self, recruiter_id: int) -> Dict:
        """Aggregate dashboard statistics for a recruiter's candidate pool."""
        db = get_db()
        try:
            resumes = db.query(Resume).filter(Resume.user_id == recruiter_id).all()
            resume_ids = [r.resume_id for r in resumes]

            analyses = (
                db.query(AnalysisResult).filter(AnalysisResult.resume_id.in_(resume_ids)).all()
                if resume_ids else []
            )

            # Status counts
            status_counts = {"New": 0, "Under Review": 0, "Shortlisted": 0, "Rejected": 0}
            for r in resumes:
                status_counts[r.status or "New"] = status_counts.get(r.status or "New", 0) + 1

            avg_ats = round(sum(a.ats_score for a in analyses) / len(analyses), 1) if analyses else 0
            avg_match = round(sum(a.job_match_percentage for a in analyses) / len(analyses), 1) if analyses else 0

            # Top skills across all candidate resumes
            skill_counts: Dict[str, int] = {}
            for r in resumes:
                for skill in self.skill_extractor.extract_skills(r.resume_text):
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
            top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            # Distributions
            ats_scores = [a.ats_score for a in analyses]
            match_scores = [a.job_match_percentage for a in analyses]

            # Recent uploads
            recent = sorted(resumes, key=lambda r: r.upload_date or "", reverse=True)[:5]
            recent_uploads = [
                {
                    "resume_id": r.resume_id,
                    "candidate_name": r.candidate_name or "Unknown",
                    "file_name": r.file_name,
                    "status": r.status or "New",
                    "upload_date": r.upload_date.strftime("%Y-%m-%d %H:%M") if r.upload_date else "N/A",
                }
                for r in recent
            ]

            return {
                "total_resumes": len(resumes),
                "total_candidates": len(resumes),
                "average_ats_score": avg_ats,
                "average_match_percentage": avg_match,
                "top_skills": top_skills,
                "shortlisted": status_counts.get("Shortlisted", 0),
                "rejected": status_counts.get("Rejected", 0),
                "under_review": status_counts.get("Under Review", 0),
                "new": status_counts.get("New", 0),
                "status_counts": status_counts,
                "ats_scores": ats_scores,
                "match_scores": match_scores,
                "recent_uploads": recent_uploads,
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Ranking
    # ------------------------------------------------------------------ #
    def rank_candidates(self, recruiter_id: int, job_id: int, auto_analyze: bool = True,
                        progress_callback=None) -> List[Dict]:
        """
        Rank a recruiter's candidates against a job description.

        Analyzes any unanalyzed resumes (cached when possible), then returns
        a list sorted by rank_score (highest first).
        """
        db = get_db()
        try:
            resumes = db.query(Resume).filter(Resume.user_id == recruiter_id).all()
        finally:
            db.close()

        resume_ids = [r.resume_id for r in resumes]
        if not resume_ids:
            return []

        if auto_analyze:
            self.analysis_service.analyze_batch(
                resume_ids, job_id, force=False, progress_callback=progress_callback
            )

        # Gather latest analysis per resume for this job
        db = get_db()
        try:
            ranked = []
            for r in resumes:
                analysis = (
                    db.query(AnalysisResult)
                    .filter(AnalysisResult.resume_id == r.resume_id, AnalysisResult.job_id == job_id)
                    .order_by(AnalysisResult.created_at.desc())
                    .first()
                )
                if not analysis:
                    continue
                ranked.append({
                    "resume_id": r.resume_id,
                    "candidate_name": r.candidate_name or "Unknown",
                    "file_name": r.file_name,
                    "status": r.status or "New",
                    "ats_score": analysis.ats_score,
                    "job_match_percentage": analysis.job_match_percentage,
                    "skill_match": analysis.skill_match or 0,
                    "experience_match": analysis.experience_match or 0,
                    "education_match": analysis.education_match or 0,
                    "certification_match": analysis.certification_match or 0,
                    "rank_score": analysis.rank_score or 0.0,
                })

            ranked.sort(key=lambda x: x["rank_score"], reverse=True)
            for i, item in enumerate(ranked, start=1):
                item["rank"] = i
            return ranked
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Filtering
    # ------------------------------------------------------------------ #
    def filter_candidates(self, ranked: List[Dict], filters: Dict) -> List[Dict]:
        """
        Filter a ranked candidate list.

        Supported filter keys: min_ats, min_match, status, skill, name.
        """
        result = ranked
        if filters.get("min_ats") is not None:
            result = [c for c in result if c["ats_score"] >= filters["min_ats"]]
        if filters.get("min_match") is not None:
            result = [c for c in result if c["job_match_percentage"] >= filters["min_match"]]
        if filters.get("status") and filters["status"] != "All":
            result = [c for c in result if c["status"] == filters["status"]]
        if filters.get("name"):
            term = filters["name"].lower()
            result = [c for c in result if term in (c["candidate_name"] or "").lower()]
        if filters.get("skill"):
            skill_term = filters["skill"]
            result = [c for c in result if self._candidate_has_skill(c["resume_id"], skill_term)]
        return result

    def _candidate_has_skill(self, resume_id: int, skill: str) -> bool:
        """Check whether a candidate's resume contains a given skill."""
        db = get_db()
        try:
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                return False
            skills = {s.lower() for s in self.skill_extractor.extract_skills(resume.resume_text)}
            return skill.lower() in skills
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Comparison
    # ------------------------------------------------------------------ #
    def compare_candidates(self, resume_ids: List[int], job_id: int) -> List[Dict]:
        """Build side-by-side comparison data for selected candidates."""
        comparison = []
        db = get_db()
        try:
            for rid in resume_ids:
                resume = db.query(Resume).filter(Resume.resume_id == rid).first()
                if not resume:
                    continue
                analysis = (
                    db.query(AnalysisResult)
                    .filter(AnalysisResult.resume_id == rid, AnalysisResult.job_id == job_id)
                    .order_by(AnalysisResult.created_at.desc())
                    .first()
                )
                skills = self.skill_extractor.extract_skills(resume.resume_text)
                comparison.append({
                    "resume_id": rid,
                    "candidate_name": resume.candidate_name or "Unknown",
                    "ats_score": analysis.ats_score if analysis else "N/A",
                    "job_match_percentage": analysis.job_match_percentage if analysis else "N/A",
                    "skill_match": (analysis.skill_match if analysis else "N/A"),
                    "experience_match": (analysis.experience_match if analysis else "N/A"),
                    "education_match": (analysis.education_match if analysis else "N/A"),
                    "certification_match": (analysis.certification_match if analysis else "N/A"),
                    "rank_score": (analysis.rank_score if analysis else "N/A"),
                    "skills": ", ".join(skills[:20]) if skills else "None detected",
                    "education": resume.education or "N/A",
                    "experience": (resume.experience[:200] if resume.experience else "N/A"),
                    "certifications": resume.certifications or "N/A",
                    "status": resume.status or "New",
                })
            return comparison
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # AI-style insights
    # ------------------------------------------------------------------ #
    def generate_insights(self, resume_id: int, job_id: int) -> Dict:
        """Generate strengths, weaknesses, and recommendations for a candidate."""
        result = self.analysis_service.analyze_resume(resume_id, job_id, force=False)
        if not result.get("success"):
            return {"strengths": [], "weaknesses": [], "recommendations": []}

        strengths = result.get("strengths", [])
        weaknesses = result.get("weaknesses", [])

        # Derive recommendations from skill gap / weaknesses
        recommendations: List[str] = []
        job_match = result.get("job_match", {})
        skill_gap = job_match.get("skill_gap", {})
        missing = skill_gap.get("missing", [])
        if missing:
            recommendations.append(f"Add or highlight missing skills: {', '.join(missing[:5])}")
        if any("structure" in w.lower() or "summary" in w.lower() for w in weaknesses):
            recommendations.append("Improve resume structure and add a professional summary.")
        if any("certif" in w.lower() for w in weaknesses):
            recommendations.append("Add relevant certifications to strengthen the profile.")
        if any("quantif" in w.lower() for w in weaknesses):
            recommendations.append("Include quantifiable achievements (numbers, %, $).")
        if not recommendations:
            recommendations.append("Profile is strong. Keep the resume tailored to each role.")

        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
        }
