#!/usr/bin/env python
"""
Final testing script for CSV file saving
"""
import os
import sys
import requests
import json
import glob
import pandas as pd
from datetime import datetime

# Get the current script directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Directory paths
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
USER_INFO_MATCH_DIR = os.path.join(PARENT_DIR, "UserInfo_and_Match")
SURVEY_RESULTS_DIR = os.path.join(USER_INFO_MATCH_DIR, "survey_results")

# Create directories if they don't exist
os.makedirs(BACKEND_DIR, exist_ok=True)
os.makedirs(SURVEY_RESULTS_DIR, exist_ok=True)

print(f"Backend directory: {os.path.abspath(BACKEND_DIR)}")
print(f"Survey results directory: {os.path.abspath(SURVEY_RESULTS_DIR)}")

# Function to count CSV files
def count_csv_files(directory):
    files = glob.glob(os.path.join(directory, "user_answer_*.csv"))
    return len(files)

# Function to submit test data
def submit_test_data(save_on_server=True):
    # Generate a unique test user
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Sample user data
    user_data = {
        'real_name': f'Final Test User ({timestamp})',
        'age_group': '25–34',
        'gender': 'Male',
        'nationality': 'Canadian',
        'preferred_residence': 'Mountain',
        'cultural_symbol': 'Architecture',
        'bucket_list': 'Adventure sports',
        'healthcare_expectations': 'Comprehensive coverage',
        'travel_budget': '$2000',
        'currency_preferences': 'Local currency',
        'insurance_type': 'Comprehensive',
        'past_insurance_issues': 'Minor claim issues',
        'save_on_server': save_on_server
    }
    
    try:
        # Submit the form data to the server
        response = requests.post(
            'http://localhost:5000/api/submit',
            json=user_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        # Check the response
        if response.status_code == 200:
            data = response.json()
            print(f"Form submitted successfully!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True, data
        else:
            print(f"Server returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except requests.exceptions.ConnectionError:
        print("Failed to connect to the server. Make sure the server is running.")
        return False, None
    except Exception as e:
        print(f"Error submitting form: {str(e)}")
        return False, None

# Main function
def main():
    print("\n=== Starting Final Test ===")
    
    # Check current file counts
    backend_before = count_csv_files(BACKEND_DIR)
    survey_before = count_csv_files(SURVEY_RESULTS_DIR)
    
    print(f"Files in backend directory: {backend_before}")
    print(f"Files in survey results directory: {survey_before}")
    
    print("\n=== Testing with save_on_server=True ===")
    success, data = submit_test_data(save_on_server=True)
    
    # Check file counts after submission
    backend_after = count_csv_files(BACKEND_DIR)
    survey_after = count_csv_files(SURVEY_RESULTS_DIR)
    
    print(f"Files in backend directory: {backend_after}")
    print(f"Files in survey results directory: {survey_after}")
    
    if success:
        # Check if file was created
        if 'path' in data:
            file_path = data['path']
            if os.path.exists(file_path):
                print(f"SUCCESS: File was created at: {file_path}")
            else:
                print(f"ERROR: File was not created at: {file_path}")
        else:
            print("WARNING: No file path in response")
        
        # Check for increase in file count
        if backend_after > backend_before or survey_after > survey_before:
            print("SUCCESS: New CSV file was created")
        else:
            print("ERROR: No new CSV file was created")
    
    print("\n=== Final Test Complete ===")

if __name__ == "__main__":
    main() 