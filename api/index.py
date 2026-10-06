import sys
import os
from pathlib import Path

# Add the project root to sys.path so the Vercel function can import phase_5_dashboard
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app instance from phase_5_dashboard directly
from phase_5_dashboard.api import app
