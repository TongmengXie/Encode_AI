import os
import subprocess
import sys
import time
import signal
import webbrowser
import requests
import pandas as pd
from dotenv import load_dotenv

# Get the current script directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Load environment variables from parent directory
load_dotenv(os.path.join(PARENT_DIR, '.env'))

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

# URLs for the application
survey_url = "http://localhost:8080"
submit_url = "http://localhost:5000/api/submit"
recommend_url = "http://localhost:5000/api/recommend"

def signal_handler(sig, frame):
    print('Stopping servers...')
    if 'frontend_process' in globals():
        frontend_process.terminate()
    if 'backend_process' in globals():
        backend_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Start backend server
backend_process = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, "server.py")])
print("Backend server started.")

# Wait for a second to let the backend server start
time.sleep(1)

# Start frontend server (static file server)
os.chdir(os.path.join(SCRIPT_DIR, "frontend"))
frontend_process = subprocess.Popen([sys.executable, "-m", "http.server", "8000"])
print("Frontend server started.")

# Open the frontend in the default web browser
try:
    webbrowser.open('http://localhost:8000')
except:
    print("Please open http://localhost:8000 in your browser.")

# Wait for Flask to start
def wait_for_backend(url=submit_url, timeout=10):
    print("🕐 Waiting for backend to be ready...")
    for i in range(timeout):
        try:
            response = requests.options(url)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return
        except:
            pass
        time.sleep(1)
    print("❌ Backend not responding after waiting.")
    exit(1)

# Wait for Flask to start
wait_for_backend()

# Wait for user to complete the form
print("📋 Please complete the form in your browser.")
print("📋 When you've finished submitting the form, you'll be redirected to a thank you page.")
print("📋 After seeing the thank you page, press Enter here to continue...")
try:
    input("\n[Press Enter after completing the survey]\n")
except KeyboardInterrupt:
    print("\nOperation cancelled by user.")
    sys.exit(0)

# Step 6: Display saved CSV files and recommendations
csv_files = [f for f in os.listdir(backend_dir) if f.startswith("user_answer") and f.endswith(".csv")]
csv_files.sort(reverse=True)

if csv_files:
    latest_file = csv_files[0]
    filepath = os.path.join(backend_dir, latest_file)
    print(f"\n📄 Latest saved file: {latest_file}")
    try:
        # Try multiple encodings to ensure proper reading
        df = None
        encodings = ['utf-8', 'ISO-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                print(f"✅ Successfully loaded file with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
            
        if df is None:
            # Last resort - use with errors='replace' to handle problematic characters
            df = pd.read_csv(filepath, encoding='utf-8', errors='replace')
            print("⚠️ Loaded file with character replacement")

    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        df = pd.DataFrame()

    if not df.empty:
        print(df.to_string(index=False))

        # Step 6.1: Send request to backend for recommendations
        print("\n🔍 Fetching top match recommendations from backend...")
        try:
            # Prepare data - handle potential encoding issues
            answers = df.iloc[0].tolist()
            # Convert any problematic values to strings with replacement
            answers = [str(val).encode('utf-8', errors='replace').decode('utf-8') if val is not None else "" for val in answers]
            
            res = requests.post(recommend_url, json={"answers": answers}, timeout=15)
            result = res.json()
            print(f"\n✅ Recommendations from {latest_file}:")
            for r in result["recommendations"]:
                print(f"• User {r['index'] + 1}: {r['name']} (Score: {r['score']:.4f})")
            
            # Try to find match results in results directory
            results_dir = os.path.join(SCRIPT_DIR, "results")
            os.makedirs(results_dir, exist_ok=True)
            
            match_files = [f for f in os.listdir(results_dir) if f.startswith("top_matches_") and f.endswith(".csv")]
            if match_files:
                match_files.sort(key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)
                latest_match = match_files[0]
                print(f"\n📄 Latest match file: {latest_match}")
                print(f"📍 Location: {results_dir}")
        except Exception as e:
            print("❌ Failed to fetch recommendations:", e)

else:
    print("⚠️ No saved answer file found.")

# Create thank_you.html page if it doesn't exist
frontend_dir = os.path.join(SCRIPT_DIR, "frontend")
thank_you_path = os.path.join(frontend_dir, "thank_you.html")
if not os.path.exists(thank_you_path):
    thank_you_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You - WanderMatch</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <div class="text-center my-5">
            <h1>Thank You for Completing the Survey!</h1>
            <p class="lead">Your responses have been recorded.</p>
            <p>You can now close this window and return to the WanderMatch application.</p>
            <div class="mt-4">
                <img src="https://images.unsplash.com/photo-1488646953014-85cb44e25828?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=500&q=80" alt="Travel Scene" class="img-fluid rounded shadow">
            </div>
            <p class="mt-4 text-muted">WanderMatch is now processing your responses to find your ideal travel partner.</p>
            <div class="mt-4">
                <button onclick="window.close()" class="btn btn-primary btn-lg">Return to WanderMatch</button>
            </div>
        </div>
    </div>
</body>
</html>"""
    with open(thank_you_path, "w", encoding="utf-8") as f:
        f.write(thank_you_html)
    print(f"Created thank you page at {thank_you_path}")

# Keep the script running to maintain the servers
print("Servers are running. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping servers...")
    frontend_process.terminate()
    backend_process.terminate()
