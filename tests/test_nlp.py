"""Unit tests for the NLP pipeline: parser, skill extractor, ATS, job matcher."""

from backend.nlp.resume_parser import ResumeParser
from backend.nlp.skill_extractor import SkillExtractor
from backend.nlp.ats_scorer import ATSScorer
from backend.nlp.job_matcher import JobMatcher


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------
def test_skill_extraction_finds_known_skills(sample_text):
    extractor = SkillExtractor()
    skills = extractor.extract_skills(sample_text)
    assert "Python" in skills
    assert "AWS" in skills
    assert "Leadership" in skills


def test_skill_extraction_empty_text():
    extractor = SkillExtractor()
    assert extractor.extract_skills("") == []


def test_skill_gap_analysis():
    extractor = SkillExtractor()
    gap = extractor.get_skill_gap(["Python", "SQL"], ["Python", "AWS"])
    assert "Python" in gap["matched"]
    assert "AWS" in gap["missing"]
    assert "SQL" in gap["extra"]


def test_skill_match_percentage():
    extractor = SkillExtractor()
    pct = extractor.calculate_skill_match_percentage(["Python", "SQL"], ["Python", "SQL", "AWS", "Docker"])
    assert pct == 50.0
    assert extractor.calculate_skill_match_percentage([], []) == 0.0


def test_categorize_skills(sample_text):
    extractor = SkillExtractor()
    cats = extractor.categorize_skills(sample_text)
    assert "Python" in cats["technical"]
    assert "Leadership" in cats["soft"]


# ---------------------------------------------------------------------------
# Resume parser
# ---------------------------------------------------------------------------
def test_resume_parser_extracts_contact(sample_text):
    parser = ResumeParser()
    parsed = parser.parse_resume(sample_text)
    assert parsed["email"] == "john.doe@example.com"
    assert parsed["phone"] is not None
    assert "education" in parsed["sections_found"]
    assert "skills" in parsed["sections_found"]


def test_resume_parser_handles_empty_text():
    parser = ResumeParser()
    parsed = parser.parse_resume("")
    assert parsed["email"] is None
    assert isinstance(parsed["skills"], list)


# ---------------------------------------------------------------------------
# ATS scorer
# ---------------------------------------------------------------------------
def test_ats_score_within_bounds(sample_text):
    scorer = ATSScorer()
    result = scorer.calculate_ats_score(sample_text)
    assert 0 <= result["overall_score"] <= 100
    assert result["grade"]
    assert set(result["component_scores"]).issuperset(
        {"format_score", "skills_coverage", "section_completeness"}
    )


def test_ats_score_with_job_description(sample_text):
    scorer = ATSScorer()
    result = scorer.calculate_ats_score(
        sample_text, "Looking for a Python developer with AWS and Docker.",
        ["Python", "AWS", "Docker"],
    )
    assert 0 <= result["overall_score"] <= 100


def test_ats_sparse_resume_scores_low(sparse_text, sample_text):
    scorer = ATSScorer()
    sparse = scorer.calculate_ats_score(sparse_text)["overall_score"]
    rich = scorer.calculate_ats_score(sample_text)["overall_score"]
    assert sparse < rich


# ---------------------------------------------------------------------------
# Job matcher
# ---------------------------------------------------------------------------
def test_job_match_structure(sample_text):
    matcher = JobMatcher()
    result = matcher.calculate_match(
        sample_text, "Python developer needed with AWS, Docker, SQL.",
        ["Python", "AWS", "Docker", "SQL"],
    )
    assert 0 <= result["overall_match"] <= 100
    assert "skill_gap" in result
    assert "recommendation" in result
    assert set(result["component_scores"]).issuperset(
        {"skill_match", "keyword_match", "experience_match", "education_match"}
    )


def test_strengths_and_weaknesses(sample_text):
    matcher = JobMatcher()
    strengths = matcher.generate_strengths(sample_text, ["Python", "AWS"])
    weaknesses = matcher.generate_weaknesses(sample_text, ["Python", "Kubernetes"])
    assert isinstance(strengths, list) and strengths
    assert isinstance(weaknesses, list)
    # Kubernetes is missing from the resume -> should surface as a weakness
    assert any("kubernetes" in w.lower() for w in weaknesses)


def test_certification_match(sample_text):
    matcher = JobMatcher()
    score = matcher.calculate_certification_match(sample_text, "AWS certification required")
    assert 0 <= score <= 100
    assert score > 0  # resume mentions AWS Certified
