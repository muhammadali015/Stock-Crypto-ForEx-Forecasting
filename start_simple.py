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
    
    # Check if simple app exists
    app_path = Path("simple_app.py")
    if not app_path.exists():
        print("❌ Application not found.")
        sys.exit(1)
    
    print("🌐 Starting Flask backend server...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("🔌 API endpoints available at: http://localhost:8000/api")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the Flask application
        subprocess.run([sys.executable, "simple_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
