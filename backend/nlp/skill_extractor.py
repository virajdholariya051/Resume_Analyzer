"""
Skill extraction engine using predefined skill datasets.
Identifies both technical and soft skills from resume text.
"""

import re
from typing import List, Dict, Tuple
from functools import lru_cache


# Comprehensive skill database
TECHNICAL_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Ruby", "PHP",
    "Swift", "Kotlin", "Go", "Rust", "R", "MATLAB", "Scala", "Perl",
    "React", "Angular", "Vue.js", "Next.js", "Svelte", "jQuery",
    "Node.js", "Express.js", "Django", "Flask", "Spring Boot", "FastAPI",
    "ASP.NET", "Ruby on Rails", "Laravel",
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "Cassandra", "DynamoDB", "Firebase", "SQLite", "Oracle",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
    "Jenkins", "CI/CD", "Ansible", "Chef", "Puppet",
    "Git", "GitHub", "GitLab", "Bitbucket",
    "Machine Learning", "Deep Learning", "Data Science", "AI",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "OpenCV",
    "NLP", "Computer Vision", "Neural Networks",
    "HTML", "CSS", "SASS", "Bootstrap", "Tailwind CSS",
    "REST API", "GraphQL", "gRPC", "WebSocket", "Microservices",
    "Linux", "Unix", "Bash", "PowerShell",
    "Apache Kafka", "RabbitMQ", "Nginx", "Apache",
    "Hadoop", "Spark", "Tableau", "Power BI",
    "Figma", "Adobe XD", "Photoshop",
    "Agile", "Scrum", "Kanban", "Jira", "Confluence",
    "DevOps", "SRE", "MLOps", "DataOps",
    "Blockchain", "Solidity", "Web3",
    "Unity", "Unreal Engine",
    "Selenium", "Cypress", "Jest", "Pytest", "JUnit",
    "Pandas", "NumPy", "Matplotlib", "Seaborn",
]

SOFT_SKILLS = [
    "Communication", "Leadership", "Problem Solving", "Teamwork",
    "Time Management", "Critical Thinking", "Creativity", "Adaptability",
    "Project Management", "Analytical Skills", "Attention to Detail",
    "Decision Making", "Conflict Resolution", "Presentation Skills",
    "Negotiation", "Mentoring", "Collaboration", "Strategic Thinking",
    "Emotional Intelligence", "Customer Service", "Public Speaking",
    "Research", "Organization", "Multitasking", "Self-Motivation",
]


class SkillExtractor:
    """Extract skills from text using pattern matching."""

    def __init__(self):
        """Initialize with skill datasets."""
        self.technical_skills = TECHNICAL_SKILLS
        self.soft_skills = SOFT_SKILLS
        self.all_skills = TECHNICAL_SKILLS + SOFT_SKILLS

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract all skills found in the text.
        
        Args:
            text: Resume or document text.
        
        Returns:
            List of identified skill names.
        """
        return list(_cached_extract_skills(text))

    def extract_technical_skills(self, text: str) -> List[str]:
        """Extract only technical skills."""
        found = []
        text_lower = text.lower()
        for skill in self.technical_skills:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                found.append(skill)
        return list(set(found))

    def extract_soft_skills(self, text: str) -> List[str]:
        """Extract only soft/non-technical skills."""
        found = []
        text_lower = text.lower()
        for skill in self.soft_skills:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                found.append(skill)
        return list(set(found))

    def categorize_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Extract and categorize skills.
        
        Returns:
            Dictionary with 'technical' and 'soft' skill lists.
        """
        return {
            "technical": self.extract_technical_skills(text),
            "soft": self.extract_soft_skills(text),
        }

    def get_skill_gap(self, resume_skills: List[str], required_skills: List[str]) -> Dict[str, List[str]]:
        """
        Identify skill gaps between resume and job requirements.
        
        Args:
            resume_skills: Skills found in resume.
            required_skills: Skills required by job description.
        
        Returns:
            Dictionary with 'matched', 'missing', and 'extra' skills.
        """
        resume_set = {s.lower() for s in resume_skills}
        required_set = {s.lower() for s in required_skills}

        matched = [s for s in required_skills if s.lower() in resume_set]
        missing = [s for s in required_skills if s.lower() not in resume_set]
        extra = [s for s in resume_skills if s.lower() not in required_set]

        return {
            "matched": matched,
            "missing": missing,
            "extra": extra,
        }

    def calculate_skill_match_percentage(self, resume_skills: List[str], required_skills: List[str]) -> float:
        """Calculate the percentage of required skills present in resume."""
        if not required_skills:
            return 0.0
        
        resume_lower = {s.lower() for s in resume_skills}
        matched = sum(1 for s in required_skills if s.lower() in resume_lower)
        return round((matched / len(required_skills)) * 100, 1)


# Module-level cached skill extraction for performance during bulk processing.
_ALL_SKILLS = TECHNICAL_SKILLS + SOFT_SKILLS


@lru_cache(maxsize=512)
def _cached_extract_skills(text: str) -> Tuple[str, ...]:
    """Cached skill extraction. Returns a tuple (hashable) of unique skills."""
    found = []
    text_lower = text.lower()
    for skill in _ALL_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return tuple(sorted(set(found)))
