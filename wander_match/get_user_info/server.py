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

# Get the current script directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Load environment variables from parent directory
load_dotenv(os.path.join(PARENT_DIR, '.env'))

# Create backend directory if it doesn't exist
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
os.makedirs(BACKEND_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Fields for the survey form (all are optional, defaults will be used if empty)
SURVEY_FIELDS = [
    'real_name', 'age_group', 'gender', 'nationality',
    'preferred_residence', 'cultural_symbol', 'bucket_list',
    'healthcare_expectations', 'travel_budget', 'currency_preferences',
    'insurance_type', 'past_insurance_issues'
]

@app.route('/')
def home():
    return 'WanderMatch Survey API is running!'

@app.route('/api/submit', methods=['POST', 'OPTIONS'])
def submit():
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    try:
        # Get the data from the request
        data = request.json
        if not data:
            print("Error: No data provided in request")
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        print(f"Received form data: {data}")
        
        # Process all fields, filling in defaults when empty
        for field in SURVEY_FIELDS:
            if field not in data or not data[field]:
                if field == 'real_name':
                    data[field] = "Anonymous Traveler"
                elif field == 'age_group':
                    data[field] = "25–34"
                elif field == 'gender':
                    data[field] = "Prefer not to say"
                elif field == 'nationality':
                    data[field] = "International"
                elif field == 'preferred_residence':
                    data[field] = "Swiss"
                elif field == 'cultural_symbol':
                    data[field] = "Local cuisine"
                elif field == 'bucket_list':
                    data[field] = "Nature exploration"
                elif field == 'healthcare_expectations':
                    data[field] = "Basic healthcare access"
                elif field == 'travel_budget':
                    data[field] = "$1000"
                elif field == 'currency_preferences':
                    data[field] = "Credit card"
                elif field == 'insurance_type':
                    data[field] = "Medical only"
                elif field == 'past_insurance_issues':
                    data[field] = "None"
                else:
                    data[field] = "Not specified"
                print(f"Filled missing field {field} with default value: {data[field]}")
        
        # Generate timestamp for the file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create a CSV file to store the data
        output_file = os.path.join(BACKEND_DIR, f"user_answer_{timestamp}.csv")
        
        # Convert data to DataFrame and save as CSV
        df = pd.DataFrame([data])
        df.to_csv(output_file, index=False)
        print(f"User data saved to {output_file}")
        
        # Return success status
        return jsonify({
            'status': 'success', 
            'message': 'Data submitted successfully', 
            'file': output_file
        })
    
    except Exception as e:
        print(f"Error processing form submission: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/get_user', methods=['GET'])
def get_user():
    try:
        # Get most recent user answer file from backend directory
        files = [f for f in os.listdir(BACKEND_DIR) if f.startswith("user_answer_") and f.endswith(".csv")]
        if not files:
            return jsonify({'status': 'error', 'message': 'No user data found'}), 404
        
        # Sort files by timestamp
        latest_file = sorted(files)[-1]
        file_path = os.path.join(BACKEND_DIR, latest_file)
        
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