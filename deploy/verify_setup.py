#!/usr/bin/env python
"""
Verification script for the WanderMatch deployment.
Checks that all required files and dependencies are available.
"""
import os
import sys
import importlib
import subprocess
import shutil

# Get the absolute path of the deploy directory
DEPLOY_DIR = os.path.dirname(os.path.abspath(__file__))

def check_python_packages():
    """Check if required Python packages are installed"""
    required_packages = ['flask', 'flask_cors', 'pandas', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ Package found: {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ Package missing: {package}")
    
    return missing_packages

def check_file_structure():
    """Check if required files and directories exist"""
    required_files = [
        'backend/app.py',
        'backend/run_api.py',
        'backend/test_api.py',
        'frontend/package.json',
        'frontend/src/App.tsx',
        'frontend/src/components/Landing/index.tsx',
        'frontend/src/components/Survey/index.tsx',
        'frontend/src/components/Survey/SurveyForm.tsx',
        'frontend/src/components/Survey/SurveySuccess.tsx',
        'frontend/src/types/index.ts',
        'frontend/src/assets/travel.svg'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = os.path.join(DEPLOY_DIR, file_path)
        if os.path.exists(full_path):
            print(f"✅ File found: {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ File missing: {full_path}")
    
    return missing_files

def check_node_npm():
    """Check if Node.js and npm are installed and their versions"""
    node_available = False
    npm_available = False
    
    # Check for Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js version: {version}")
            node_available = True
        else:
            print("❌ Node.js check failed")
    except:
        print("❌ Node.js not found")
    
    # Check for npm directly
    npm_path = shutil.which("npm")
    if npm_path:
        try:
            result = subprocess.run([npm_path, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ npm version: {version} (path: {npm_path})")
                npm_available = True
            else:
                print(f"❌ npm check failed (path: {npm_path})")
        except:
            print(f"❌ Error running npm at {npm_path}")
    else:
        print("❌ npm not found in PATH")
        
        # If node is available but npm isn't, try to find npm relative to node
        if node_available:
            node_path = shutil.which("node")
            node_dir = os.path.dirname(node_path)
            print(f"Looking for npm relative to Node.js at: {node_dir}")
            
            possible_npm_paths = [
                os.path.join(node_dir, "npm"),
                os.path.join(node_dir, "npm.cmd"),
                os.path.join(os.path.dirname(node_dir), "npm"),
                os.path.join(os.path.dirname(node_dir), "npm.cmd")
            ]
            
            for path in possible_npm_paths:
                if os.path.exists(path):
                    print(f"✅ Found npm at: {path}")
                    npm_available = True
                    break
    
    return node_available, npm_available

def main():
    """Main verification function"""
    print("WanderMatch Deployment Verification")
    print("==================================\n")
    
    # Print current directory and deploy directory
    print(f"Current directory: {os.getcwd()}")
    print(f"Deploy directory: {DEPLOY_DIR}")
    
    # Check Python packages
    print("\nChecking Python packages:")
    missing_packages = check_python_packages()
    
    # Check Node.js and npm
    print("\nChecking Node.js and npm:")
    node_available, npm_available = check_node_npm()
    
    # Check file structure
    print("\nChecking file structure:")
    missing_files = check_file_structure()
    
    # Check for top-level directories
    if not os.path.isdir(os.path.join(DEPLOY_DIR, "frontend")):
        print("❌ Critical: 'frontend' directory is missing!")
        missing_files.append("frontend")
    else:
        print("✅ Directory found: frontend")
    
    if not os.path.isdir(os.path.join(DEPLOY_DIR, "backend")):
        print("❌ Critical: 'backend' directory is missing!")
        missing_files.append("backend")
    else:
        print("✅ Directory found: backend")
    
    # Print summary
    print("\nVerification Summary:")
    print("====================")
    
    if missing_packages:
        print(f"❌ Missing Python packages: {', '.join(missing_packages)}")
        print("   Run: pip install " + " ".join(missing_packages))
    else:
        print("✅ All required Python packages are installed")
    
    if not node_available:
        print("❌ Node.js is not available")
        print("   Please install Node.js from https://nodejs.org/")
    else:
        print("✅ Node.js is available")
    
    if not npm_available:
        print("❌ npm is not available or not properly configured")
        print("   Please ensure npm is installed and in your PATH")
    else:
        print("✅ npm is available")
    
    if missing_files:
        print(f"❌ Missing files/directories: {len(missing_files)}")
        for file in missing_files:
            print(f"   - {file}")
        
        # Special help for critical directories
        if "frontend" in missing_files or "backend" in missing_files:
            print("\n⚠️ Critical directories are missing. Please verify your directory structure:")
            print(f"   The deploy directory should be: {DEPLOY_DIR}")
            print("   It should contain 'frontend' and 'backend' subdirectories")
            print("   Make sure you're running this script from the correct location")
    else:
        print("✅ All required files and directories are present")
    
    # Final verdict
    if not missing_packages and node_available and npm_available and not missing_files:
        print("\n✅ All checks passed! You can run the deployment.")
        print("   Run: python run_deployment.py")
    else:
        print("\n❌ Some checks failed. Please fix the issues before running the deployment.")
        
        # Extra guidance for npm/node issues
        if not node_available or not npm_available:
            print("\n⚠️ Node.js/npm issues detected:")
            print("   1. Make sure Node.js is installed from https://nodejs.org/")
            print("   2. Make sure it's added to your PATH environment variable")
            print("   3. If npm is not found but Node.js is, try reinstalling Node.js")
            print("      Or manually find npm and add its location to your PATH")

if __name__ == "__main__":
    main() 