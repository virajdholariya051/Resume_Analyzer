"""
Report generation service for creating downloadable PDF reports.

Uses fpdf2 with the built-in Helvetica core font and the modern
``new_x``/``new_y`` line-break API (the legacy ``ln``/``Arial`` usage was
deprecated and scheduled for removal).
"""

import os
from typing import Dict
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from backend.config.settings import REPORTS_DIR

# Core font that ships with fpdf2 (avoids the deprecated Arial substitution).
_FONT = "Helvetica"


class ReportService:
    """Service for generating PDF analysis reports."""

    def __init__(self):
        """Initialize report service."""
        os.makedirs(REPORTS_DIR, exist_ok=True)

    @staticmethod
    def _line(pdf: FPDF, height: float, text: str, style: str = "", size: int = 10) -> None:
        """Write a full-width line of text followed by a line break."""
        pdf.set_font(_FONT, style, size)
        pdf.cell(0, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def generate_ats_report(self, analysis_data: Dict, resume_name: str) -> str:
        """
        Generate a PDF ATS analysis report.

        Args:
            analysis_data: Dictionary containing analysis results.
            resume_name: Name of the analyzed resume.

        Returns:
            Path to the generated PDF file.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title
        pdf.set_font(_FONT, "B", 18)
        pdf.cell(0, 15, "Resume Analysis Report",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(5)

        # Metadata
        self._line(pdf, 8, f"Resume: {resume_name}")
        analysis_type = analysis_data.get("analysis_type", "Resume + Job Description")
        self._line(pdf, 8, f"Analysis Type: {analysis_type}")
        self._line(pdf, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        pdf.ln(6)

        # ATS Score
        ats_score = analysis_data.get("ats_score", {})
        self._line(pdf, 10, f"ATS Score: {ats_score.get('overall_score', 'N/A')}/100", style="B", size=14)
        self._line(pdf, 8, f"Grade: {ats_score.get('grade', 'N/A')}")
        pdf.ln(3)

        # Resume quality (Resume Only workflow)
        if "quality_score" in analysis_data:
            self._line(pdf, 8, f"Resume Quality Score: {analysis_data.get('quality_score', 'N/A')}/100")
            pdf.ln(2)

        # Component Scores
        components = ats_score.get("component_scores", {})
        if components:
            self._line(pdf, 10, "Score Breakdown:", style="B", size=12)
            for key, value in components.items():
                label = key.replace("_", " ").title()
                self._line(pdf, 7, f"  - {label}: {round(value, 1)}/100")
        pdf.ln(3)

        # Job Match (only when present)
        job_match = analysis_data.get("job_match")
        if job_match:
            self._line(pdf, 10, f"Job Match: {job_match.get('overall_match', 'N/A')}%", style="B", size=14)
            pdf.ln(3)

        # Strengths
        strengths = analysis_data.get("strengths", [])
        if strengths:
            self._line(pdf, 10, "Strengths:", style="B", size=12)
            for s in strengths:
                self._line(pdf, 7, f"  + {s}")
            pdf.ln(3)

        # Weaknesses
        weaknesses = analysis_data.get("weaknesses", [])
        if weaknesses:
            self._line(pdf, 10, "Areas for Improvement:", style="B", size=12)
            for w in weaknesses:
                self._line(pdf, 7, f"  - {w}")
            pdf.ln(3)

        # Recommendations
        recommendations = analysis_data.get("recommendations", [])
        if recommendations:
            self._line(pdf, 10, "Recommendations:", style="B", size=12)
            for r in recommendations:
                self._line(pdf, 7, f"  * {r}")
            pdf.ln(3)

        # Skill Gap
        skill_gap = (job_match or {}).get("skill_gap", {})
        if skill_gap:
            self._line(pdf, 10, "Skill Gap Analysis:", style="B", size=12)
            matched = skill_gap.get("matched", [])
            if matched:
                self._line(pdf, 7, f"  Matched Skills: {', '.join(matched)}")
            missing = skill_gap.get("missing", [])
            if missing:
                self._line(pdf, 7, f"  Missing Skills: {', '.join(missing)}")

        # Save PDF
        file_name = f"report_{resume_name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(REPORTS_DIR, file_name)
        pdf.output(file_path)

        return file_path

    def generate_skill_gap_report(self, skill_gap: Dict, resume_name: str, job_title: str) -> str:
        """Generate a skill gap analysis report."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font(_FONT, "B", 18)
        pdf.cell(0, 15, "Skill Gap Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(5)

        self._line(pdf, 8, f"Resume: {resume_name}")
        self._line(pdf, 8, f"Target Role: {job_title}")
        self._line(pdf, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        pdf.ln(6)

        matched = skill_gap.get("matched", [])
        missing = skill_gap.get("missing", [])
        extra = skill_gap.get("extra", [])

        # Matched Skills
        self._line(pdf, 10, f"Matched Skills ({len(matched)}):", style="B", size=12)
        for s in matched:
            self._line(pdf, 7, f"  [OK] {s}")
        pdf.ln(3)

        # Missing Skills
        self._line(pdf, 10, f"Missing Skills ({len(missing)}):", style="B", size=12)
        for s in missing:
            self._line(pdf, 7, f"  [!] {s}")
        pdf.ln(3)

        # Additional Skills
        self._line(pdf, 10, f"Additional Skills ({len(extra)}):", style="B", size=12)
        for s in extra:
            self._line(pdf, 7, f"  [+] {s}")

        file_name = f"skill_gap_{resume_name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(REPORTS_DIR, file_name)
        pdf.output(file_path)

        return file_path
