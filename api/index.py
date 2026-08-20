import sys
import os
from pathlib import Path

# Add current directory (containing app/) to sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from app.main import app
