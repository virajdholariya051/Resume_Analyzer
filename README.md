# Resume Analyzer with ATS Score and Job Match Prediction

A professional AI-powered Resume Analyzer system built with Streamlit, Python, spaCy NLP, and SQLite that allows users to upload resumes, analyze skills, compare resumes against job descriptions, calculate ATS scores, and generate improvement suggestions.

## Features

- **User Authentication** - Register, login, logout with bcrypt password hashing and session management
- **Resume Upload** - Support for PDF and DOCX formats with text extraction
- **NLP Resume Parsing** - Extract name, email, phone, skills, education, experience, certifications
- **Skill Extraction Engine** - Identify technical and soft skills from predefined datasets
- **ATS Score Calculator** - Score resumes (0-100) based on format, keywords, skills, experience, education
- **Job Match Percentage** - Compare resumes against job descriptions with detailed breakdown
- **Resume Feedback** - Generate strengths and improvement areas
- **Visual Analytics** - Interactive charts with Plotly (gauges, radar charts, trend lines)
- **Admin Panel** - Manage users, resumes, analyses, jobs, and skills database
- **Report Generation** - Downloadable PDF reports for ATS analysis and skill gaps
- **Role-Based Access** - Admin and Job Seeker roles with different capabilities

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Backend | Python |
| NLP | spaCy, Pattern Matching |
| Database | SQLite |
| ORM | SQLAlchemy |
| Authentication | bcrypt + Session-based |
| PDF Parsing | PyPDF2, pdfplumber |
| DOCX Parsing | python-docx |
| Visualization | Plotly |
| Reports | FPDF2 |
| Data Processing | Pandas |

## Project Structure

```
resume_analyzer/
├── frontend/
│   ├── app.py                 # Main Streamlit entry point
│   ├── pages/
│   │   ├── login.py           # Login page
│   │   ├── register.py        # Registration page
│   │   ├── dashboard.py       # Dashboard with analytics
│   │   ├── upload_resume.py   # Resume upload page
│   │   ├── analysis.py        # Analysis page
│   │   ├── profile.py         # User profile management
│   │   └── admin.py           # Admin panel
│   ├── components/
│   │   ├── navbar.py          # Navigation bar
│   │   ├── sidebar.py         # Filter sidebar
│   │   └── charts.py          # Plotly chart components
│   └── assets/
│       └── styles.css          # Custom CSS
├── backend/
│   ├── controllers/
│   │   └── resume_controller.py
│   ├── services/
│   │   ├── resume_service.py
│   │   ├── analysis_service.py
│   │   ├── user_service.py
│   │   ├── job_service.py
│   │   └── report_service.py
│   ├── nlp/
│   │   ├── resume_parser.py   # NLP-based resume parsing
│   │   ├── skill_extractor.py # Skill extraction engine
│   │   ├── ats_scorer.py      # ATS score calculator
│   │   └── job_matcher.py     # Job match engine
│   ├── auth/
│   │   └── auth_service.py    # Authentication service
│   ├── config/
│   │   └── settings.py        # Application settings
│   ├── utils/
│   │   └── file_parser.py     # File parsing utilities
│   └── models/
├── database/
│   ├── database.py            # DB connection & session
│   ├── schema.py              # SQLAlchemy ORM models
│   └── seed.py                # Database seeding script
├── uploads/                   # Uploaded resume files
├── reports/                   # Generated PDF reports
├── requirements.txt
├── main.py
└── README.md
```

## Database Schema

### Tables

1. **users** - User accounts with authentication
2. **resumes** - Uploaded resume data and extracted text
3. **job_descriptions** - Job postings with required skills
4. **analysis_results** - ATS scores and match percentages
5. **skills** - Skills database (technical + soft)
6. **resume_skills** - Many-to-many relationship (resume ↔ skills)

## Installation Guide

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. **Clone/Download the project:**
   ```bash
   cd resume_analyzer
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Initialize database and seed data:**
   ```bash
   python database/seed.py
   ```

6. **Run the application:**
   ```bash
   streamlit run frontend/app.py
   ```

7. **Access the application:**
   Open your browser at `http://localhost:8501`

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@resumeanalyzer.com | admin123 |

## Usage

1. **Register** - Create a new account or login with default credentials
2. **Upload Resume** - Upload PDF/DOCX resume from the Upload page
3. **Add Job Description** - Add target job descriptions in the Analysis tab
4. **Run Analysis** - Select resume and job, then click "Run Analysis"
5. **View Results** - See ATS score, job match, strengths, weaknesses, skill gaps
6. **Download Reports** - Generate PDF reports for your analysis results

## ATS Score Calculation

The ATS score (0-100) is calculated as a weighted combination of:

| Factor | Weight |
|--------|--------|
| Resume Format | 15% |
| Keyword Density | 25% |
| Skills Coverage | 25% |
| Experience Relevance | 15% |
| Education Match | 10% |
| Section Completeness | 10% |

## Job Match Calculation

| Factor | Weight |
|--------|--------|
| Skill Match | 40% |
| Keyword Match | 30% |
| Experience Match | 20% |
| Education Match | 10% |

## Security Features

- Password hashing with bcrypt
- SQL injection prevention via SQLAlchemy ORM
- Input validation on all forms
- Secure file upload with type/size validation
- Session-based authentication

## License

MIT License
