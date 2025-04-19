#!/usr/bin/env python
"""
Main script to run the WanderMatch deployment.
This script activates the environment, sets up the application, and starts both
the backend and frontend servers.
"""
import os
import sys
import subprocess
import time
import webbrowser
import shutil

# Get the absolute path of the deploy directory
DEPLOY_DIR = os.path.dirname(os.path.abspath(__file__))

def check_environment():
    """Check if the required environment is available"""
    print("Checking environment...")
    
    # Check if Python is available
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print("Warning: Python 3.8+ is recommended")
    
    # Check if Node.js is available
    try:
        node_version = subprocess.check_output(["node", "--version"], text=True).strip()
        print(f"Node.js version: {node_version}")
    except:
        print("Warning: Node.js not found. Please install Node.js")
        return False
    
    print("✅ Environment check passed")
    return True

def get_npm_command():
    """Get the appropriate npm command based on the OS"""
    # Check for npm directly
    npm_path = shutil.which("npm")
    if npm_path:
        print(f"Found npm at: {npm_path}")
        return ["npm"]
    
    # Check for node
    node_path = shutil.which("node")
    if not node_path:
        print("❌ Node.js not found in PATH")
        return None
    
    # Try to find npm relative to node
    node_dir = os.path.dirname(node_path)
    possible_npm_paths = [
        os.path.join(node_dir, "npm"),
        os.path.join(node_dir, "npm.cmd"),
        os.path.join(node_dir, "npm.bat"),
        os.path.join(node_dir, "node_modules", "npm", "bin", "npm-cli.js")
    ]
    
    for path in possible_npm_paths:
        if os.path.exists(path):
            print(f"Found npm at: {path}")
            if path.endswith(".js"):
                return [node_path, path]
            return [path]
    
    # If we can't find npm in standard locations, try the full path
    for npm_name in ["npm", "npm.cmd", "npm.bat"]:
        full_path = os.path.join("C:", os.sep, "Program Files", "nodejs", npm_name)
        if os.path.exists(full_path):
            print(f"Found npm at alternative location: {full_path}")
            return [full_path]
    
    print("❌ Could not find npm executable")
    return None

