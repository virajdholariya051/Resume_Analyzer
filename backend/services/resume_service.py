"""
Resume service handling upload, storage, and retrieval operations.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from database.database import get_db
from database.schema import Resume, Skill, resume_skills_table
from backend.utils.file_parser import save_uploaded_file, extract_text, validate_file
from backend.nlp.skill_extractor import SkillExtractor
from backend.config.settings import UPLOAD_DIR


class ResumeService:
    """Service class for resume operations."""

    def __init__(self):
        """Initialize resume service."""
        self.skill_extractor = SkillExtractor()

    def upload_resume(self, uploaded_file, user_id: int) -> Dict:
        """
        Process and store an uploaded resume.
        
        Args:
            uploaded_file: Streamlit UploadedFile object.
            user_id: ID of the uploading user.
        
        Returns:
            Dictionary with operation result.
        """
        # Validate file
        validation = validate_file(uploaded_file.name, uploaded_file.size)
        if not validation["valid"]:
            return {"success": False, "message": validation["message"]}

        # Save file to disk
        file_path = save_uploaded_file(uploaded_file, UPLOAD_DIR)
        if not file_path:
            return {"success": False, "message": "Failed to save file."}

        # Extract text
        resume_text = extract_text(file_path)
        if not resume_text:
            # Clean up the saved file
            os.remove(file_path)
            return {"success": False, "message": "Failed to extract text from file. The file may be empty or corrupted."}

        # Save to database
        db = get_db()
        try:
            resume = Resume(
                file_name=uploaded_file.name,
                resume_text=resume_text,
                user_id=user_id,
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

            # Extract and save skills
            skills = self.skill_extractor.extract_skills(resume_text)
            self._save_resume_skills(db, resume.resume_id, skills)

            return {
                "success": True,
                "message": "Resume uploaded successfully!",
                "resume_id": resume.resume_id,
                "text_length": len(resume_text),
                "skills_found": len(skills),
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db.close()

    def _save_resume_skills(self, db, resume_id: int, skill_names: List[str]) -> None:
        """Save extracted skills linked to a resume."""
        for skill_name in skill_names:
            skill = db.query(Skill).filter(Skill.skill_name == skill_name).first()
            if skill:
                # Check if association already exists
                existing = db.execute(
                    resume_skills_table.select().where(
                        (resume_skills_table.c.resume_id == resume_id) &
                        (resume_skills_table.c.skill_id == skill.skill_id)
                    )
                ).first()
                if not existing:
                    db.execute(
                        resume_skills_table.insert().values(
                            resume_id=resume_id, skill_id=skill.skill_id
                        )
                    )
        db.commit()

    def get_user_resumes(self, user_id: int) -> List[Dict]:
        """Get all resumes for a user."""
        db = get_db()
        try:
            resumes = db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.upload_date.desc()).all()
            return [
                {
                    "resume_id": r.resume_id,
                    "file_name": r.file_name,
                    "upload_date": r.upload_date.strftime("%Y-%m-%d %H:%M") if r.upload_date else "N/A",
                    "text_preview": r.resume_text[:200] + "..." if len(r.resume_text) > 200 else r.resume_text,
                }
                for r in resumes
            ]
        finally:
            db.close()

    def get_resume_by_id(self, resume_id: int) -> Optional[Dict]:
        """Get a specific resume by ID."""
        db = get_db()
        try:
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if resume:
                return {
                    "resume_id": resume.resume_id,
                    "file_name": resume.file_name,
                    "upload_date": resume.upload_date.strftime("%Y-%m-%d %H:%M") if resume.upload_date else "N/A",
                    "resume_text": resume.resume_text,
                    "user_id": resume.user_id,
                }
            return None
        finally:
            db.close()

    def delete_resume(self, resume_id: int) -> Dict:
        """Delete a resume by ID."""
        db = get_db()
        try:
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                return {"success": False, "message": "Resume not found."}

            # Delete file from disk
            file_path = os.path.join(UPLOAD_DIR, resume.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)

            db.delete(resume)
            db.commit()
            return {"success": True, "message": "Resume deleted successfully."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error deleting resume: {str(e)}"}
        finally:
            db.close()

    def get_all_resumes(self) -> List[Dict]:
        """Get all resumes (admin function)."""
        db = get_db()
        try:
            resumes = db.query(Resume).order_by(Resume.upload_date.desc()).all()
            return [
                {
                    "resume_id": r.resume_id,
                    "file_name": r.file_name,
                    "upload_date": r.upload_date.strftime("%Y-%m-%d %H:%M") if r.upload_date else "N/A",
                    "user_id": r.user_id,
                }
                for r in resumes
            ]
        finally:
            db.close()
