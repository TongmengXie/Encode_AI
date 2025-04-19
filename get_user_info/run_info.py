import os
import subprocess
import sys
import time
import signal
import webbrowser
import requests
import pandas as pd
import socket
from dotenv import load_dotenv
import threading

# Get the current script directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Load environment variables from parent directory
load_dotenv(os.path.join(PARENT_DIR, '.env'))

# Check if ports are in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Kill process using a specific port (Windows-compatible)
def kill_process_on_port(port):
    try:
        if sys.platform.startswith('win'):
            subprocess.run(f"FOR /F \"tokens=5\" %P IN ('netstat -a -n -o | findstr :{port}') DO taskkill /F /PID %P", shell=True)
        else:
            subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True)
        print(f"Killed process using port {port}")
        time.sleep(1)  # Give the system time to release the port
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")

# Check if user_pool.csv exists in the get_user_info directory
user_pool_path = os.path.join(SCRIPT_DIR, "user_pool.csv")
if not os.path.exists(user_pool_path):
    print("Running migration to move user_pool.csv to get_user_info directory...")
    try:
        # Import and run the migration script
        migration_script = os.path.join(SCRIPT_DIR, "migrate_user_pool.py")
        
        # Check if migration script exists
        if os.path.exists(migration_script):
            subprocess.run([sys.executable, migration_script], check=True)
        else:
            print("Migration script not found. Creating empty user_pool.csv...")
            # Create empty user_pool.csv with header
            columns = [
                'real_name', 'age_group', 'gender', 'nationality', 
                'preferred_residence', 'cultural_symbol', 'bucket_list',
                'healthcare_expectations', 'travel_budget', 
                'currency_preferences', 'insurance_type', 'past_insurance_issues'
            ]
            pd.DataFrame(columns=columns).to_csv(user_pool_path, index=False)
            print(f"Created empty user_pool.csv at: {user_pool_path}")
            
            # Create cache directory
            cache_dir = os.path.join(SCRIPT_DIR, "cache")
            os.makedirs(cache_dir, exist_ok=True)
    except Exception as e:
        print(f"Error during migration: {str(e)}")

# Backend directory in the same location as wandermatch.py
backend_dir = os.path.join(SCRIPT_DIR, "backend")
# Ensure backend directory exists
os.makedirs(backend_dir, exist_ok=True)

# Create UserInfo_and_Match/survey_results directory for saving results
user_info_match_dir = os.path.join(PARENT_DIR, "UserInfo_and_Match")
survey_results_dir = os.path.join(user_info_match_dir, "survey_results")
os.makedirs(survey_results_dir, exist_ok=True)
print(f"Survey results will be saved to: {survey_results_dir}")

# URLs for the application
survey_url = "http://localhost:8080"
submit_url = "http://localhost:5000/api/submit"
recommend_url = "http://localhost:5000/api/recommend"
frontend_port = 8000
backend_port = 5000

def signal_handler(sig, frame):
    print('Stopping servers...')
    if 'frontend_process' in globals():
        frontend_process.terminate()
    if 'backend_process' in globals():
        backend_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Check if ports are in use and kill processes if needed
print("Checking if ports are in use...")
if is_port_in_use(backend_port):
    print(f"Port {backend_port} is in use. Attempting to kill the process...")
    kill_process_on_port(backend_port)

if is_port_in_use(frontend_port):
    print(f"Port {frontend_port} is in use. Attempting to kill the process...")
    kill_process_on_port(frontend_port)

# Start backend server
print("Starting backend server...")
backend_process = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, "server.py")])
print("Backend server started.")

# Wait for a second to let the backend server start
time.sleep(1)

# Start frontend server (static file server)
os.chdir(os.path.join(SCRIPT_DIR, "frontend"))
frontend_process = subprocess.Popen([sys.executable, "-m", "http.server", str(frontend_port)])
print("Frontend server started.")

# Open the frontend in the default web browser
try:
    webbrowser.open(f'http://localhost:{frontend_port}')
except:
    print(f"Please open http://localhost:{frontend_port} in your browser.")

