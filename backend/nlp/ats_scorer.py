"""
ATS (Applicant Tracking System) Score Calculator.
Calculates a comprehensive ATS score based on multiple factors.
"""

import re
from typing import Dict, List
from backend.config.settings import ATS_WEIGHTS
from backend.nlp.skill_extractor import SkillExtractor
from backend.nlp.resume_parser import SECTION_PATTERNS


class ATSScorer:
    """Calculate ATS compatibility score for resumes."""

    def __init__(self):
        """Initialize ATS scorer."""
        self.skill_extractor = SkillExtractor()
        self.weights = ATS_WEIGHTS

    def calculate_ats_score(self, resume_text: str, job_description: str = "", required_skills: List[str] = None) -> Dict:
        """
        Calculate comprehensive ATS score.
        
        Args:
            resume_text: The resume text content.
            job_description: Optional job description for comparison.
            required_skills: Optional list of required skills.
        
        Returns:
            Dictionary containing overall score and component scores.
        """
        scores = {
            "format_score": self._calculate_format_score(resume_text),
            "keyword_density": self._calculate_keyword_density(resume_text, job_description),
            "skills_coverage": self._calculate_skills_coverage(resume_text, required_skills),
            "experience_relevance": self._calculate_experience_relevance(resume_text, job_description),
            "education_match": self._calculate_education_match(resume_text),
            "section_completeness": self._calculate_section_completeness(resume_text),
        }

        # Calculate weighted total
        total_score = sum(
            scores[key] * self.weights[key] for key in scores
        )
        total_score = min(100, max(0, round(total_score)))

        return {
            "overall_score": total_score,
            "component_scores": scores,
            "grade": self._get_grade(total_score),
        }

    def _calculate_format_score(self, text: str) -> float:
        """
        Score resume formatting (0-100).
        Checks for proper structure, readability, and formatting.
        """
        score = 0
        
        # Check for reasonable length (300-3000 words is ideal)
        word_count = len(text.split())
        if 300 <= word_count <= 3000:
            score += 30
        elif 100 <= word_count < 300 or 3000 < word_count <= 5000:
            score += 15
        
        # Check for line breaks (proper formatting)
        lines = text.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        if len(non_empty_lines) > 10:
            score += 20
        
        # Check for bullet points or list formatting
        bullet_patterns = [r"[•\-\*]\s", r"^\d+[\.\)]\s"]
        for pattern in bullet_patterns:
            if re.search(pattern, text, re.MULTILINE):
                score += 15
                break
        
        # Check for consistent formatting (no excessive whitespace)
        if not re.search(r"\n{4,}", text):
            score += 15
        
        # Check for presence of contact information
        has_email = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))
        has_phone = bool(re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text))
        if has_email:
            score += 10
        if has_phone:
            score += 10
        
        return min(100, score)

    def _calculate_keyword_density(self, resume_text: str, job_description: str) -> float:
        """
        Score keyword density relative to job description (0-100).
        """
        if not job_description:
            # Without job description, check for general professional keywords
            professional_keywords = [
                "developed", "managed", "implemented", "designed", "led",
                "created", "improved", "achieved", "built", "delivered",
                "collaborated", "analyzed", "optimized", "reduced", "increased",
            ]
            resume_lower = resume_text.lower()
            found = sum(1 for kw in professional_keywords if kw in resume_lower)
            return min(100, (found / len(professional_keywords)) * 100)

        # Extract meaningful words from job description
        job_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", job_description.lower()))
        # Remove common stop words
        stop_words = {"the", "and", "for", "are", "but", "not", "you", "all",
                      "can", "had", "her", "was", "one", "our", "out", "has",
                      "have", "with", "this", "that", "will", "from", "they"}
        job_words -= stop_words

        if not job_words:
            return 50

        resume_lower = resume_text.lower()
        matched = sum(1 for word in job_words if word in resume_lower)
        percentage = (matched / len(job_words)) * 100

        return min(100, round(percentage))

    def _calculate_skills_coverage(self, resume_text: str, required_skills: List[str] = None) -> float:
        """
        Score skills coverage (0-100).
        """
        resume_skills = self.skill_extractor.extract_skills(resume_text)

        if required_skills:
            # Compare against required skills
            return self.skill_extractor.calculate_skill_match_percentage(
                resume_skills, required_skills
            )
        else:
            # General scoring based on number of identified skills
            skill_count = len(resume_skills)
            if skill_count >= 15:
                return 100
            elif skill_count >= 10:
                return 80
            elif skill_count >= 5:
                return 60
            elif skill_count >= 3:
                return 40
            else:
                return 20

    def _calculate_experience_relevance(self, resume_text: str, job_description: str) -> float:
        """
        Score experience relevance (0-100).
        """
        score = 0
        text_lower = resume_text.lower()

        # Check for experience section
        if re.search(r"(?i)(experience|employment|work\s*history)", resume_text):
            score += 30

        # Check for action verbs (indicates good experience descriptions)
        action_verbs = [
            "developed", "managed", "implemented", "designed", "led",
            "created", "built", "improved", "achieved", "delivered",
            "maintained", "coordinated", "established", "supervised",
            "analyzed", "optimized", "reduced", "increased", "launched",
        ]
        verbs_found = sum(1 for verb in action_verbs if verb in text_lower)
        score += min(30, verbs_found * 5)

        # Check for quantifiable achievements
        if re.search(r"\d+%", resume_text) or re.search(r"\$\d+", resume_text):
            score += 20

        # Check for year/duration mentions
        if re.search(r"\d{4}\s*[-–]\s*(\d{4}|present|current)", text_lower):
            score += 20

        return min(100, score)

    def _calculate_education_match(self, resume_text: str) -> float:
        """
        Score education section (0-100).
        """
        score = 0
        text_lower = resume_text.lower()

        # Check for education section
        if re.search(r"(?i)(education|academic|qualification)", resume_text):
            score += 30

        # Check for degree mentions
        degrees = ["bachelor", "master", "phd", "doctorate", "associate", "b.s.", "m.s.",
                   "b.a.", "m.a.", "mba", "b.tech", "m.tech", "b.e.", "m.e."]
        for degree in degrees:
            if degree in text_lower:
                score += 25
                break

        # Check for university/college mention
        if re.search(r"(?i)(university|college|institute|school)", resume_text):
            score += 20

        # Check for GPA mention
        if re.search(r"(?i)(gpa|cgpa|grade)", resume_text):
            score += 15

        # Check for graduation year
        if re.search(r"20\d{2}", resume_text):
            score += 10

        return min(100, score)

    def _calculate_section_completeness(self, resume_text: str) -> float:
        """
        Score section completeness (0-100).
        """
        essential_sections = ["education", "experience", "skills"]
        optional_sections = ["summary", "projects", "certifications", "achievements"]

        found_essential = 0
        found_optional = 0

        for section in essential_sections:
            pattern = SECTION_PATTERNS.get(section)
            if pattern and re.search(pattern, resume_text):
                found_essential += 1

        for section in optional_sections:
            pattern = SECTION_PATTERNS.get(section)
            if pattern and re.search(pattern, resume_text):
                found_optional += 1

        # Essential sections weighted more heavily
        essential_score = (found_essential / len(essential_sections)) * 60
        optional_score = (found_optional / len(optional_sections)) * 40

        return min(100, round(essential_score + optional_score))

    def _get_grade(self, score: int) -> str:
        """Get letter grade from score."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"
