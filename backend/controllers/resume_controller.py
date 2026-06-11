"""
Resume controller coordinating between frontend and backend services.
"""

from typing import Dict, List, Optional
from backend.services.resume_service import ResumeService
from backend.services.analysis_service import AnalysisService
from backend.services.job_service import JobService
from backend.services.report_service import ReportService


class ResumeController:
    """Controller for resume-related operations following MVC pattern."""

    def __init__(self):
        """Initialize controller with required services."""
        self.resume_service = ResumeService()
        self.analysis_service = AnalysisService()
        self.job_service = JobService()
        self.report_service = ReportService()

    def upload_resume(self, uploaded_file, user_id: int) -> Dict:
        """Handle resume upload request."""
        return self.resume_service.upload_resume(uploaded_file, user_id)

    def get_user_resumes(self, user_id: int) -> List[Dict]:
        """Get all resumes for a user."""
        return self.resume_service.get_user_resumes(user_id)

    def get_resume(self, resume_id: int) -> Optional[Dict]:
        """Get a specific resume."""
        return self.resume_service.get_resume_by_id(resume_id)

    def delete_resume(self, resume_id: int) -> Dict:
        """Delete a resume."""
        return self.resume_service.delete_resume(resume_id)

    def analyze_resume(self, resume_id: int, job_id: int) -> Dict:
        """Run analysis on a resume against a job description."""
        return self.analysis_service.analyze_resume(resume_id, job_id)

    def get_analysis_history(self, user_id: int) -> List[Dict]:
        """Get user's analysis history."""
        return self.analysis_service.get_analysis_history(user_id)

    def get_dashboard_stats(self, user_id: int) -> Dict:
        """Get dashboard statistics."""
        return self.analysis_service.get_dashboard_stats(user_id)

    def create_job(self, title: str, description: str, skills: str = "") -> Dict:
        """Create a new job description."""
        return self.job_service.create_job(title, description, skills)

    def get_all_jobs(self) -> List[Dict]:
        """Get all job descriptions."""
        return self.job_service.get_all_jobs()

    def generate_report(self, analysis_data: Dict, resume_name: str) -> str:
        """Generate a PDF report."""
        return self.report_service.generate_ats_report(analysis_data, resume_name)
