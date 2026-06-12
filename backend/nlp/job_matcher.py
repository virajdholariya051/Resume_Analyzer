"""
Job Match Engine - Calculates match percentage between resume and job description.
"""

import re
from typing import Dict, List
from backend.config.settings import JOB_MATCH_WEIGHTS
from backend.nlp.skill_extractor import SkillExtractor


class JobMatcher:
    """Calculate job match percentage between resume and job description."""

    def __init__(self):
        """Initialize job matcher."""
        self.skill_extractor = SkillExtractor()
        self.weights = JOB_MATCH_WEIGHTS

    def calculate_match(self, resume_text: str, job_description: str, required_skills: List[str]) -> Dict:
        """
        Calculate comprehensive job match percentage.
        
        Args:
            resume_text: The resume text content.
            job_description: The job description text.
            required_skills: List of required skills for the job.
        
        Returns:
            Dictionary containing overall match and component scores.
        """
        scores = {
            "skill_match": self._calculate_skill_match(resume_text, required_skills),
            "keyword_match": self._calculate_keyword_match(resume_text, job_description),
            "experience_match": self._calculate_experience_match(resume_text, job_description),
            "education_match": self._calculate_education_match(resume_text, job_description),
        }

        # Weighted total
        total_match = sum(
            scores[key] * self.weights[key] for key in scores
        )
        total_match = min(100, max(0, round(total_match)))

        # Generate skill gap analysis
        resume_skills = self.skill_extractor.extract_skills(resume_text)
        skill_gap = self.skill_extractor.get_skill_gap(resume_skills, required_skills)

        return {
            "overall_match": total_match,
            "component_scores": scores,
            "skill_gap": skill_gap,
            "recommendation": self._get_recommendation(total_match),
        }

    def _calculate_skill_match(self, resume_text: str, required_skills: List[str]) -> float:
        """Calculate skill match percentage."""
        if not required_skills:
            return 50.0

        resume_skills = self.skill_extractor.extract_skills(resume_text)
        return self.skill_extractor.calculate_skill_match_percentage(
            resume_skills, required_skills
        )

    def _calculate_keyword_match(self, resume_text: str, job_description: str) -> float:
        """Calculate keyword match percentage."""
        if not job_description:
            return 50.0

        # Extract meaningful keywords from job description
        job_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", job_description.lower()))
        stop_words = {"the", "and", "for", "are", "but", "not", "you", "all",
                      "can", "had", "her", "was", "one", "our", "out", "has",
                      "have", "with", "this", "that", "will", "from", "they",
                      "been", "some", "them", "than", "other", "into", "more",
                      "also", "about", "must", "should", "would", "could"}
        job_words -= stop_words

        if not job_words:
            return 50.0

        resume_lower = resume_text.lower()
        matched = sum(1 for word in job_words if word in resume_lower)

        return min(100, round((matched / len(job_words)) * 100))

    def _calculate_experience_match(self, resume_text: str, job_description: str) -> float:
        """Calculate experience relevance match."""
        score = 0
        text_lower = resume_text.lower()
        job_lower = job_description.lower()

        # Check for years of experience
        resume_years = re.findall(r"(\d+)\+?\s*years?", text_lower)
        job_years = re.findall(r"(\d+)\+?\s*years?", job_lower)

        if resume_years:
            score += 30
            if job_years:
                max_resume_years = max(int(y) for y in resume_years)
                required_years = min(int(y) for y in job_years)
                if max_resume_years >= required_years:
                    score += 40
                else:
                    score += 20
        
        # Check for relevant action verbs
        action_verbs = ["developed", "managed", "implemented", "designed", "led",
                        "built", "created", "maintained", "deployed", "optimized"]
        verbs_found = sum(1 for v in action_verbs if v in text_lower)
        score += min(30, verbs_found * 5)

        return min(100, score)

    def _calculate_education_match(self, resume_text: str, job_description: str) -> float:
        """Calculate education match."""
        score = 50  # Base score
        text_lower = resume_text.lower()
        job_lower = job_description.lower()

        # Check if job requires specific degree
        degree_levels = {
            "phd": 4, "doctorate": 4,
            "master": 3, "m.s.": 3, "m.a.": 3, "mba": 3,
            "bachelor": 2, "b.s.": 2, "b.a.": 2, "b.tech": 2,
            "associate": 1,
        }

        job_required_level = 0
        resume_level = 0

        for degree, level in degree_levels.items():
            if degree in job_lower:
                job_required_level = max(job_required_level, level)
            if degree in text_lower:
                resume_level = max(resume_level, level)

        if job_required_level > 0:
            if resume_level >= job_required_level:
                score = 100
            elif resume_level == job_required_level - 1:
                score = 70
            else:
                score = 40
        elif resume_level > 0:
            score = 80

        return score

    def calculate_certification_match(self, resume_text: str, job_description: str = "") -> float:
        """
        Calculate certification match score (0-100).

        Rewards presence of certifications and overlap with any certifications
        mentioned in the job description.
        """
        text_lower = resume_text.lower()
        has_cert_section = bool(re.search(r"(?i)(certif|license|credential)", resume_text))

        if not has_cert_section:
            return 0.0

        score = 50.0  # base for having any certifications

        # Common certification keywords
        cert_keywords = [
            "aws certified", "azure", "gcp", "pmp", "scrum master", "cissp",
            "comptia", "cisco", "ccna", "oracle certified", "google cloud",
            "kubernetes", "terraform", "tensorflow", "data science", "six sigma",
        ]
        found = sum(1 for kw in cert_keywords if kw in text_lower)
        score += min(30, found * 10)

        # Bonus if job description mentions certifications and resume has them
        if job_description and re.search(r"(?i)(certif|license)", job_description):
            score += 20

        return min(100.0, score)

    def _get_recommendation(self, match_percentage: int) -> str:
        """Get recommendation based on match percentage."""
        if match_percentage >= 80:
            return "Excellent match! Your resume is well-suited for this position."
        elif match_percentage >= 60:
            return "Good match. Consider enhancing skills in gap areas to strengthen your application."
        elif match_percentage >= 40:
            return "Moderate match. You may need to acquire additional skills or tailor your resume more."
        else:
            return "Low match. This role may require significant skill development or a different approach."

    def generate_strengths(self, resume_text: str, required_skills: List[str]) -> List[str]:
        """Generate list of resume strengths."""
        strengths = []
        resume_skills = self.skill_extractor.extract_skills(resume_text)
        categorized = self.skill_extractor.categorize_skills(resume_text)

        if len(categorized["technical"]) >= 5:
            strengths.append("Strong technical skill set")
        if len(categorized["soft"]) >= 3:
            strengths.append("Good soft skills demonstrated")
        if re.search(r"(?i)(experience|employment|work\s*history)", resume_text):
            strengths.append("Relevant work experience included")
        if re.search(r"\d+%|\$\d+", resume_text):
            strengths.append("Quantifiable achievements present")
        if re.search(r"(?i)(certif|license)", resume_text):
            strengths.append("Professional certifications listed")
        if required_skills:
            match_pct = self.skill_extractor.calculate_skill_match_percentage(resume_skills, required_skills)
            if match_pct >= 60:
                strengths.append("Good coverage of required skills")

        # Check for well-structured resume
        from backend.nlp.resume_parser import SECTION_PATTERNS
        sections_found = sum(1 for p in SECTION_PATTERNS.values() if re.search(p, resume_text))
        if sections_found >= 4:
            strengths.append("Well-structured resume with clear sections")

        if not strengths:
            strengths.append("Resume submitted for review")

        return strengths

    def generate_weaknesses(self, resume_text: str, required_skills: List[str]) -> List[str]:
        """Generate list of resume weaknesses/areas for improvement."""
        weaknesses = []
        resume_skills = self.skill_extractor.extract_skills(resume_text)
        
        if required_skills:
            skill_gap = self.skill_extractor.get_skill_gap(resume_skills, required_skills)
            if skill_gap["missing"]:
                missing_str = ", ".join(skill_gap["missing"][:5])
                weaknesses.append(f"Missing key skills: {missing_str}")

        if not re.search(r"(?i)(summary|objective|profile)", resume_text):
            weaknesses.append("No professional summary or objective section")

        if not re.search(r"\d+%|\$\d+", resume_text):
            weaknesses.append("Lacks quantifiable achievements")

        word_count = len(resume_text.split())
        if word_count < 200:
            weaknesses.append("Resume content may be too brief")
        elif word_count > 3000:
            weaknesses.append("Resume may be too lengthy for ATS systems")

        if not re.search(r"(?i)(certif|license)", resume_text):
            weaknesses.append("No certifications or licenses mentioned")

        # Check for action verbs
        action_verbs = ["developed", "managed", "implemented", "led", "created", "built"]
        verbs_found = sum(1 for v in action_verbs if v in resume_text.lower())
        if verbs_found < 3:
            weaknesses.append("Limited use of action verbs in experience descriptions")

        if not weaknesses:
            weaknesses.append("No major issues detected")

        return weaknesses
