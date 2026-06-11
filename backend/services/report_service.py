"""
Report generation service for creating downloadable PDF reports.
"""

import os
from typing import Dict
from datetime import datetime
from fpdf import FPDF
from backend.config.settings import REPORTS_DIR


class ReportService:
    """Service for generating PDF analysis reports."""

    def __init__(self):
        """Initialize report service."""
        os.makedirs(REPORTS_DIR, exist_ok=True)

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
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 15, "Resume Analysis Report", ln=True, align="C")
        pdf.ln(5)

        # Metadata
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f"Resume: {resume_name}", ln=True)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(10)

        # ATS Score
        ats_score = analysis_data.get("ats_score", {})
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"ATS Score: {ats_score.get('overall_score', 'N/A')}/100", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f"Grade: {ats_score.get('grade', 'N/A')}", ln=True)
        pdf.ln(5)

        # Component Scores
        components = ats_score.get("component_scores", {})
        if components:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Score Breakdown:", ln=True)
            pdf.set_font("Arial", "", 10)
            for key, value in components.items():
                label = key.replace("_", " ").title()
                pdf.cell(0, 7, f"  - {label}: {round(value, 1)}/100", ln=True)
        pdf.ln(5)

        # Job Match
        job_match = analysis_data.get("job_match", {})
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Job Match: {job_match.get('overall_match', 'N/A')}%", ln=True)
        pdf.ln(5)

        # Strengths
        strengths = analysis_data.get("strengths", [])
        if strengths:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Strengths:", ln=True)
            pdf.set_font("Arial", "", 10)
            for s in strengths:
                pdf.cell(0, 7, f"  + {s}", ln=True)
        pdf.ln(5)

        # Weaknesses
        weaknesses = analysis_data.get("weaknesses", [])
        if weaknesses:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Areas for Improvement:", ln=True)
            pdf.set_font("Arial", "", 10)
            for w in weaknesses:
                pdf.cell(0, 7, f"  - {w}", ln=True)
        pdf.ln(5)

        # Skill Gap
        skill_gap = job_match.get("skill_gap", {})
        if skill_gap:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Skill Gap Analysis:", ln=True)
            pdf.set_font("Arial", "", 10)

            matched = skill_gap.get("matched", [])
            if matched:
                pdf.cell(0, 7, f"  Matched Skills: {', '.join(matched)}", ln=True)
            
            missing = skill_gap.get("missing", [])
            if missing:
                pdf.cell(0, 7, f"  Missing Skills: {', '.join(missing)}", ln=True)

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

        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 15, "Skill Gap Report", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f"Resume: {resume_name}", ln=True)
        pdf.cell(0, 8, f"Target Role: {job_title}", ln=True)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(10)

        matched = skill_gap.get("matched", [])
        missing = skill_gap.get("missing", [])
        extra = skill_gap.get("extra", [])

        # Matched Skills
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Matched Skills ({len(matched)}):", ln=True)
        pdf.set_font("Arial", "", 10)
        for s in matched:
            pdf.cell(0, 7, f"  [OK] {s}", ln=True)
        pdf.ln(5)

        # Missing Skills
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Missing Skills ({len(missing)}):", ln=True)
        pdf.set_font("Arial", "", 10)
        for s in missing:
            pdf.cell(0, 7, f"  [!] {s}", ln=True)
        pdf.ln(5)

        # Additional Skills
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Additional Skills ({len(extra)}):", ln=True)
        pdf.set_font("Arial", "", 10)
        for s in extra:
            pdf.cell(0, 7, f"  [+] {s}", ln=True)

        file_name = f"skill_gap_{resume_name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(REPORTS_DIR, file_name)
        pdf.output(file_path)

        return file_path
