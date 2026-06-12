"""
Analysis service for running resume analysis, ATS scoring, and job matching.
"""

import time
from typing import Dict, List, Optional
from database.database import get_db
from database.schema import AnalysisResult, Resume, JobDescription
from backend.nlp.ats_scorer import ATSScorer
from backend.nlp.job_matcher import JobMatcher
from backend.nlp.resume_parser import ResumeParser
from backend.nlp.skill_extractor import SkillExtractor
from backend.services.ai_log_service import AILogService


# Candidate ranking formula weights
RANK_WEIGHTS = {
    "ats_score": 0.40,
    "skill_match": 0.30,
    "experience_match": 0.15,
    "education_match": 0.10,
    "certification_match": 0.05,
}


class AnalysisService:
    """Service for resume analysis operations."""

    def __init__(self):
        """Initialize analysis service."""
        self.ats_scorer = ATSScorer()
        self.job_matcher = JobMatcher()
        self.resume_parser = ResumeParser()
        self.skill_extractor = SkillExtractor()
        self.ai_log = AILogService()

    @staticmethod
    def compute_rank_score(ats: float, skill: float, experience: float,
                           education: float, certification: float) -> float:
        """Compute the weighted candidate ranking score (0-100)."""
        score = (
            ats * RANK_WEIGHTS["ats_score"]
            + skill * RANK_WEIGHTS["skill_match"]
            + experience * RANK_WEIGHTS["experience_match"]
            + education * RANK_WEIGHTS["education_match"]
            + certification * RANK_WEIGHTS["certification_match"]
        )
        return round(score, 2)

    def analyze_resume(self, resume_id: int, job_id: int, force: bool = False) -> Dict:
        """
        Perform complete resume analysis against a job description.

        Args:
            resume_id: ID of the resume to analyze.
            job_id: ID of the job description to compare against.
            force: If False, reuse an existing analysis for the pair (prevents
                duplicate analysis). If True, always recompute.

        Returns:
            Dictionary with complete analysis results.
        """
        db = get_db()
        try:
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            job = db.query(JobDescription).filter(JobDescription.job_id == job_id).first()

            if not resume:
                return {"success": False, "message": "Resume not found."}
            if not job:
                return {"success": False, "message": "Job description not found."}

            # Reuse cached analysis if present (performance + prevent duplicates)
            if not force:
                existing = (
                    db.query(AnalysisResult)
                    .filter(AnalysisResult.resume_id == resume_id, AnalysisResult.job_id == job_id)
                    .order_by(AnalysisResult.created_at.desc())
                    .first()
                )
                if existing:
                    return self._build_result_from_record(existing, resume, job)

            resume_text = resume.resume_text
            job_description = job.job_description_text
            required_skills = [s.strip() for s in job.required_skills.split(",") if s.strip()]

            _start = time.perf_counter()
            parsed_resume = self.resume_parser.parse_resume(resume_text)

            ats_result = self.ats_scorer.calculate_ats_score(
                resume_text, job_description, required_skills
            )
            match_result = self.job_matcher.calculate_match(
                resume_text, job_description, required_skills
            )
            cert_match = self.job_matcher.calculate_certification_match(resume_text, job_description)

            components = match_result.get("component_scores", {})
            skill_match = components.get("skill_match", 0)
            experience_match = components.get("experience_match", 0)
            education_match = components.get("education_match", 0)
            keyword_match = components.get("keyword_match", 0)

            rank_score = self.compute_rank_score(
                ats_result["overall_score"], skill_match, experience_match,
                education_match, cert_match,
            )

            strengths = self.job_matcher.generate_strengths(resume_text, required_skills)
            weaknesses = self.job_matcher.generate_weaknesses(resume_text, required_skills)

            analysis = AnalysisResult(
                ats_score=ats_result["overall_score"],
                job_match_percentage=match_result["overall_match"],
                strengths="; ".join(strengths),
                weaknesses="; ".join(weaknesses),
                resume_id=resume_id,
                job_id=job_id,
                skill_match=round(skill_match),
                experience_match=round(experience_match),
                education_match=round(education_match),
                certification_match=round(cert_match),
                keyword_match=round(keyword_match),
                rank_score=rank_score,
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

            # Record AI monitoring log (success)
            processing_ms = int((time.perf_counter() - _start) * 1000)
            self.ai_log.log(
                user_id=resume.user_id, resume_id=resume_id, action="Resume Analysis",
                status="success", processing_ms=processing_ms,
                message=f"ATS={ats_result['overall_score']} Match={match_result['overall_match']}",
            )

            return {
                "success": True,
                "analysis_id": analysis.analysis_id,
                "ats_score": ats_result,
                "job_match": match_result,
                "parsed_resume": parsed_resume,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "certification_match": round(cert_match),
                "rank_score": rank_score,
            }

        except Exception as e:
            db.rollback()
            self.ai_log.log(
                user_id=None, resume_id=resume_id, action="Resume Analysis",
                status="failed", processing_ms=0, message=str(e),
            )
            return {"success": False, "message": f"Analysis failed: {str(e)}"}
        finally:
            db.close()

    def _build_result_from_record(self, record, resume, job) -> Dict:
        """Reconstruct a result dict from a stored AnalysisResult (cached path)."""
        return {
            "success": True,
            "analysis_id": record.analysis_id,
            "ats_score": {
                "overall_score": record.ats_score,
                "grade": self.ats_scorer._get_grade(record.ats_score),
                "component_scores": {},
            },
            "job_match": {
                "overall_match": record.job_match_percentage,
                "component_scores": {
                    "skill_match": record.skill_match or 0,
                    "keyword_match": record.keyword_match or 0,
                    "experience_match": record.experience_match or 0,
                    "education_match": record.education_match or 0,
                },
                "skill_gap": {},
                "recommendation": "",
            },
            "parsed_resume": {},
            "strengths": record.strengths.split("; ") if record.strengths else [],
            "weaknesses": record.weaknesses.split("; ") if record.weaknesses else [],
            "certification_match": record.certification_match or 0,
            "rank_score": record.rank_score or 0.0,
            "cached": True,
        }

    def analyze_batch(self, resume_ids: List[int], job_id: int, force: bool = False,
                      progress_callback=None) -> Dict:
        """
        Analyze multiple resumes against one job description (batch processing).

        Args:
            resume_ids: List of resume IDs.
            job_id: Job description ID.
            force: Recompute even if a cached analysis exists.
            progress_callback: Optional callable(current, total).

        Returns:
            Summary with succeeded/failed counts.
        """
        summary = {"total": len(resume_ids), "succeeded": 0, "failed": 0}
        for idx, rid in enumerate(resume_ids, start=1):
            if progress_callback:
                progress_callback(idx, len(resume_ids))
            result = self.analyze_resume(rid, job_id, force=force)
            if result.get("success"):
                summary["succeeded"] += 1
            else:
                summary["failed"] += 1
        return summary

    def get_analysis_history(self, user_id: int) -> List[Dict]:
        """Get analysis history for a user."""
        db = get_db()
        try:
            results = (
                db.query(AnalysisResult)
                .join(Resume)
                .filter(Resume.user_id == user_id)
                .order_by(AnalysisResult.created_at.desc())
                .all()
            )
            return [
                {
                    "analysis_id": r.analysis_id,
                    "ats_score": r.ats_score,
                    "job_match_percentage": r.job_match_percentage,
                    "strengths": r.strengths,
                    "weaknesses": r.weaknesses,
                    "resume_id": r.resume_id,
                    "job_id": r.job_id,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "N/A",
                }
                for r in results
            ]
        finally:
            db.close()

    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Get a specific analysis result."""
        db = get_db()
        try:
            r = db.query(AnalysisResult).filter(AnalysisResult.analysis_id == analysis_id).first()
            if r:
                return {
                    "analysis_id": r.analysis_id,
                    "ats_score": r.ats_score,
                    "job_match_percentage": r.job_match_percentage,
                    "strengths": r.strengths.split("; ") if r.strengths else [],
                    "weaknesses": r.weaknesses.split("; ") if r.weaknesses else [],
                    "resume_id": r.resume_id,
                    "job_id": r.job_id,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "N/A",
                }
            return None
        finally:
            db.close()

    def get_dashboard_stats(self, user_id: int) -> Dict:
        """Get dashboard statistics for a user."""
        db = get_db()
        try:
            resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
            resume_ids = [r.resume_id for r in resumes]

            analyses = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.resume_id.in_(resume_ids))
                .all() if resume_ids else []
            )

            total_resumes = len(resumes)
            total_analyses = len(analyses)
            avg_ats = round(sum(a.ats_score for a in analyses) / len(analyses), 1) if analyses else 0
            avg_match = round(sum(a.job_match_percentage for a in analyses) / len(analyses), 1) if analyses else 0

            # Get most common skills
            all_skills = []
            for resume in resumes:
                skills = self.skill_extractor.extract_skills(resume.resume_text)
                all_skills.extend(skills)

            skill_counts = {}
            for skill in all_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            # Recent analyses
            recent = sorted(analyses, key=lambda a: a.created_at if a.created_at else "", reverse=True)[:5]
            recent_analyses = [
                {
                    "analysis_id": a.analysis_id,
                    "ats_score": a.ats_score,
                    "job_match_percentage": a.job_match_percentage,
                    "created_at": a.created_at.strftime("%Y-%m-%d") if a.created_at else "N/A",
                }
                for a in recent
            ]

            return {
                "total_resumes": total_resumes,
                "total_analyses": total_analyses,
                "average_ats_score": avg_ats,
                "average_match_percentage": avg_match,
                "top_skills": top_skills,
                "recent_analyses": recent_analyses,
            }
        finally:
            db.close()

    def get_all_analyses(self) -> List[Dict]:
        """Get all analysis results (admin function)."""
        db = get_db()
        try:
            results = db.query(AnalysisResult).order_by(AnalysisResult.created_at.desc()).all()
            return [
                {
                    "analysis_id": r.analysis_id,
                    "ats_score": r.ats_score,
                    "job_match_percentage": r.job_match_percentage,
                    "resume_id": r.resume_id,
                    "job_id": r.job_id,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "N/A",
                }
                for r in results
            ]
        finally:
            db.close()
