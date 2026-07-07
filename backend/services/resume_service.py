"""
Resume service handling upload, storage, retrieval, and candidate management.
"""

import os
import hashlib
from typing import Dict, List, Optional
from database.database import get_db
from database.schema import Resume, Skill, resume_skills_table
from backend.utils.file_parser import save_uploaded_file, extract_text, validate_file
from backend.nlp.skill_extractor import SkillExtractor
from backend.nlp.resume_parser import ResumeParser
from backend.config.settings import UPLOAD_DIR


# Valid candidate workflow statuses
CANDIDATE_STATUSES = ["New", "Under Review", "Shortlisted", "Rejected"]


class ResumeService:
    """Service class for resume operations."""

    def __init__(self):
        """Initialize resume service."""
        self.skill_extractor = SkillExtractor()
        self.resume_parser = ResumeParser()

    # ------------------------------------------------------------------ #
    # Upload
    # ------------------------------------------------------------------ #
    def upload_resume(self, uploaded_file, user_id: int) -> Dict:
        """
        Process and store a single uploaded resume.

        Returns:
            Dictionary with operation result.
        """
        validation = validate_file(uploaded_file.name, uploaded_file.size)
        if not validation["valid"]:
            return {"success": False, "message": validation["message"]}

        file_path = save_uploaded_file(uploaded_file, UPLOAD_DIR)
        if not file_path:
            return {"success": False, "message": "Failed to save file."}

        resume_text = extract_text(file_path)
        if not resume_text:
            if os.path.exists(file_path):
                os.remove(file_path)
            return {"success": False, "message": "Failed to extract text. The file may be empty or corrupted."}

        return self._persist_resume(uploaded_file.name, resume_text, user_id)

    def bulk_upload_resumes(self, uploaded_files: List, user_id: int, progress_callback=None) -> Dict:
        """
        Process and store multiple uploaded resumes (recruiter bulk upload).

        Args:
            uploaded_files: List of Streamlit UploadedFile objects.
            user_id: ID of the uploading recruiter.
            progress_callback: Optional callable(current, total, filename) for progress UI.

        Returns:
            Summary dictionary with per-file results.
        """
        results = {
            "total": len(uploaded_files),
            "succeeded": 0,
            "duplicates": 0,
            "failed": 0,
            "details": [],
        }

        for idx, uploaded_file in enumerate(uploaded_files, start=1):
            if progress_callback:
                progress_callback(idx, len(uploaded_files), uploaded_file.name)

            validation = validate_file(uploaded_file.name, uploaded_file.size)
            if not validation["valid"]:
                results["failed"] += 1
                results["details"].append({"file": uploaded_file.name, "status": "failed", "message": validation["message"]})
                continue

            try:
                raw_bytes = uploaded_file.getbuffer()
                file_hash = hashlib.sha256(bytes(raw_bytes)).hexdigest()
            except Exception:
                file_hash = None

            # Duplicate detection by content hash
            if file_hash and self._hash_exists(file_hash, user_id):
                results["duplicates"] += 1
                results["details"].append({"file": uploaded_file.name, "status": "duplicate", "message": "Duplicate resume skipped."})
                continue

            file_path = save_uploaded_file(uploaded_file, UPLOAD_DIR)
            if not file_path:
                results["failed"] += 1
                results["details"].append({"file": uploaded_file.name, "status": "failed", "message": "Could not save file."})
                continue

            resume_text = extract_text(file_path)
            if not resume_text:
                if os.path.exists(file_path):
                    os.remove(file_path)
                results["failed"] += 1
                results["details"].append({"file": uploaded_file.name, "status": "failed", "message": "Text extraction failed."})
                continue

            persist = self._persist_resume(uploaded_file.name, resume_text, user_id, file_hash=file_hash)
            if persist["success"]:
                results["succeeded"] += 1
                results["details"].append({"file": uploaded_file.name, "status": "success", "message": "Uploaded & processed."})
            else:
                results["failed"] += 1
                results["details"].append({"file": uploaded_file.name, "status": "failed", "message": persist["message"]})

        return results

    def _hash_exists(self, file_hash: str, user_id: int) -> bool:
        """Check whether a resume with the given content hash already exists for the user."""
        db = get_db()
        try:
            return db.query(Resume).filter(
                Resume.file_hash == file_hash,
                Resume.user_id == user_id,
            ).first() is not None
        finally:
            db.close()

    def _persist_resume(self, file_name: str, resume_text: str, user_id: int, file_hash: Optional[str] = None) -> Dict:
        """Parse a resume and store it (plus extracted skills) in the database."""
        parsed = self.resume_parser.parse_resume(resume_text)

        db = get_db()
        try:
            resume = Resume(
                file_name=file_name,
                resume_text=resume_text,
                user_id=user_id,
                file_hash=file_hash,
                candidate_name=parsed.get("name"),
                candidate_email=parsed.get("email"),
                status="New",
                education=parsed.get("education"),
                experience=parsed.get("experience"),
                certifications=parsed.get("certifications"),
                projects=parsed.get("projects"),
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

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

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
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
                    "candidate_name": r.candidate_name or "Unknown",
                    "status": r.status or "New",
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
                    "candidate_name": resume.candidate_name or "Unknown",
                    "candidate_email": resume.candidate_email or "",
                    "status": resume.status or "New",
                    "education": resume.education or "",
                    "experience": resume.experience or "",
                    "certifications": resume.certifications or "",
                    "projects": resume.projects or "",
                }
            return None
        finally:
            db.close()

    def get_candidates(self, recruiter_id: int) -> List[Dict]:
        """Get all candidate resumes uploaded by a recruiter."""
        db = get_db()
        try:
            resumes = (
                db.query(Resume)
                .filter(Resume.user_id == recruiter_id)
                .order_by(Resume.upload_date.desc())
                .all()
            )
            return [
                {
                    "resume_id": r.resume_id,
                    "file_name": r.file_name,
                    "candidate_name": r.candidate_name or "Unknown",
                    "candidate_email": r.candidate_email or "",
                    "status": r.status or "New",
                    "upload_date": r.upload_date.strftime("%Y-%m-%d %H:%M") if r.upload_date else "N/A",
                    "resume_text": r.resume_text,
                }
                for r in resumes
            ]
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Status management (shortlisting workflow)
    # ------------------------------------------------------------------ #
    def update_status(self, resume_id: int, status: str) -> Dict:
        """Update candidate workflow status."""
        if status not in CANDIDATE_STATUSES:
            return {"success": False, "message": f"Invalid status. Allowed: {', '.join(CANDIDATE_STATUSES)}"}

        db = get_db()
        try:
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                return {"success": False, "message": "Resume not found."}
            resume.status = status
            db.commit()
            return {"success": True, "message": f"Status updated to '{status}'."}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating status: {str(e)}"}
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Deletion
    # ------------------------------------------------------------------ #
    def delete_resume(self, resume_id: int) -> Dict:
        """Delete a resume by ID."""
        db = get_db()
        try:
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                return {"success": False, "message": "Resume not found."}

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
                    "candidate_name": r.candidate_name or "Unknown",
                    "status": r.status or "New",
                }
                for r in resumes
            ]
        finally:
            db.close()
