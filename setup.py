"""
Setup script for the FinTech forecasting application.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_virtual_environment():
    """Create virtual environment."""
    if not os.path.exists("venv"):
        return run_command("python -m venv venv", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
        return True

def install_dependencies():
    """Install Python dependencies."""
    # Determine the correct pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # macOS/Linux
        pip_cmd = "venv/bin/pip"
    
    return run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")

def initialize_database():
    """Initialize the database."""
    # Determine the correct python command based on OS
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # macOS/Linux
        python_cmd = "venv/bin/python"
    
    return run_command(f"{python_cmd} backend/database.py", "Initializing database")

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# FinTech Forecasting Application Environment Variables
DATABASE_URL=sqlite:///fintech_forecasting.db
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
DEBUG=True
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")

def run_tests():
    """Run the test suite."""
    # Determine the correct python command based on OS
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # macOS/Linux
        python_cmd = "venv/bin/python"
    
    return run_command(f"{python_cmd} -m pytest tests/ -v", "Running tests")

def main():
    """Main setup function."""
    print("🚀 FinTech Forecasting Application Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Initialize database
    if not initialize_database():
        print("⚠️  Database initialization failed, but continuing...")
    
    # Run tests
    if not run_tests():
        print("⚠️  Some tests failed, but continuing...")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # macOS/Linux
        print("   source venv/bin/activate")
    
    print("2. Start the application:")
    print("   python backend/app.py")
    
    print("3. Open your browser and go to:")
    print("   http://localhost:5000")
    
    print("\n📚 For more information, see docs/README.md")

if __name__ == "__main__":
    main()
