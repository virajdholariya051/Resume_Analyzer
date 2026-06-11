"""
Streamlit Cloud entry point.
This file redirects to the actual app in frontend/app.py.
"""

import sys
import os

# Ensure the project root is in the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import and run the actual app
from frontend.app import main

main()
