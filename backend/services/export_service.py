"""
Export service for generating candidate reports in CSV, Excel, and PDF formats.
"""

import io
from typing import Dict, List
from datetime import datetime
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Core font that ships with fpdf2 (avoids the deprecated Arial substitution).
_FONT = "Helvetica"


# Standard export columns
EXPORT_COLUMNS = [
    ("rank", "Rank"),
    ("candidate_name", "Candidate Name"),
    ("ats_score", "ATS Score"),
    ("job_match_percentage", "Match %"),
    ("rank_score", "Overall Score"),
    ("status", "Status"),
]


class ExportService:
    """Generate downloadable candidate reports."""

    def _to_dataframe(self, candidates: List[Dict]) -> pd.DataFrame:
        """Build a tidy DataFrame from ranked candidate dicts."""
        rows = []
        for c in candidates:
            rows.append({label: c.get(key, "") for key, label in EXPORT_COLUMNS})
        return pd.DataFrame(rows)

    def to_csv(self, candidates: List[Dict]) -> bytes:
        """Export candidates to CSV bytes."""
        df = self._to_dataframe(candidates)
        return df.to_csv(index=False).encode("utf-8")

    def to_excel(self, candidates: List[Dict]) -> bytes:
        """Export candidates to an Excel (.xlsx) byte stream."""
        df = self._to_dataframe(candidates)
        buffer = io.BytesIO()
        # openpyxl is the default engine for .xlsx
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Candidates")
        buffer.seek(0)
        return buffer.getvalue()

    def to_pdf(self, candidates: List[Dict], title: str = "Candidate Ranking Report") -> bytes:
        """Export candidates to a PDF byte stream."""
        pdf = FPDF(orientation="L")  # landscape for the table
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font(_FONT, "B", 16)
        pdf.cell(0, 12, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font(_FONT, "", 9)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

        # Header
        headers = [label for _, label in EXPORT_COLUMNS]
        col_widths = [20, 80, 30, 30, 35, 40]

        pdf.set_font(_FONT, "B", 10)
        pdf.set_fill_color(102, 126, 234)
        pdf.set_text_color(255, 255, 255)
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 9, str(h), border=1, align="C", fill=True)
        pdf.ln()

        # Rows
        pdf.set_font(_FONT, "", 9)
        pdf.set_text_color(0, 0, 0)
        for c in candidates:
            values = [str(c.get(key, "")) for key, _ in EXPORT_COLUMNS]
            for w, val in zip(col_widths, values):
                # truncate long candidate names to fit
                text = val if len(val) <= 45 else val[:42] + "..."
                pdf.cell(w, 8, text, border=1)
            pdf.ln()

        # fpdf2 returns a bytearray from output() when no filename is given.
        return bytes(pdf.output())
