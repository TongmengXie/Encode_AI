#!/usr/bin/env python
"""
Environment Check Utility
Checks if all required dependencies for the Travel Route Planner are installed.
"""
import os
import sys
import platform

def print_header(text):
    """Print a header with separation lines."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def check_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name.split('.')[0])
        return True
    except ImportError:
        return False

print_header("PYTHON ENVIRONMENT INFORMATION")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Platform: {platform.platform()}")
print(f"Current directory: {os.getcwd()}")

print_header("CHECKING REQUIRED DEPENDENCIES")
required_packages = [
    "dotenv",
    "requests", 
    "folium",
    "rich",
    "matplotlib",
    "google.generativeai",
    "openrouteservice"
]

for package in required_packages:
    if check_package(package):
        print(f"✓ {package} - Installed")
    else:
        print(f"✗ {package} - NOT FOUND")

print_header("ENVIRONMENT VARIABLES")
env_vars = ["GEMINI_API_KEY"]
for var in env_vars:
    value = os.getenv(var)
    if value:
        masked_value = value[:4] + "****" + value[-4:] if len(value) > 8 else "****"
        print(f"✓ {var} - Set ({masked_value})")
    else:
        print(f"✗ {var} - NOT SET")

print_header("PROJECT FILES")
required_files = [
    "main.py",
    "RouteGenerator_Hybrid.py",
    "visualize_route.py",
    "enhanced_visualization.py",
    ".env"
]

for file in required_files:
    if os.path.exists(file):
        print(f"✓ {file} - Found")
    else:
        print(f"✗ {file} - NOT FOUND")

print_header("RECOMMENDATION")
print("If you're having issues with missing dependencies, run:")
print("pip install google-generativeai folium rich matplotlib python-dotenv requests openrouteservice")
print("\nIf environment variables are missing, create a .env file with:")
print("GEMINI_API_KEY=your_api_key_here")
print("\nTo run the application, use:")
print("python main.py")
print("=" * 60) 