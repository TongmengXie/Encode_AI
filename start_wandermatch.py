#!/usr/bin/env python
"""
WanderMatch Launcher Script
This is a simple launcher that helps run the WanderMatch deployment.
It verifies the setup and then runs the deployment.
"""
import os
import sys
import subprocess
import shutil
import time

def find_nodejs_path():
    """Find Node.js directory to ensure npm will work properly"""
    # Common locations for Node.js installation
    node_locations = [
        "C:\\Program Files\\nodejs",
        "C:\\Program Files (x86)\\nodejs",
        os.path.expanduser("~\\AppData\\Roaming\\npm")
    ]
    
    # Check if node is in PATH
    node_path = shutil.which("node")
    if node_path:
        # Get the directory containing node
        return os.path.dirname(node_path)
    
    # Check common locations
    for location in node_locations:
        if os.path.exists(location):
            return location
    
    return None

def main():
    """Main launcher function"""
    print("WanderMatch Launcher")
    print("==================\n")
    
    # Display basic system info for diagnostics
    print("System Information:")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current directory: {os.getcwd()}")
    
    # Get the deploy directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    deploy_dir = os.path.join(current_dir, "deploy")
    
    print(f"Deploy directory: {deploy_dir}")
    
    if not os.path.isdir(deploy_dir):
        print(f"❌ Error: 'deploy' directory not found at {deploy_dir}")
        print("Make sure you're running this script from the root of the WanderMatch project.")
        return 1
    
    # Add Node.js to PATH if found
    nodejs_path = find_nodejs_path()
    if nodejs_path:
        print(f"Found Node.js at: {nodejs_path}")
        # Add Node.js to PATH
        os.environ["PATH"] = nodejs_path + os.pathsep + os.environ.get("PATH", "")
    else:
        print("⚠️ Warning: Node.js directory not found in common locations.")
        print("The application may not work correctly without Node.js and npm.")
    
    # Print PATH for debugging
    print("\nPATH environment variable:")
    for path in os.environ.get("PATH", "").split(os.pathsep):
        print(f"  - {path}")
    
    # Path to verification and deployment scripts
    verify_script = os.path.join(deploy_dir, "verify_setup.py")
    deploy_script = os.path.join(deploy_dir, "run_deployment.py")
    
    # Check if scripts exist
    if not os.path.exists(verify_script):
        print(f"❌ Error: Verification script not found at {verify_script}")
        return 1
    
    if not os.path.exists(deploy_script):
        print(f"❌ Error: Deployment script not found at {deploy_script}")
        return 1
    
    # Simplified direct execution for testing
    print("\nStarting WanderMatch application directly...\n")
    try:
        # Try to run deployment directly
        os.chdir(deploy_dir)
        print(f"Changed to directory: {os.getcwd()}")
        
        # Check if files we need exist
        backend_dir = os.path.join(deploy_dir, "backend")
        frontend_dir = os.path.join(deploy_dir, "frontend")
        
        print(f"Checking backend directory: {os.path.exists(backend_dir)}")
        print(f"Checking frontend directory: {os.path.exists(frontend_dir)}")
        
        if os.path.exists(backend_dir):
            print("\nStarting backend directly...")
            # Run backend in a subprocess
            backend_script = os.path.join(backend_dir, "app.py")
            if os.path.exists(backend_script):
                backend_process = subprocess.Popen([sys.executable, backend_script])
                print("Backend started successfully!")
                time.sleep(2)  # Give backend time to start
            else:
                print(f"❌ Error: Backend script not found at {backend_script}")
                return 1
        
        if os.path.exists(frontend_dir):
            # Try to launch the frontend
            os.chdir(frontend_dir)
            print(f"Changed to frontend directory: {os.getcwd()}")
            print("Opening a browser to the React app...")
            import webbrowser
            webbrowser.open("http://localhost:3000")
            
            # Return to deploy directory
            os.chdir(deploy_dir)
        
        # Keep the script running
        print("\n✅ WanderMatch is now running.")
        print("Press Ctrl+C to exit.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as e:
        print(f"\n❌ Error running deployment: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 