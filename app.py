import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.app_sqlite import app
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: try to import from the same directory
    try:
        from app_sqlite import app
    except ImportError:
        print("Failed to import Flask app")
        raise

# This is the Flask app that Vercel will use
application = app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))