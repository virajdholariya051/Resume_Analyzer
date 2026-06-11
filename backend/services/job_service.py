"""
Job description service for managing job postings.
"""

from typing import Dict, List, Optional
from database.database import get_db
from database.schema import JobDescription
from backend.nlp.skill_extractor import SkillExtractor


class JobService:
    """Service class for job description operations."""

    def __init__(self):
        """Initialize job service."""
        self.skill_extractor = SkillExtractor()

    def create_job(self, title: str, description: str, skills: str = "") -> Dict:
        """
        Create a new job description.
        
        Args:
            title: Job title.
            description: Job description text.
            skills: Comma-separated required skills (auto-extracted if empty).
        
        Returns:
            Dictionary with operation result.
        """
        if not title or not description:
            return {"success": False, "message": "Title and description are required."}

        # Auto-extract skills if not provided
        if not skills:
            extracted = self.skill_extractor.extract_skills(description)
            skills = ", ".join(extracted)

        db = get_db()
        try:
            job = JobDescription(
                job_title=title,
                job_description_text=description,
                required_skills=skills,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return {
                "success": True,
                "message": "Job description saved successfully!",
                "job_id": job.job_id,
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error saving job: {str(e)}"}
        finally:
            db.close()

    def get_all_jobs(self) -> List[Dict]:
        """Get all job descriptions."""
        db = get_db()
        try:
            jobs = db.query(JobDescription).all()
            return [
                {
                    "job_id": j.job_id,
                    "job_title": j.job_title,
                    "job_description_text": j.job_description_text,
                    "required_skills": j.required_skills,
                }
                for j in jobs
            ]
        finally:
            db.close()

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Get a specific job description."""
        db = get_db()
        try:
            j = db.query(JobDescription).filter(JobDescription.job_id == job_id).first()
            if j:
                return {
                    "job_id": j.job_id,
                    "job_title": j.job_title,
                    "job_description_text": j.job_description_text,
                    "required_skills": j.required_skills,
                }
            return None
        finally:
            db.close()

    def update_job(self, job_id: int, title: str, description: str, skills: str) -> Dict:
        """Update an existing job description."""
        db = get_db()
        try:
            job = db.query(JobDescription).filter(JobDescription.job_id == job_id).first()
            if not job:
                return {"success": False, "message": "Job not found."}

            job.job_title = title
            job.job_description_text = description
            job.required_skills = skills
            db.commit()
            return {"success": True, "message": "Job updated successfully!"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating job: {str(e)}"}
        finally:
            db.close()

    def delete_job(self, job_id: int) -> Dict:
        """Delete a job description."""
        db = get_db()
        try:
            job = db.query(JobDescription).filter(JobDescription.job_id == job_id).first()
            if not job:
                return {"success": False, "message": "Job not found."}

            db.delete(job)
            db.commit()
            return {"success": True, "message": "Job deleted successfully!"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error deleting job: {str(e)}"}
        finally:
            db.close()
