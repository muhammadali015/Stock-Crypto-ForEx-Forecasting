import os
import sys

# Get the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the Flask app
from app_sqlite import app

if __name__ == "__main__":
    # This will also call init_database() from app_sqlite.py
    app.run()
