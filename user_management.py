#!/usr/bin/env python
"""
User management functions for WanderMatch.
Contains functions for getting user information and selecting travel partners.
"""
import os
import sys
import pandas as pd
import time
import traceback
from typing import Dict, Any, Optional, List
from ui_utils import print_header, print_info, print_success, print_error, print_warning, input_prompt, clear_screen

# Constants
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_INFO_MATCH_DIR = os.path.join(WORKSPACE_DIR, "UserInfo_and_Match")
SURVEY_RESULTS_DIR = os.path.join(USER_INFO_MATCH_DIR, "survey_results")
SIMILARITY_MATRICES_DIR = os.path.join(USER_INFO_MATCH_DIR, "similarity_matrices")
PARTNER_MATCHES_DIR = os.path.join(USER_INFO_MATCH_DIR, "partner_matches")

# Create directories if they don't exist
for directory in [USER_INFO_MATCH_DIR, SURVEY_RESULTS_DIR, SIMILARITY_MATRICES_DIR, PARTNER_MATCHES_DIR]:
    os.makedirs(directory, exist_ok=True)

def get_user_info():
    """
    Collect user information for travel planning using the online survey if available.
    Falls back to manual input if the online survey isn't accessible.
    
    Returns:
        Dictionary containing user information
    """
    print_header("User Information Collection", emoji="[USER]")
    
    # Path to get_user_info folder
    get_user_info_dir = os.path.join(WORKSPACE_DIR, "get_user_info")
    backend_dir = os.path.join(get_user_info_dir, "backend")
    frontend_dir = os.path.join(get_user_info_dir, "frontend")
    embed_info_path = os.path.join(get_user_info_dir, "embed_info.py")
    
    # Check if the run_info.py script exists
    run_info_path = os.path.join(get_user_info_dir, "run_info.py")
    
    if os.path.exists(run_info_path):
        print_info("Launching online survey to collect user information...")
        
        try:
            # Run the survey script to collect user info
            import subprocess
            
            # Start the survey process
            survey_process = subprocess.Popen([sys.executable, run_info_path], 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE,
                                             universal_newlines=True)
            
            print_info("Online survey launched. Please complete the survey in your browser.")
            print_info("When you have completed the survey, you'll see a thank you page.")
            print_info("After seeing the thank you page, return here and press Enter to continue...")
            
            # Wait for user to indicate they've completed the survey
            input_prompt("Press Enter after completing the survey...")
            
            # Try to terminate the survey process
            try:
                survey_process.terminate()
                print_info("Survey servers stopped.")
            except:
                print_warning("Could not stop survey servers. They may still be running in the background.")
            
            # Wait a moment for any file operations to complete
            time.sleep(2)
            
            # Calculate embeddings if embed_info.py exists
            if os.path.exists(embed_info_path):
                print_info("Calculating embeddings for the new user data...")
                try:
                    # Run the embed_info.py script to calculate embeddings
                    embed_process = subprocess.run(
                        [sys.executable, embed_info_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8',  # Explicitly use UTF-8
                        errors='replace',  # Replace any problematic characters
                        cwd=get_user_info_dir  # Run from the get_user_info directory
                    )
                    
                    if embed_process.returncode == 0:
                        print_success("Embeddings calculated successfully.")
                    else:
                        print_warning(f"Embeddings calculation returned code {embed_process.returncode}.")
                        print_warning(f"Error: {embed_process.stderr}")
                except Exception as e:
                    print_warning(f"Error calculating embeddings: {str(e)}")
            
            # Check for the latest user answer file in the survey results directory
            if os.path.exists(SURVEY_RESULTS_DIR):
                csv_files = [f for f in os.listdir(SURVEY_RESULTS_DIR) if f.startswith("user_answer_") and f.endswith(".csv")]
                
                if csv_files:
                    # Sort files by timestamp to get the most recent one
                    latest_file = sorted(csv_files, reverse=True)[0]
                    user_csv_path = os.path.join(SURVEY_RESULTS_DIR, latest_file)
                    print_info(f"Using user data from survey results directory: {latest_file}")
                else:
                    print_warning("No user data files found.")
                    return fallback_user_info()
                
                try:
                    import pandas as pd
                    import numpy as np
                    
                    # Read the user data
                    user_df = pd.read_csv(user_csv_path)
                    
                    if not user_df.empty:
                        # Fill NaN values with default values
                        default_values = {
                            'real_name': 'Anonymous Traveler',
                            'age_group': '25–34',
                            'gender': 'Not specified',
                            'nationality': 'International',
                            'preferred_residence': 'Various locations',
                            'cultural_symbol': 'Local cuisine',
                            'bucket_list': 'Nature exploration',
                            'healthcare_expectations': 'Basic healthcare access',
                            'travel_budget': '$1000',
                            'currency_preferences': 'Credit card',
                            'insurance_type': 'Basic travel',
                            'past_insurance_issues': 'None',
                            'travel_season': 'Summer',
                            'stay_duration': '1-2 weeks',
                            'interests': 'Cultural experiences',
                            'personality_type': 'Balanced',
                            'communication_style': 'Moderate',
                            'travel_style': 'Mix of planned and spontaneous',
                            'accommodation_preference': 'Mid-range hotel'
                        }
                        
                        # Replace NaN values with defaults
                        user_df = user_df.fillna(default_values)
                        
                        # Replace empty strings with defaults
                        for col in user_df.columns:
                            if col in default_values:
                                user_df[col] = user_df[col].apply(lambda x: default_values[col] if pd.isna(x) or x == '' or str(x).strip() == '' else x)
                        
                        # Convert first row to dictionary
                        user_info = user_df.iloc[0].to_dict()
                        print_success("User data collected successfully!")
                        
                        # Print user information summary
                        print_header("User Information Summary", emoji="[USER]")
                        for key, value in user_info.items():
                            # Skip columns with special characters or empty values
                            if pd.notna(value) and str(value).strip() and not key.startswith("Unnamed"):
                                print(f"{key}: {value}")
                        
                        # Map fields to match the expected format
                        user_info["name"] = user_info.get("real_name", "Anonymous Traveler")
                        user_info["interests"] = [user_info.get("cultural_symbol", "Local culture"), 
                                                user_info.get("bucket_list", "Nature exploration")]
                        age_group = user_info.get("age_group", "25-34")
                        if '–' in age_group:
                            # Extract first number from age range
                            user_info["age"] = age_group.split('–')[0]
                        else:
                            user_info["age"] = "30"  # Default age
                        
                        # Map budget_preference
                        budget = user_info.get("travel_budget", "$1000")
                        if '$' in budget:
                            # Extract budget amount
                            amount = int(budget.replace('$', '').replace(',', ''))
                            if amount < 1500:
                                user_info["budget_preference"] = "Low"
                            elif amount < 3000:
                                user_info["budget_preference"] = "Medium"
                            else:
                                user_info["budget_preference"] = "High"
                        else:
                            user_info["budget_preference"] = "Medium"
                        
                        # Default travel style
                        user_info["travel_style"] = user_info.get("travel_style", "Cultural")
                        
                        return user_info
                    
                except Exception as e:
                    print_warning(f"Error reading user data: {str(e)}")
                    print_warning("Falling back to manual user information collection.")
            else:
                print_warning("Survey results directory not found.")
        except Exception as e:
            print_warning(f"Error launching survey: {str(e)}")
            print_warning("Falling back to manual user information collection.")
    else:
        print_warning("Survey script not found. Using manual input method.")
    
    return fallback_user_info()

def fallback_user_info():
    """
    Fallback method to collect user information manually.
    Used when the online survey is not available or fails.
    
    Returns:
        Dictionary containing user information
    """
    # Fall back to using existing user data if survey fails
    user_info = {}
    
    # Check if there are any user_answer_*.csv files in the survey results directory
    if os.path.exists(SURVEY_RESULTS_DIR):
        csv_files = [f for f in os.listdir(SURVEY_RESULTS_DIR) if f.startswith("user_answer_") and f.endswith(".csv")]
        if csv_files:
            # Sort files by timestamp to get the most recent one
            latest_file = sorted(csv_files, reverse=True)[0]
            user_csv_path = os.path.join(SURVEY_RESULTS_DIR, latest_file)
            print_info(f"Using existing user data from: {latest_file}")
            
            try:
                import pandas as pd
                import numpy as np
                
                # Read the user data with default values for NaN
                user_df = pd.read_csv(user_csv_path)
                
                if not user_df.empty:
                    # Fill NaN values with default values
                    default_values = {
                        'real_name': 'Anonymous Traveler',
                        'age_group': '25–34',
                        'gender': 'Not specified',
                        'nationality': 'International',
                        'preferred_residence': 'Various locations',
                        'cultural_symbol': 'Local cuisine',
                        'bucket_list': 'Nature exploration',
                        'healthcare_expectations': 'Basic healthcare access',
                        'travel_budget': '$1000',
                        'currency_preferences': 'Credit card',
                        'insurance_type': 'Basic travel',
                        'past_insurance_issues': 'None',
                        'travel_season': 'Summer',
                        'stay_duration': '1-2 weeks',
                        'interests': 'Cultural experiences',
                        'personality_type': 'Balanced',
                        'communication_style': 'Moderate',
                        'travel_style': 'Mix of planned and spontaneous',
                        'accommodation_preference': 'Mid-range hotel'
                    }
                    
                    # Replace NaN values with defaults
                    user_df = user_df.fillna(default_values)
                    
                    # Replace empty strings with defaults
                    for col in user_df.columns:
                        if col in default_values:
                            user_df[col] = user_df[col].apply(lambda x: default_values[col] if pd.isna(x) or x == '' or str(x).strip() == '' else x)
                    
                    # Convert first row to dictionary
                    user_info = user_df.iloc[0].to_dict()
                    print_success("Existing user data loaded successfully!")
                    
                    # Print user information summary
                    print_header("User Information", emoji="[USER]")
                    for key, value in user_info.items():
                        # Skip columns with special characters or empty values
                        if pd.notna(value) and str(value).strip() and not key.startswith("Unnamed"):
                            print(f"{key}: {value}")
                    
                    # Map fields to match the expected format
                    user_info["name"] = user_info.get("real_name", "Anonymous Traveler")
                    user_info["interests"] = [user_info.get("cultural_symbol", "Local culture"), 
                                             user_info.get("bucket_list", "Nature exploration")]
                    age_group = user_info.get("age_group", "25-34")
                    if '–' in age_group:
                        # Extract first number from age range
                        user_info["age"] = age_group.split('–')[0]
                    else:
                        user_info["age"] = "30"  # Default age
                    
                    # Map budget_preference
                    budget = user_info.get("travel_budget", "$1000")
                    if '$' in budget:
                        # Extract budget amount
                        amount = int(budget.replace('$', '').replace(',', ''))
                        if amount < 1500:
                            user_info["budget_preference"] = "Low"
                        elif amount < 3000:
                            user_info["budget_preference"] = "Medium"
                        else:
                            user_info["budget_preference"] = "High"
                    else:
                        user_info["budget_preference"] = "Medium"  # Default
                    
                    # Default travel style
                    user_info["travel_style"] = user_info.get("travel_style", "Cultural")
                    
                    return user_info
                
            except Exception as e:
                print_warning(f"Error reading user data: {str(e)}")
    
    # If no user data found or error occurred, use manual input
    print_info("Please provide some information about yourself.")
    
    # Basic information with manual input
    user_info = {}
    user_info["name"] = input_prompt("What is your name?", default="Traveler")
    user_info["age_group"] = input_prompt("What is your age group?", default="25-34")
    user_info["gender"] = input_prompt("What is your gender?", default="Not specified")
    user_info["nationality"] = input_prompt("What is your nationality?", default="International")
    
    # Travel preferences
    print_header("Travel Preferences", emoji="[TRAVEL]")
    user_info["travel_style"] = input_prompt("What is your travel style?", default="Mix of popular sites and hidden gems")
    user_info["budget"] = input_prompt("What is your travel budget? (Daily in USD)", default="$100-200")
    user_info["interests"] = input_prompt("What are your main travel interests?", default="Food, culture, nature")
    
    # Map additional fields to expected format
    user_info["real_name"] = user_info["name"]
    user_info["age"] = user_info["age_group"].split("-")[0]
    
    # Map budget to budget_preference
    budget_str = user_info["budget"]
    if "$" in budget_str:
        amount = 0
        try:
            # Try to extract the numeric part
            import re
            matches = re.findall(r'\d+', budget_str)
            if matches:
                amount = int(matches[0])
        except:
            amount = 150  # Default value
            
        if amount < 100:
            user_info["budget_preference"] = "Low"
        elif amount < 300:
            user_info["budget_preference"] = "Medium"
        else:
            user_info["budget_preference"] = "High"
    else:
        user_info["budget_preference"] = "Medium"  # Default
    
    # Save the manually collected user information to a CSV file in the survey results directory
    try:
        import pandas as pd
        from datetime import datetime
        
        # Create a DataFrame from the user_info dictionary
        df = pd.DataFrame([user_info])
        
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(SURVEY_RESULTS_DIR, f"user_answer_{timestamp}.csv")
        
        # Save the CSV file
        df.to_csv(filepath, index=False, encoding='utf-8')
        print_success(f"User information saved to: {filepath}")
    except Exception as e:
        print_warning(f"Error saving user information to CSV: {str(e)}")
    
    print_success(f"Thank you, {user_info['name']}! Your profile has been created.")
    return user_info

def select_travel_partner(user_info):
    """
    Display potential travel partners and let the user select one.
    
    Args:
        user_info (dict): The user's profile information
        
    Returns:
        dict: Selected partner info or None if traveling solo
    """
    print_header("Travel Partner Selection", emoji="[PARTNER]")
    
    # Try to use get_user_info directory's partner selection
    try:
        from get_user_info.embed_info import run_matching
        
        # Check if partner matching is available
        top_matches = run_matching(top_k=5, output_dir=PARTNER_MATCHES_DIR, silent=True)
        
        if top_matches and len(top_matches) > 0:
            print_success("Found potential travel partners based on your profile!")
            
            # Load user pool to get partner details
            user_pool_path = os.path.join(WORKSPACE_DIR, "get_user_info", "user_pool.csv")
            
            if os.path.exists(user_pool_path):
                try:
                    user_pool = pd.read_csv(user_pool_path)
                    potential_partners = []
                    
                    # Process matches into a standardized format
                    for i, (idx, score) in enumerate(top_matches):
                        user_row = user_pool.iloc[idx]
                        partner = {
                            "name": user_row.get('real_name', f'Partner {i+1}'),
                            "nationality": user_row.get('nationality', 'Unknown'),
                            "age": user_row.get('age_group', 'Unknown'),
                            "interests": [user_row.get('bucket_list', 'Various activities')],
                            "match_percentage": int(score * 100),
                            "original_idx": idx
                        }
                        potential_partners.append(partner)
                    
                    # Display partners using simple text formatting
                    print_header("Your Potential Travel Partners", emoji="[PARTNERS]")
                    for i, partner in enumerate(potential_partners, 1):
                        print(f"{i}. {partner['name']} - Match Score: {partner['match_percentage']}%")
                        print(f"   Nationality: {partner['nationality']}")
                        print(f"   Age: {partner['age']}")
                        print(f"   Interests: {', '.join(partner['interests'])}")
                        print()
                    
                    # Ask user to select a partner
                    selection = input_prompt("Select a travel partner by number (or 0 to travel solo)", default="1")
                    
                    try:
                        selection = int(selection)
                        if selection == 0:
                            print_info("You've chosen to travel solo. Adventure awaits!")
                            return None
                        elif 1 <= selection <= len(top_matches):
                            idx, _ = top_matches[selection-1]
                            partner_row = user_pool.iloc[idx]
                            partner_info = partner_row.to_dict()
                            print_success(f"You've selected {partner_info.get('real_name', f'Partner {selection}')} as your travel companion!")
                            return partner_info
                        else:
                            print_warning("Invalid selection. Traveling solo by default.")
                            return None
                    except ValueError:
                        print_warning("Invalid input. Traveling solo by default.")
                        return None
                
                except Exception as e:
                    print_error(f"Error loading user pool: {str(e)}")
            
        else:
            print_warning("No matching partners found.")
    
    except ImportError:
        print_warning("Partner matching module not available.")
    except Exception as e:
        print_error(f"Error in partner selection: {str(e)}")
    
    # Fallback to basic partner selection
    print_info("Using basic partner selection...")
    
    partner_options = [
        {"name": "Alex", "nationality": "American", "age": "25-34", "interests": "Food, hiking, photography"},
        {"name": "Jamie", "nationality": "British", "age": "35-44", "interests": "History, architecture, local cuisine"},
        {"name": "Sam", "nationality": "Australian", "age": "25-34", "interests": "Adventure sports, beaches, nightlife"},
    ]
    
    print_info("Available travel partners:")
    for i, partner in enumerate(partner_options):
        print(f"{i+1}. {partner['name']} ({partner['nationality']}, {partner['age']})")
        print(f"   Interests: {partner['interests']}")
        print()
    
    selection = input_prompt("Select a travel partner by number (or 0 to travel solo)", default="0")
    
    try:
        selection = int(selection)
        if selection == 0:
            print_info("You've chosen to travel solo. Adventure awaits!")
            return None
        elif 1 <= selection <= len(partner_options):
            partner_info = partner_options[selection-1]
            print_success(f"You've selected {partner_info['name']} as your travel companion!")
            return partner_info
        else:
            print_warning("Invalid selection. Traveling solo by default.")
            return None
    except ValueError:
        print_warning("Invalid input. Traveling solo by default.")
        return None 