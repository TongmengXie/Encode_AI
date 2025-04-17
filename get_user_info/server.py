#!/usr/bin/env python
"""
WanderMatch Survey Server

This script starts a simple HTTP server to serve the survey form and handle form submissions.
"""
import os
import sys
import json
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import csv
import traceback

# Get the current script directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Print paths for debugging
print(f"Script directory: {SCRIPT_DIR}")
print(f"Parent directory: {PARENT_DIR}")

# Load environment variables from parent directory
load_dotenv(os.path.join(PARENT_DIR, '.env'))

# Use the PROJECT_PATH from .env file if available
PROJECT_PATH = os.getenv("PROJECT_PATH", PARENT_DIR)
print(f"Using project path: {PROJECT_PATH}")

# Create backend directory if it doesn't exist (for backwards compatibility)
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
os.makedirs(BACKEND_DIR, exist_ok=True)
print(f"Backend directory: {os.path.abspath(BACKEND_DIR)}")

# Create UserInfo_and_Match/survey_results directory
USER_INFO_MATCH_DIR = os.path.join(PROJECT_PATH, "UserInfo_and_Match")
SURVEY_RESULTS_DIR = os.path.join(USER_INFO_MATCH_DIR, "survey_results")
os.makedirs(SURVEY_RESULTS_DIR, exist_ok=True)
print(f"Survey results directory: {os.path.abspath(SURVEY_RESULTS_DIR)}")

# Define destination suggestions for quick lookup
DESTINATION_SUGGESTIONS = {
    "usa": ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco"],
    "france": ["Paris", "Nice", "Lyon", "Marseille", "Bordeaux"],
    "japan": ["Tokyo", "Kyoto", "Osaka", "Hokkaido", "Okinawa"],
    "default": ["Switzerland", "Japan", "France", "Italy", "Canada"]
}

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Survey fields - updated to match client-side fields
SURVEY_FIELDS = [
    'name', 'age', 'gender', 'nationality', 'destination', 
    'cultural_symbol', 'bucket_list', 'healthcare', 'budget', 
    'payment_preference', 'insurance', 'insurance_issues', 
    'travel_season', 'stay_duration', 'interests', 
    'personality_type', 'communication_style', 'travel_style', 
    'accommodation_preference', 'origin_city', 'destination_city'
]

# Default values for missing fields
DEFAULT_VALUES = {
    'name': 'Anonymous',
    'age': 'Not specified',
    'gender': 'Not specified',
    'nationality': 'Not specified',
    'destination': 'Not specified',
    'cultural_symbol': 'Not specified',
    'bucket_list': 'Not specified',
    'healthcare': 'Not specified',
    'budget': 'Not specified',
    'payment_preference': 'Not specified',
    'insurance': 'Not specified',
    'insurance_issues': 'Not specified',
    'travel_season': 'Not specified',
    'stay_duration': 'Not specified',
    'interests': 'Not specified',
    'personality_type': 'Not specified', 
    'communication_style': 'Not specified',
    'travel_style': 'Not specified',
    'accommodation_preference': 'Not specified',
    'origin_city': 'Not specified',
    'destination_city': 'Not specified'
}

# Initialize the survey_results directory
os.makedirs(SURVEY_RESULTS_DIR, exist_ok=True)

@app.route('/')
def home():
    return 'WanderMatch Survey API is running!'

@app.route('/api/submit', methods=['POST'])
def submit_survey():
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided', 'file_saved': False}), 400
        
        # Process the data - ensure all fields are present
        processed_data = {}
        for field in SURVEY_FIELDS:
            # Use the provided value or default
            processed_data[field] = data.get(field, DEFAULT_VALUES.get(field, 'Not specified'))
        
        # Create a timestamped filename for the CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"user_answer_{timestamp}.csv"
        filepath = os.path.join(SURVEY_RESULTS_DIR, filename)
        
        # Always save on server, ignore client-side save_on_server flag
        file_saved = False
        
        try:
            # Save the data to a CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=SURVEY_FIELDS)
                writer.writeheader()
                writer.writerow({field: processed_data.get(field, '') for field in SURVEY_FIELDS})
            
            file_saved = True
            print(f"Survey data saved to {filepath}")
        except Exception as e:
            print(f"Error saving CSV: {str(e)}")
            traceback.print_exc()
        
        # Return success response WITHOUT data needed for client-side CSV generation
        return jsonify({
            'success': True,
            'message': 'Survey data processed successfully',
            'file_saved': file_saved,
            'filepath': filepath if file_saved else None,
            # No processed_data or csv_fields to prevent client-side CSV generation
        })
        
    except Exception as e:
        print(f"Error processing survey: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': str(e), 
            'file_saved': False,
            # No data for client-side CSV generation
        }), 500

@app.route('/api/get_user', methods=['GET'])
def get_user():
    try:
        # Get most recent user answer file from survey results directory
        files = [f for f in os.listdir(SURVEY_RESULTS_DIR) if f.startswith("user_answer_") and f.endswith(".csv")]
        if not files:
            # Fall back to backend directory for backwards compatibility
            files = [f for f in os.listdir(BACKEND_DIR) if f.startswith("user_answer_") and f.endswith(".csv")]
            if not files:
                return jsonify({'status': 'error', 'message': 'No user data found'}), 404
            file_path = os.path.join(BACKEND_DIR, sorted(files)[-1])
        else:
            file_path = os.path.join(SURVEY_RESULTS_DIR, sorted(files)[-1])
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        user_data = df.iloc[0].to_dict()
        
        return jsonify({'status': 'success', 'data': user_data})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    try:
        origin = request.args.get('origin', '').lower()
        suggestions = DESTINATION_SUGGESTIONS.get(origin, DESTINATION_SUGGESTIONS['default'])
        return jsonify({'status': 'success', 'destinations': suggestions})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 