"""
Analysis service for running resume analysis, ATS scoring, and job matching.

Supports two workflows:
    * "Resume Only"             - parse, ATS score, quality evaluation and
                                  improvement recommendations (no job needed).
    * "Resume + Job Description" - the above plus Sentence-BERT/keyword based
                                  job matching, skill gap analysis and a
                                  candidate compatibility (rank) score.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from database.database import get_db
from database.schema import AnalysisResult, Resume, JobDescription
from backend.nlp.ats_scorer import ATSScorer
from backend.nlp.job_matcher import JobMatcher
from backend.nlp.resume_parser import ResumeParser
from backend.nlp.skill_extractor import SkillExtractor
from backend.services.ai_log_service import AILogService

logger = logging.getLogger("resume_analyzer.analysis")

# Analysis workflow identifiers (stored in AnalysisResult.analysis_type)
ANALYSIS_TYPE_RESUME_ONLY = "Resume Only"
ANALYSIS_TYPE_RESUME_JOB = "Resume + Job Description"
ANALYSIS_TYPES = [ANALYSIS_TYPE_RESUME_ONLY, ANALYSIS_TYPE_RESUME_JOB]

# Candidate ranking formula weights
RANK_WEIGHTS = {
    "ats_score": 0.40,
    "skill_match": 0.30,
    "experience_match": 0.15,
    "education_match": 0.10,
    "certification_match": 0.05,
}

# Resume quality score weights (structure/quality oriented, ATS-independent)
QUALITY_WEIGHTS = {
    "format_score": 0.30,
    "section_completeness": 0.30,
    "experience_relevance": 0.20,
    "education_match": 0.20,
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

    def evaluate_resume_quality(self, ats_component_scores: Dict) -> int:
        """Compute an overall resume quality score (0-100).

        This is a structure/quality oriented score derived from the ATS
        component scores. It is distinct from the ATS overall score and is the
        headline metric for the "Resume Only" workflow.
        """
        if not ats_component_scores:
            return 0
        total = 0.0
        for key, weight in QUALITY_WEIGHTS.items():
            total += ats_component_scores.get(key, 0) * weight
        return min(100, max(0, round(total)))

    def generate_recommendations(self, weaknesses: List[str],
                                 ats_component_scores: Dict) -> List[str]:
        """Turn detected weaknesses and low component scores into actionable
        improvement recommendations.
        """
        recommendations: List[str] = []

        # Map each weakness to an actionable suggestion.
        for weakness in weaknesses:
            low = weakness.lower()
            if "missing key skills" in low:
                recommendations.append(
                    "Add the missing skills to your resume where you have genuine "
                    "experience, and highlight them in a dedicated Skills section."
                )
            elif "summary" in low or "objective" in low:
                recommendations.append(
                    "Add a concise professional summary at the top that frames your "
                    "experience and target role."
                )
            elif "quantifiable" in low:
                recommendations.append(
                    "Quantify achievements with numbers, percentages or currency "
                    "(e.g. 'reduced load time by 40%')."
                )
            elif "too brief" in low:
                recommendations.append(
                    "Expand your resume with more detail on responsibilities and "
                    "measurable outcomes."
                )
            elif "too lengthy" in low:
                recommendations.append(
                    "Trim your resume to the most relevant, recent achievements to "
                    "improve ATS parsing."
                )
            elif "certification" in low:
                recommendations.append(
                    "List relevant certifications or licenses to strengthen credibility."
                )
            elif "action verbs" in low:
                recommendations.append(
                    "Start bullet points with strong action verbs (developed, led, "
                    "implemented, optimized)."
                )

        # Component-driven recommendations.
        comp = ats_component_scores or {}
        if comp.get("format_score", 100) < 60:
            recommendations.append(
                "Improve formatting: use clear section headers, consistent bullet "
                "points and include contact details."
            )
        if comp.get("section_completeness", 100) < 60:
            recommendations.append(
                "Ensure the essential sections are present: Education, Experience "
                "and Skills."
            )
        if comp.get("skills_coverage", 100) < 50:
            recommendations.append(
                "Broaden your listed skills to better reflect your expertise."
            )

        # De-duplicate while preserving order.
        seen = set()
        unique = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique.append(rec)

        if not unique:
            unique.append("Your resume looks solid. Keep it tailored to each role you apply for.")
        return unique

    def analyze_resume_only(self, resume_id: int, force: bool = False) -> Dict:
        """Run the "Resume Only" workflow (no job description required).

        Extracts resume information, calculates the ATS score, evaluates resume
        quality and generates improvement recommendations.
        """
        db = get_db()
        try:
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                return {"success": False, "message": "Resume not found."}

            # Reuse a cached Resume Only analysis when available.
            if not force:
                existing = (
                    db.query(AnalysisResult)
                    .filter(
                        AnalysisResult.resume_id == resume_id,
                        AnalysisResult.job_id.is_(None),
                        AnalysisResult.analysis_type == ANALYSIS_TYPE_RESUME_ONLY,
                    )
                    .order_by(AnalysisResult.created_at.desc())
                    .first()
                )
                if existing:
                    logger.info("Returning cached Resume Only analysis %s", existing.analysis_id)
                    return self._build_result_from_record(existing, resume, None)

            resume_text = resume.resume_text
            _start = time.perf_counter()

            parsed_resume = self.resume_parser.parse_resume(resume_text)
            ats_result = self.ats_scorer.calculate_ats_score(resume_text)
            components = ats_result.get("component_scores", {})

            quality_score = self.evaluate_resume_quality(components)
            strengths = self.job_matcher.generate_strengths(resume_text, [])
            weaknesses = self.job_matcher.generate_weaknesses(resume_text, [])
            recommendations = self.generate_recommendations(weaknesses, components)

            analysis = AnalysisResult(
                ats_score=ats_result["overall_score"],
                job_match_percentage=None,
                strengths="; ".join(strengths),
                weaknesses="; ".join(weaknesses),
                recommendations="; ".join(recommendations),
                resume_id=resume_id,
                job_id=None,
                analysis_type=ANALYSIS_TYPE_RESUME_ONLY,
                quality_score=quality_score,
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

            processing_ms = int((time.perf_counter() - _start) * 1000)
            self.ai_log.log(
                user_id=resume.user_id, resume_id=resume_id, action="Resume Only Analysis",
                status="success", processing_ms=processing_ms,
                message=f"ATS={ats_result['overall_score']} Quality={quality_score}",
            )
            logger.info("Resume Only analysis complete for resume %s", resume_id)

            return {
                "success": True,
                "analysis_id": analysis.analysis_id,
                "analysis_type": ANALYSIS_TYPE_RESUME_ONLY,
                "ats_score": ats_result,
                "quality_score": quality_score,
                "parsed_resume": parsed_resume,
                "skills": parsed_resume.get("skills", []),
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommendations": recommendations,
            }
        except Exception as e:
            db.rollback()
            logger.exception("Resume Only analysis failed for resume %s", resume_id)
            self.ai_log.log(
                user_id=None, resume_id=resume_id, action="Resume Only Analysis",
                status="failed", processing_ms=0, message=str(e),
            )
            return {"success": False, "message": f"Analysis failed: {str(e)}"}
        finally:
            db.close()

    def analyze_resume(self, resume_id: int, job_id: int, force: bool = False) -> Dict:
        """
        Perform complete resume analysis against a job description
        ("Resume + Job Description" workflow).

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
            quality_score = self.evaluate_resume_quality(ats_result.get("component_scores", {}))

            strengths = self.job_matcher.generate_strengths(resume_text, required_skills)
            weaknesses = self.job_matcher.generate_weaknesses(resume_text, required_skills)
            recommendations = self.generate_recommendations(
                weaknesses, ats_result.get("component_scores", {})
            )

            analysis = AnalysisResult(
                ats_score=ats_result["overall_score"],
                job_match_percentage=match_result["overall_match"],
                strengths="; ".join(strengths),
                weaknesses="; ".join(weaknesses),
                recommendations="; ".join(recommendations),
                resume_id=resume_id,
                job_id=job_id,
                analysis_type=ANALYSIS_TYPE_RESUME_JOB,
                quality_score=quality_score,
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
            logger.info("Resume + JD analysis complete for resume %s / job %s", resume_id, job_id)

            return {
                "success": True,
                "analysis_id": analysis.analysis_id,
                "analysis_type": ANALYSIS_TYPE_RESUME_JOB,
                "ats_score": ats_result,
                "job_match": match_result,
                "parsed_resume": parsed_resume,
                "quality_score": quality_score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommendations": recommendations,
                "certification_match": round(cert_match),
                "rank_score": rank_score,
                "candidate_compatibility": rank_score,
            }

        except Exception as e:
            db.rollback()
            logger.exception("Resume + JD analysis failed for resume %s", resume_id)
            self.ai_log.log(
                user_id=None, resume_id=resume_id, action="Resume Analysis",
                status="failed", processing_ms=0, message=str(e),
            )
            return {"success": False, "message": f"Analysis failed: {str(e)}"}
        finally:
            db.close()

    def _build_result_from_record(self, record, resume, job) -> Dict:
        """Reconstruct a result dict from a stored AnalysisResult (cached path)."""
        analysis_type = record.analysis_type or ANALYSIS_TYPE_RESUME_JOB
        # Re-parse resume text so cached results still show structured fields.
        parsed_resume = {}
        if resume is not None:
            try:
                parsed_resume = self.resume_parser.parse_resume(resume.resume_text)
            except Exception:  # pragma: no cover - parsing is best-effort here
                parsed_resume = {}

        result = {
            "success": True,
            "cached": True,
            "analysis_id": record.analysis_id,
            "analysis_type": analysis_type,
            "ats_score": {
                "overall_score": record.ats_score,
                "grade": self.ats_scorer._get_grade(record.ats_score),
                "component_scores": {},
            },
            "quality_score": record.quality_score or 0,
            "parsed_resume": parsed_resume,
            "skills": parsed_resume.get("skills", []),
            "strengths": record.strengths.split("; ") if record.strengths else [],
            "weaknesses": record.weaknesses.split("; ") if record.weaknesses else [],
            "recommendations": record.recommendations.split("; ") if record.recommendations else [],
            "certification_match": record.certification_match or 0,
            "rank_score": record.rank_score or 0.0,
            "candidate_compatibility": record.rank_score or 0.0,
        }

        if analysis_type == ANALYSIS_TYPE_RESUME_JOB:
            result["job_match"] = {
                "overall_match": record.job_match_percentage or 0,
                "component_scores": {
                    "skill_match": record.skill_match or 0,
                    "keyword_match": record.keyword_match or 0,
                    "experience_match": record.experience_match or 0,
                    "education_match": record.education_match or 0,
                },
                "skill_gap": {},
                "recommendation": "",
            }
        return result

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
                    "analysis_type": r.analysis_type or ANALYSIS_TYPE_RESUME_JOB,
                    "quality_score": r.quality_score or 0,
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

            # Match percentage stats ignore Resume Only analyses (NULL match).
            match_values = [a.job_match_percentage for a in analyses if a.job_match_percentage is not None]
            avg_match = round(sum(match_values) / len(match_values), 1) if match_values else 0

            # Chronological ordering (oldest -> newest) for trend charts.
            ordered = sorted(analyses, key=lambda a: a.created_at or datetime.min)
            latest = ordered[-1] if ordered else None
            latest_ats = latest.ats_score if latest else 0
            latest_match = latest.job_match_percentage if (latest and latest.job_match_percentage is not None) else 0

            # ATS Score history (chronological) for the trend chart.
            ats_history = [
                {
                    "analysis_id": a.analysis_id,
                    "ats_score": a.ats_score,
                    "job_match_percentage": a.job_match_percentage or 0,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "N/A",
                }
                for a in ordered
            ]

            # Resume upload timeline (count of uploads per day).
            upload_counts: Dict[str, int] = {}
            for r in resumes:
                day = r.upload_date.strftime("%Y-%m-%d") if r.upload_date else "N/A"
                upload_counts[day] = upload_counts.get(day, 0) + 1
            upload_days = sorted(upload_counts.keys())
            upload_timeline = {
                "labels": upload_days,
                "values": [upload_counts[d] for d in upload_days],
            }

            # Get most common skills
            all_skills = []
            for resume in resumes:
                skills = self.skill_extractor.extract_skills(resume.resume_text)
                all_skills.extend(skills)

            skill_counts = {}
            for skill in all_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

            top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            # Recent analyses (newest first) for the history table/chart.
            recent = list(reversed(ordered))[:5]
            recent_analyses = [
                {
                    "analysis_id": a.analysis_id,
                    "ats_score": a.ats_score,
                    "job_match_percentage": a.job_match_percentage or 0,
                    "analysis_type": a.analysis_type or ANALYSIS_TYPE_RESUME_JOB,
                    "created_at": a.created_at.strftime("%Y-%m-%d") if a.created_at else "N/A",
                }
                for a in recent
            ]

            return {
                "total_resumes": total_resumes,
                "total_analyses": total_analyses,
                "average_ats_score": avg_ats,
                "average_match_percentage": avg_match,
                "latest_ats_score": latest_ats,
                "latest_match_percentage": latest_match,
                "top_skills": top_skills,
                "recent_analyses": recent_analyses,
                "ats_history": ats_history,
                "upload_timeline": upload_timeline,
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
