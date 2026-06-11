"""
Seed script to populate the database with initial data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_db, get_db
from database.schema import Skill, User, JobDescription
from backend.auth.auth_service import hash_password


# Predefined skills dataset
SKILLS_DATA = [
    # Technical Skills
    ("Python", "Technical"),
    ("Java", "Technical"),
    ("JavaScript", "Technical"),
    ("React", "Technical"),
    ("Node.js", "Technical"),
    ("SQL", "Technical"),
    ("MongoDB", "Technical"),
    ("AWS", "Technical"),
    ("Docker", "Technical"),
    ("Kubernetes", "Technical"),
    ("Git", "Technical"),
    ("Machine Learning", "Technical"),
    ("Data Science", "Technical"),
    ("HTML", "Technical"),
    ("CSS", "Technical"),
    ("TypeScript", "Technical"),
    ("C++", "Technical"),
    ("C#", "Technical"),
    ("Ruby", "Technical"),
    ("PHP", "Technical"),
    ("Swift", "Technical"),
    ("Kotlin", "Technical"),
    ("Go", "Technical"),
    ("Rust", "Technical"),
    ("R", "Technical"),
    ("MATLAB", "Technical"),
    ("TensorFlow", "Technical"),
    ("PyTorch", "Technical"),
    ("Django", "Technical"),
    ("Flask", "Technical"),
    ("Spring Boot", "Technical"),
    ("Angular", "Technical"),
    ("Vue.js", "Technical"),
    ("PostgreSQL", "Technical"),
    ("MySQL", "Technical"),
    ("Redis", "Technical"),
    ("Elasticsearch", "Technical"),
    ("Apache Kafka", "Technical"),
    ("CI/CD", "Technical"),
    ("Jenkins", "Technical"),
    ("Terraform", "Technical"),
    ("Azure", "Technical"),
    ("GCP", "Technical"),
    ("Linux", "Technical"),
    ("REST API", "Technical"),
    ("GraphQL", "Technical"),
    ("Microservices", "Technical"),
    ("Agile", "Technical"),
    ("Scrum", "Technical"),
    ("DevOps", "Technical"),
    # Soft Skills
    ("Communication", "Soft"),
    ("Leadership", "Soft"),
    ("Problem Solving", "Soft"),
    ("Teamwork", "Soft"),
    ("Time Management", "Soft"),
    ("Critical Thinking", "Soft"),
    ("Creativity", "Soft"),
    ("Adaptability", "Soft"),
    ("Project Management", "Soft"),
    ("Analytical Skills", "Soft"),
    ("Attention to Detail", "Soft"),
    ("Decision Making", "Soft"),
    ("Conflict Resolution", "Soft"),
    ("Presentation Skills", "Soft"),
    ("Negotiation", "Soft"),
]

SAMPLE_JOBS = [
    {
        "title": "Python Developer",
        "description": "We are looking for a Python Developer with experience in Django/Flask, REST APIs, SQL databases, and cloud services. Strong problem-solving skills required.",
        "skills": "Python, Django, Flask, REST API, SQL, PostgreSQL, AWS, Docker, Git, Problem Solving",
    },
    {
        "title": "Data Scientist",
        "description": "Seeking a Data Scientist proficient in Python, Machine Learning, TensorFlow/PyTorch, and statistical analysis. Must have strong communication skills.",
        "skills": "Python, Machine Learning, Data Science, TensorFlow, PyTorch, SQL, R, Communication, Analytical Skills",
    },
    {
        "title": "Full Stack Developer",
        "description": "Full Stack Developer needed with expertise in React, Node.js, MongoDB, and cloud deployment. Agile experience preferred.",
        "skills": "JavaScript, React, Node.js, MongoDB, HTML, CSS, TypeScript, AWS, Docker, Git, Agile",
    },
]


def seed_database() -> None:
    """Populate the database with initial seed data."""
    init_db()
    db = get_db()

    try:
        # Seed skills
        existing_skills = db.query(Skill).count()
        if existing_skills == 0:
            for skill_name, skill_type in SKILLS_DATA:
                skill = Skill(skill_name=skill_name, skill_type=skill_type)
                db.add(skill)
            db.commit()
            print(f"✓ Seeded {len(SKILLS_DATA)} skills.")
        else:
            print(f"Skills already exist ({existing_skills} found). Skipping.")

        # Seed admin user
        existing_admin = db.query(User).filter(User.role == "Admin").first()
        if not existing_admin:
            admin = User(
                name="Admin",
                email="admin@resumeanalyzer.com",
                password=hash_password("admin123"),
                role="Admin",
                phone="0000000000",
            )
            db.add(admin)
            db.commit()
            print("✓ Seeded admin user (email: admin@resumeanalyzer.com, password: admin123).")
        else:
            print("Admin user already exists. Skipping.")

        # Seed sample job descriptions
        existing_jobs = db.query(JobDescription).count()
        if existing_jobs == 0:
            for job_data in SAMPLE_JOBS:
                job = JobDescription(
                    job_title=job_data["title"],
                    job_description_text=job_data["description"],
                    required_skills=job_data["skills"],
                )
                db.add(job)
            db.commit()
            print(f"✓ Seeded {len(SAMPLE_JOBS)} sample job descriptions.")
        else:
            print(f"Job descriptions already exist ({existing_jobs} found). Skipping.")

        print("\n✓ Database seeding complete!")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
