"""
NLP-based resume parser using spaCy and regex patterns.
Extracts structured information from resume text.
"""

import re
from typing import Dict, List, Optional


# Common section headers for resume parsing
SECTION_PATTERNS = {
    "education": r"(?i)(education|academic|qualification|degree)",
    "experience": r"(?i)(experience|employment|work\s*history|professional\s*experience)",
    "skills": r"(?i)(skills|technical\s*skills|competencies|proficiencies)",
    "projects": r"(?i)(projects|personal\s*projects|academic\s*projects)",
    "certifications": r"(?i)(certifications?|certificates?|licenses?)",
    "languages": r"(?i)(languages?|linguistic)",
    "achievements": r"(?i)(achievements?|accomplishments?|awards?|honors?)",
    "summary": r"(?i)(summary|objective|profile|about\s*me)",
}

# Email pattern
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Phone pattern (various formats)
PHONE_PATTERN = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"

# Name pattern (typically first line or after specific markers)
NAME_PATTERN = r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})"


class ResumeParser:
    """Parse resume text to extract structured information."""

    def __init__(self):
        """Initialize the resume parser."""
        self.nlp = None
        self._load_nlp()

    def _load_nlp(self) -> None:
        """Load spaCy NLP model."""
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # If model not installed, use blank model
                self.nlp = spacy.blank("en")
        except ImportError:
            self.nlp = None

    def parse_resume(self, text: str) -> Dict:
        """
        Parse resume text and extract all relevant information.
        
        Args:
            text: Raw resume text.
        
        Returns:
            Dictionary with extracted resume fields.
        """
        result = {
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "skills": self._extract_skills(text),
            "education": self._extract_section(text, "education"),
            "experience": self._extract_section(text, "experience"),
            "projects": self._extract_section(text, "projects"),
            "certifications": self._extract_section(text, "certifications"),
            "languages": self._extract_languages(text),
            "achievements": self._extract_section(text, "achievements"),
            "summary": self._extract_section(text, "summary"),
            "sections_found": self._identify_sections(text),
        }
        return result

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume text."""
        lines = text.strip().split("\n")
        
        # Try first few non-empty lines
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
            # Skip lines that look like contact info
            if "@" in line or re.search(PHONE_PATTERN, line):
                continue
            # Check if it looks like a name (2-4 capitalized words)
            match = re.match(NAME_PATTERN, line)
            if match:
                return match.group(1)
        
        # Fallback: use spaCy NER if available
        if self.nlp:
            doc = self.nlp(text[:500])
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text
        
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from resume text."""
        match = re.search(EMAIL_PATTERN, text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume text."""
        match = re.search(PHONE_PATTERN, text)
        return match.group(0) if match else None

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text using keyword matching."""
        from backend.nlp.skill_extractor import SkillExtractor
        extractor = SkillExtractor()
        return extractor.extract_skills(text)

    def _extract_section(self, text: str, section: str) -> Optional[str]:
        """Extract a specific section from resume text."""
        pattern = SECTION_PATTERNS.get(section)
        if not pattern:
            return None

        lines = text.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            # Check if this line starts the target section
            if re.search(pattern, line) and not in_section:
                in_section = True
                continue
            # Check if we've hit another section header
            elif in_section:
                is_other_section = False
                for key, pat in SECTION_PATTERNS.items():
                    if key != section and re.search(pat, line):
                        is_other_section = True
                        break
                if is_other_section:
                    break
                if line.strip():
                    section_lines.append(line.strip())

        return "\n".join(section_lines) if section_lines else None

    def _extract_languages(self, text: str) -> List[str]:
        """Extract languages from resume text."""
        common_languages = [
            "English", "Spanish", "French", "German", "Chinese", "Mandarin",
            "Hindi", "Arabic", "Portuguese", "Japanese", "Korean", "Russian",
            "Italian", "Dutch", "Swedish", "Turkish", "Vietnamese", "Thai",
        ]
        
        found = []
        text_lower = text.lower()
        for lang in common_languages:
            if lang.lower() in text_lower:
                found.append(lang)
        
        return found

    def _identify_sections(self, text: str) -> List[str]:
        """Identify which sections are present in the resume."""
        found_sections = []
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, text):
                found_sections.append(section_name)
        return found_sections
