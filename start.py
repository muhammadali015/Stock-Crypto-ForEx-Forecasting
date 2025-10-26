#!/usr/bin/env python3
"""
FinTech Forecasting Application - Startup Script
Runs both backend and frontend servers
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal

class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(text, color=Colors.NC):
    print(f"{color}{text}{Colors.NC}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n" + "="*50)
    print(" CHECKING DEPENDENCIES")
    print("="*50 + "\n")
    
    # Check Python
    try:
        import flask
        print_colored("[OK] Python and Flask are installed", Colors.GREEN)
    except ImportError:
        print_colored("[ERROR] Flask is not installed", Colors.RED)
        print("Run: pip install -r requirements.txt")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print_colored(f"[OK] Node.js is installed: {result.stdout.strip()}", Colors.GREEN)
    except FileNotFoundError:
        print_colored("[ERROR] Node.js is not installed", Colors.RED)
        return False
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        print_colored(f"[OK] npm is installed: {result.stdout.strip()}", Colors.GREEN)
    except FileNotFoundError:
        print_colored("[ERROR] npm is not installed", Colors.RED)
        return False
    
    return True

def install_dependencies():
    """Install required dependencies if needed"""
    print("\n" + "="*50)
    print(" INSTALLING DEPENDENCIES")
    print("="*50 + "\n")
    
    # Check if dependencies are already installed
    if not os.path.exists('backend/__pycache__'):
        print("[1/4] Installing Python dependencies...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True, capture_output=True)
            print_colored("[OK] Python dependencies installed", Colors.GREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"[ERROR] Failed to install Python dependencies: {e}", Colors.RED)
            return False
    else:
        print_colored("[OK] Python dependencies already installed", Colors.GREEN)
    
    # Check if frontend dependencies are installed
    if not os.path.exists('frontend/node_modules'):
        print("[2/4] Installing Node.js dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd='frontend', check=True, capture_output=True)
            print_colored("[OK] Node.js dependencies installed", Colors.GREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"[ERROR] Failed to install Node.js dependencies: {e}", Colors.RED)
            return False
    else:
        print_colored("[OK] Node.js dependencies already installed", Colors.GREEN)
    
    return True

def initialize_database():
    """Initialize the SQLite database if needed"""
    print("\n" + "="*50)
    print(" INITIALIZING DATABASE")
    print("="*50 + "\n")
    
    if not os.path.exists('instance/fintech_forecasting.db'):
        print("[3/4] Initializing SQLite database...")
        try:
            subprocess.run([sys.executable, 'init_db.py'], check=True)
            print_colored("[OK] Database initialized", Colors.GREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"[ERROR] Failed to initialize database: {e}", Colors.RED)
            return False
    else:
        print_colored("[OK] Database already exists", Colors.GREEN)
    
    return True

def start_servers():
    """Start both backend and frontend servers"""
    print("\n" + "="*50)
    print(" STARTING SERVERS")
    print("="*50 + "\n")
    
    # Start Backend
    print("[4/4] Starting Backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, 'backend/app_sqlite.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print_colored("Backend starting...", Colors.BLUE)
    time.sleep(3)  # Wait for backend to initialize
    
    # Start Frontend
    print("Starting Frontend server...")
    frontend_process = subprocess.Popen(
        ['npm', 'start'],
        cwd='frontend',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print_colored("Frontend starting...", Colors.BLUE)
    time.sleep(2)
    
    # Display server information
    print("\n" + "="*50)
    print(" SERVER STATUS")
    print("="*50)
    print_colored("Backend:  http://localhost:8000", Colors.GREEN)
    print_colored("Frontend: http://localhost:3000", Colors.GREEN)
    print_colored("API:      http://localhost:8000/api", Colors.GREEN)
    print_colored("Database: instance/fintech_forecasting.db", Colors.GREEN)
    print("="*50 + "\n")
    
    print_colored("APPLICATION STARTED SUCCESSFULLY!", Colors.GREEN)
    print("\n[INFO] Both servers are running in the background")
    print("[INFO] Press Ctrl+C to stop the application\n")
    
    # Open browser
    time.sleep(2)
    print("Opening browser...")
    webbrowser.open('http://localhost:3000')
    
    # Wait for user interrupt
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "="*50)
        print(" STOPPING APPLICATION")
        print("="*50 + "\n")
        
        print("Stopping Backend server...")
        backend_process.terminate()
        
        print("Stopping Frontend server...")
        frontend_process.terminate()
        
        # Wait for processes to terminate
        time.sleep(1)
        
        print_colored("[OK] Application stopped", Colors.GREEN)

def main():
    """Main function"""
    print("\n" + Colors.BLUE + "="*50)
    print(" FinTech Forecasting Application")
    print(" Complete Startup Script")
    print("="*50 + Colors.NC)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Start servers
    start_servers()

if __name__ == '__main__':
    main()