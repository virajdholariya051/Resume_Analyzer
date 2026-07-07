"""
Resume Analyzer with ATS Score and Job Match Prediction
Main entry point for the application.
"""

import subprocess
import sys


def main() -> None:
    """Launch the Streamlit frontend application."""
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py"],
        check=True,
    )


if __name__ == "__main__":
    main()