def setup_frontend_dependencies():
    """Install frontend dependencies directly"""
    print("\nInstalling frontend dependencies...")
    
    # Navigate to frontend directory using absolute path
    frontend_dir = os.path.join(DEPLOY_DIR, "frontend")
    if not os.path.exists(frontend_dir):
        print(f"❌ Frontend directory not found at {frontend_dir}")
        return False
    
    # Save current directory
    current_dir = os.getcwd()
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    print(f"Changed to directory: {os.getcwd()}")
    
    # Get npm command
    npm_cmd = get_npm_command()
    if not npm_cmd:
        print("❌ Cannot find npm. Please make sure Node.js is installed correctly.")
        os.chdir(current_dir)
        return False
    
    # Print environment information for debugging
    print("Environment information:")
    print(f"PATH: {os.environ.get('PATH', 'Not set')}")
    
    # Try installation up to 3 times
    max_attempts = 3
    success = False
    
    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt}/{max_attempts} to install frontend dependencies...")
        
        # Install dependencies
        print(f"Running: {' '.join(npm_cmd)} install")
        install_cmd = npm_cmd + ["install"]
        
        try:
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Frontend dependencies installed successfully")
                success = True
                break
            else:
                print(f"❌ Error installing frontend dependencies (attempt {attempt}):")
                print(f"Exit code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                
                # If npm not found, try different approach
                if "not recognized" in result.stderr or "no se reconoce" in result.stderr:
                    print("Trying alternative npm approach...")
                    # Try explicit path on Windows
                    if os.name == 'nt':
                        alt_npm = os.path.join("C:", os.sep, "Program Files", "nodejs", "npm.cmd")
                        if os.path.exists(alt_npm):
                            print(f"Found alternative npm at: {alt_npm}")
                            result = subprocess.run([alt_npm, "install"], capture_output=True, text=True)
                            if result.returncode == 0:
                                print("✅ Frontend dependencies installed with alternative npm")
                                success = True
                                break
                
                # Wait before retrying
                if attempt < max_attempts:
                    print(f"Waiting 5 seconds before retrying...")
                    time.sleep(5)
                    
        except subprocess.TimeoutExpired:
            print(f"❌ Installation timed out (attempt {attempt})")
            if attempt < max_attempts:
                print(f"Waiting 5 seconds before retrying...")
                time.sleep(5)
        except Exception as e:
            print(f"❌ Unexpected error during installation: {str(e)}")
            if attempt < max_attempts:
                print(f"Waiting 5 seconds before retrying...")
                time.sleep(5)
    
    # Change back to original directory
    os.chdir(current_dir)
    
    return success

def start_backend():
    """Start the backend server"""
    print("\nStarting the backend server...")
    
    # Use absolute path for backend directory
    backend_dir = os.path.join(DEPLOY_DIR, "backend")
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found at {backend_dir}")
        return None
    
    # Save current directory
    current_dir = os.getcwd()
    
    # Change to backend directory
    os.chdir(backend_dir)
    print(f"Changed to directory: {os.getcwd()}")
    
    # Start the Flask app
    flask_process = subprocess.Popen([sys.executable, "app.py"])
    
    # Change back to original directory
    os.chdir(current_dir)
    
    print("✅ Backend server started")
    return flask_process

def start_frontend():
    """Start the frontend development server"""
    print("\nStarting the frontend server...")
    
    # Use absolute path for frontend directory
    frontend_dir = os.path.join(DEPLOY_DIR, "frontend")
    if not os.path.exists(frontend_dir):
        print(f"❌ Frontend directory not found at {frontend_dir}")
        return None
    
    # Save current directory
    current_dir = os.getcwd()
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    print(f"Changed to directory: {os.getcwd()}")
    
    # Get npm command
    npm_cmd = get_npm_command()
    if not npm_cmd:
        print("❌ Cannot find npm. Please make sure Node.js is installed correctly.")
        os.chdir(current_dir)
        return None
    
    # Try to find a direct path to npm on Windows
    if os.name == 'nt':
        npm_direct_path = os.path.join("C:", os.sep, "Program Files", "nodejs", "npm.cmd")
        if os.path.exists(npm_direct_path) and (not npm_cmd or npm_cmd[0] != npm_direct_path):
            print(f"Using direct npm path: {npm_direct_path}")
            npm_cmd = [npm_direct_path]
    
    # Ensure node_modules exists, install dependencies if not
    node_modules_path = os.path.join(frontend_dir, "node_modules")
    if not os.path.exists(node_modules_path) or not os.listdir(node_modules_path):
        print("node_modules not found or empty, installing dependencies first...")
        install_cmd = npm_cmd + ["install"]
        try:
            print(f"Running: {' '.join(install_cmd)}")
            subprocess.run(install_cmd, check=True, timeout=300)
            print("Dependencies installed successfully")
        except Exception as e:
            print(f"❌ Error installing dependencies: {str(e)}")
            os.chdir(current_dir)
            return None
    
    # Start the React app with specific environment
    print(f"Running: {' '.join(npm_cmd)} start")
    
    # Create a copy of the environment with the correct PATH
    env = os.environ.copy()
    if os.name == 'nt':
        # Ensure Node.js is in PATH on Windows
        if os.path.exists("C:\\Program Files\\nodejs"):
            nodejs_path = "C:\\Program Files\\nodejs"
            print(f"Adding Node.js path to environment: {nodejs_path}")
            if "PATH" in env:
                env["PATH"] = f"{nodejs_path};{env['PATH']}"
            else:
                env["PATH"] = nodejs_path
    
    try:
        start_cmd = npm_cmd + ["start"]
        frontend_process = subprocess.Popen(start_cmd, env=env)
        print("✅ Frontend server started")
    except Exception as e:
        print(f"❌ Error starting frontend: {str(e)}")
        frontend_process = None
    
    # Change back to original directory
    os.chdir(current_dir)
    
    return frontend_process

def main():
    """Main function to run the WanderMatch deployment"""
    print("WanderMatch Deployment Runner")
    print("============================\n")
    
    # Print current directory and deploy directory
    print(f"Current directory: {os.getcwd()}")
    print(f"Deploy directory: {DEPLOY_DIR}")
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed. Exiting...")
        return
    
    # Install frontend dependencies
    if not setup_frontend_dependencies():
        print("❌ Setup failed. Exiting...")
        return
    
    # Start backend server
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend server. Exiting...")
        return
    
    # Wait for backend to initialize
    print("Waiting for backend server to initialize...")
    time.sleep(3)
    
    # Start frontend server
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend server. Exiting...")
        backend_process.terminate()
        return
    
    # Wait for frontend to initialize
    print("Waiting for frontend server to initialize...")
    time.sleep(5)
    
    # Open the application in the browser
    print("\nOpening application in browser...")
    try:
        webbrowser.open("http://localhost:3000")
        print("✅ Application opened in browser")
    except Exception as e:
        print(f"❌ Error opening browser: {str(e)}")
        print("Please open http://localhost:3000 in your browser manually")
    
    print("\n✅ WanderMatch deployment is running!")
    print("Backend server: http://localhost:5000")
    print("Frontend server: http://localhost:3000")
    print("\nPress Ctrl+C to stop the servers\n")
    
    try:
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        frontend_process.terminate()
        backend_process.terminate()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main() 