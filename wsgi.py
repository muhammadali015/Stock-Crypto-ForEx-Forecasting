import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app_sqlite import app

# WSGI application entry point
application = app

if __name__ == "__main__":
    app.run()
