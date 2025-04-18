#!/usr/bin/env python
"""
Survey Save Test Script
This script tests if survey results can be saved to the correct directory.
"""
import os
import time
import pandas as pd
import json

def test_save_survey():
    """Test saving a survey result to the specified directory"""
    print("Survey Save Test Script")
    print("======================\n")
    
    # Get the absolute path to the project root directory
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    
    # Create survey results directory path
    survey_results_dir = os.path.join(PROJECT_ROOT, 'UserInfo_and_Match', 'survey_results')
    
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Survey results directory: {survey_results_dir}")
    
    # Check if directory exists, create if it doesn't
    if not os.path.exists(survey_results_dir):
        try:
            os.makedirs(survey_results_dir, exist_ok=True)
            print(f"✅ Created survey results directory: {survey_results_dir}")
        except Exception as e:
            print(f"❌ Error creating directory: {str(e)}")
            return False
    else:
        print(f"✅ Survey results directory already exists")
    
    # Create a test survey data
    test_data = {
        "name": "Test User",
        "email": "test@example.com",
        "age": 30,
        "travel_preference": "Adventure",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Create timestamp for filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"test_answer_{timestamp}.csv"
    filepath = os.path.join(survey_results_dir, filename)
    
    # Convert data to DataFrame and save
    df = pd.DataFrame([test_data])
    
    try:
        # Save the CSV file
        df.to_csv(filepath, index=False)
        print(f"✅ Test survey saved to: {filepath}")
        
        # Verify the file was created
        if os.path.exists(filepath):
            print(f"✅ File verification passed")
            
            # Read back the file to confirm data integrity
            try:
                df_read = pd.read_csv(filepath)
                print(f"✅ Data read back successfully: {len(df_read)} rows")
                return True
            except Exception as e:
                print(f"❌ Error reading back the file: {str(e)}")
                return False
        else:
            print(f"❌ File was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error saving test survey: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_save_survey()
    print("\nTest result:", "PASSED" if result else "FAILED") 