# Wait for Flask to start
def wait_for_backend(url=submit_url, timeout=15):
    print("[CLOCK] Waiting for backend to be ready...")
    start_time = time.time()
    for i in range(timeout):
        try:
            response = requests.options(url, timeout=1)
            if response.status_code == 200:
                print(f"[CHECK] Backend is ready! ({time.time() - start_time:.2f}s)")
                return True
        except requests.exceptions.RequestException:
            pass
        
        # Only print message every 2 seconds
        if i % 2 == 0:
            print(f"[WAITING] Still waiting for backend... ({i+1}/{timeout}s)")
        time.sleep(1)
    
    print("[X] Backend not responding after waiting.")
    return False

# Wait for Flask to start - with better error handling
if not wait_for_backend():
    print("[ERROR] Backend failed to start. Stopping servers.")
    frontend_process.terminate()
    backend_process.terminate()
    sys.exit(1)

# Display survey information
print("[CLIPBOARD] Please complete the form in your browser.")
print("[CLIPBOARD] Your survey will be processed and saved automatically.")
print("[CLIPBOARD] The success message with the save path will appear on the page after submission.")

# Modify scripts.js to ensure smoother submission handling
frontend_dir = os.path.join(SCRIPT_DIR, "frontend")
scripts_js_path = os.path.join(frontend_dir, "scripts.js")

# Monitor for new CSV files
def monitor_for_survey_results():
    """Monitor for new survey result files and return the path when found."""
    # Get initial list of files
    initial_files = set()
    
    if os.path.exists(survey_results_dir):
        initial_files = set([f for f in os.listdir(survey_results_dir) if f.startswith("user_answer") and f.endswith(".csv")])
    
    backend_initial_files = set()
    if os.path.exists(backend_dir):
        backend_initial_files = set([f for f in os.listdir(backend_dir) if f.startswith("user_answer") and f.endswith(".csv")])
    
    print("Waiting for survey submissions...")
    
    # Keep track of the last seen files to detect new ones
    last_seen_files = initial_files.copy()
    last_seen_backend_files = backend_initial_files.copy()
    
    while True:
        time.sleep(1)  # Check every second
        
        # Check survey_results_dir first
        current_files = set()
        if os.path.exists(survey_results_dir):
            current_files = set([f for f in os.listdir(survey_results_dir) if f.startswith("user_answer") and f.endswith(".csv")])
        
        new_files = current_files - last_seen_files
        if new_files:
            latest_file = max(new_files, key=lambda f: os.path.getmtime(os.path.join(survey_results_dir, f)))
            filepath = os.path.join(survey_results_dir, latest_file)
            print(f"\n[CHECK] Survey submitted!")
            print(f"[FILE] Survey results saved to: {filepath}")
            print("\nFile Location Information:")
            print("---------------------------")
            print(f"Parent Directory: {PARENT_DIR}")
            print(f"Survey Results Directory: {survey_results_dir}")
            print(f"Saved File: {latest_file}")
            print("---------------------------\n")
            print("Waiting for additional survey submissions...")
            
            # Update last seen files
            last_seen_files = current_files.copy()
        
        # Also check backend directory as fallback
        backend_current_files = set()
        if os.path.exists(backend_dir):
            backend_current_files = set([f for f in os.listdir(backend_dir) if f.startswith("user_answer") and f.endswith(".csv")])
        
        new_backend_files = backend_current_files - last_seen_backend_files
        if new_backend_files:
            latest_file = max(new_backend_files, key=lambda f: os.path.getmtime(os.path.join(backend_dir, f)))
            filepath = os.path.join(backend_dir, latest_file)
            print(f"\n[CHECK] Survey submitted!")
            print(f"[FILE] Survey results saved to: {filepath}")
            print("\nFile Location Information:")
            print("---------------------------")
            print(f"Parent Directory: {PARENT_DIR}")
            print(f"Backend Directory: {backend_dir}")
            print(f"Saved File: {latest_file}")
            print("---------------------------\n")
            print("Waiting for additional survey submissions...")
            
            # Update last seen backend files
            last_seen_backend_files = backend_current_files.copy()

# Start monitoring for survey results in a separate thread
monitor_thread = threading.Thread(target=monitor_for_survey_results, daemon=True)
monitor_thread.start()

# Keep the script running to maintain the servers
print("Servers are running. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping servers...")
    frontend_process.terminate()
    backend_process.terminate()
