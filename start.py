#!/usr/bin/env python3
"""
Startup script for the FinTech forecasting application.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the FinTech forecasting application."""
    print("🚀 Starting FinTech Forecasting Application...")
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found. Please run setup.py first.")
        sys.exit(1)
    
    # Determine the correct python command based on OS
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # macOS/Linux
        python_cmd = "venv/bin/python"
    
    # Check if backend app exists
    app_path = Path("backend/app.py")
    if not app_path.exists():
        print("❌ Backend application not found.")
        sys.exit(1)
    
    print("🌐 Starting Flask backend server...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔌 API endpoints available at: http://localhost:5000/api")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the Flask application
        subprocess.run([python_cmd, "backend/app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
