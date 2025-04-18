#!/usr/bin/env python
"""
WanderMatch Survey Launcher - Windows Version
This script starts the survey components needed for WanderMatch.
"""
import os
import sys
import subprocess
import webbrowser
import time
import shutil
import requests
import traceback
from dotenv import load_dotenv

# Load environment variables if .env file exists
load_dotenv()

def check_directories():
    """Check if required directories exist"""
    # Use environment variable or default to script directory
    current_dir = os.environ.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
    
    # Check backend directory
    backend_dir = os.path.join(current_dir, "deploy", "backend")
    if not os.path.exists(backend_dir):
        print(f"❌ Error: Backend directory not found at {backend_dir}")
        return False
    
    # Ensure backend app exists
    backend_app = os.path.join(backend_dir, "app.py")
    if not os.path.exists(backend_app):
        print(f"❌ Error: Backend application not found at {backend_app}")
        return False
    
    # Check for test HTML form
    test_form = os.path.join(current_dir, "test_survey_form.html")
    if not os.path.exists(test_form):
        print(f"❌ Warning: Test form not found at {test_form}")
    
    # Ensure survey results directory exists - use environment variable if available
    survey_dir = os.environ.get('SURVEY_RESULTS_DIR', 
                              os.path.join(current_dir, "UserInfo_and_Match", "survey_results"))
    if not os.path.exists(survey_dir):
        try:
            os.makedirs(survey_dir, exist_ok=True)
            print(f"Created survey results directory: {survey_dir}")
        except Exception as e:
            print(f"❌ Error creating survey directory: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    # Try to create a test file to verify write permissions
    test_file = os.path.join(survey_dir, "write_test.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("Write test successful")
        os.remove(test_file)
        print(f"✅ Directory write test successful")
    except Exception as e:
        print(f"❌ Error writing to survey directory: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        print(f"Make sure the directory has proper write permissions")
        return False
    
    return True

def start_backend():
    """Start the backend Flask server"""
    # Use environment variable or default
    current_dir = os.environ.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
    backend_app = os.path.join(current_dir, "deploy", "backend", "app.py")
    
    print("Starting backend server...")
    
    # Add a hook for proper error handling
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # Ensure output is not buffered
    
    backend_process = subprocess.Popen(
        [sys.executable, backend_app],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Start a thread to monitor backend output
    import threading
    def monitor_output():
        while True:
            line = backend_process.stdout.readline()
            if not line and backend_process.poll() is not None:
                break
            if line:
                print(f"Backend: {line.strip()}")
    
    # Start the monitoring thread
    threading.Thread(target=monitor_output, daemon=True).start()
    
    # Get API host and port from environment or use defaults
    api_host = os.environ.get('API_HOST', 'localhost')
    api_port = os.environ.get('PORT', '5000')
    api_url = f"http://{api_host}:{api_port}"
    
    # Wait for backend to start
    print("Waiting for backend to initialize...")
    for i in range(15):
        try:
            response = requests.get(f"{api_url}/api/health")
            if response.status_code == 200:
                print("✅ Backend server is running")
                # Verify the survey directory path is correct
                data = response.json()
                print(f"Survey directory (from API): {data.get('survey_dir', 'unknown')}")
                return backend_process
        except requests.exceptions.ConnectionError:
            pass
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\n⚠️ Timed out waiting for backend to start, but continuing anyway")
    return backend_process

def open_survey_browser():
    """Open the survey in the browser"""
    # Get environment or use defaults
    current_dir = os.environ.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
    environment = os.environ.get('ENVIRONMENT', 'development')
    api_host = os.environ.get('API_HOST', 'localhost')
    api_port = os.environ.get('PORT', '5000')
    api_url = f"http://{api_host}:{api_port}"
    
    # Production or development mode affects how we open the browser
    if environment == 'production':
        # In production, we use the deployed web URL
        print("\nOpening API health check...")
        webbrowser.open(f"{api_url}/api/health")
    else:
        # First try to open our test form if it exists
        test_form = os.path.join(current_dir, "test_survey_form.html")
        if os.path.exists(test_form):
            print("\nOpening test survey form...")
            # Convert path to URL format
            form_url = f"file:///{test_form.replace(os.sep, '/')}"
            webbrowser.open(form_url)
            print(f"Survey form opened at: {form_url}")
        else:
            # Fallback to API health endpoint
            print("\nOpening API health check...")
            webbrowser.open(f"{api_url}/api/health")
    
    print("\nIf the browser didn't open automatically, please navigate to:")
    print(f"  API Health: {api_url}/api/health")
    
    if environment != 'production':
        test_form = os.path.join(current_dir, "test_survey_form.html")
        if os.path.exists(test_form):
            print(f"  Test Form: file:///{test_form.replace(os.sep, '/')}")

def main():
    """Main function"""
    print("WanderMatch Survey Launcher")
    print("=========================\n")
    
    # Check if required directories exist
    if not check_directories():
        print("❌ Error: Required directories not found")
        return 1
    
    # Start backend server only
    backend_process = start_backend()
    if not backend_process:
        print("❌ Error: Failed to start backend server")
        return 1
    
    # Open survey in browser
    open_survey_browser()
    
    print("\n✅ Survey backend is running!")
    print("\nWhen you submit the survey, the results will be saved to:")
    survey_dir = os.environ.get('SURVEY_RESULTS_DIR', 
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                         "UserInfo_and_Match", "survey_results"))
    print(f"  {survey_dir}")
    
    print("\nPress Ctrl+C to stop the backend server")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down backend server...")
        backend_process.terminate()
        print("✅ Backend server stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 