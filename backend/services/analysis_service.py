"""
Analysis service for running resume analysis, ATS scoring, and job matching.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import AnalysisResult, Resume, JobDescription
from backend.nlp.ats_scorer import ATSScorer
from backend.nlp.job_matcher import JobMatcher
from backend.nlp.resume_parser import ResumeParser
from backend.nlp.skill_extractor import SkillExtractor


class AnalysisService:
    """Service for resume analysis operations."""

    def __init__(self):
        """Initialize analysis service."""
        self.ats_scorer = ATSScorer()
        self.job_matcher = JobMatcher()
        self.resume_parser = ResumeParser()
        self.skill_extractor = SkillExtractor()

    def analyze_resume(self, resume_id: int, job_id: int) -> Dict:
        """
        Perform complete resume analysis against a job description.
        
        Args:
            resume_id: ID of the resume to analyze.
            job_id: ID of the job description to compare against.
        
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

            resume_text = resume.resume_text
            job_description = job.job_description_text
            required_skills = [s.strip() for s in job.required_skills.split(",")]

            # Parse resume
            parsed_resume = self.resume_parser.parse_resume(resume_text)

            # Calculate ATS score
            ats_result = self.ats_scorer.calculate_ats_score(
                resume_text, job_description, required_skills
            )

            # Calculate job match
            match_result = self.job_matcher.calculate_match(
                resume_text, job_description, required_skills
            )

            # Generate strengths and weaknesses
            strengths = self.job_matcher.generate_strengths(resume_text, required_skills)
            weaknesses = self.job_matcher.generate_weaknesses(resume_text, required_skills)

            # Save analysis result
            analysis = AnalysisResult(
                ats_score=ats_result["overall_score"],
                job_match_percentage=match_result["overall_match"],
                strengths="; ".join(strengths),
                weaknesses="; ".join(weaknesses),
                resume_id=resume_id,
                job_id=job_id,
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

            return {
                "success": True,
                "analysis_id": analysis.analysis_id,
                "ats_score": ats_result,
                "job_match": match_result,
                "parsed_resume": parsed_resume,
                "strengths": strengths,
                "weaknesses": weaknesses,
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Analysis failed: {str(e)}"}
        finally:
            db.close()

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
