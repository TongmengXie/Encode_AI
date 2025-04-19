from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import time
import pandas as pd
import json
import traceback
from dotenv import load_dotenv
import sys

# Load environment variables from .env file if present
load_dotenv()

app = Flask(__name__)

# Configure CORS based on environment
if os.environ.get('ENVIRONMENT') == 'production':
    # In production, allow specific frontend domain and handle all Render variations
    allowed_origins = [
        'https://wandermatch-frontend-b17a.onrender.com',
        'https://wandermatch-frontend.onrender.com',
        'https://wandermatch-frontend-*.onrender.com'  # Explicit pattern for Render subdomains
    ]
    
    # Get allowed origin from environment if available
    if os.environ.get('ALLOWED_ORIGINS'):
        allowed_origins.append(os.environ.get('ALLOWED_ORIGINS'))
        
    # Add http variations for testing
    allowed_origins.extend([
        'http://wandermatch-frontend-b17a.onrender.com',
        'http://wandermatch-frontend.onrender.com',
        'http://wandermatch-frontend-*.onrender.com'
    ])
    
    print(f"Configuring CORS for production with specific origins: {allowed_origins}")
    # Log more detailed CORS configuration
    print(f"ALLOWED_ORIGINS from environment: {os.environ.get('ALLOWED_ORIGINS')}")
    
    # Use a more permissive CORS configuration for Render
    CORS(app, origins=allowed_origins, supports_credentials=True, allow_headers="*", expose_headers="*")
else:
    # In development, allow all origins
    CORS(app)
    print(f"Configuring CORS for development (all origins allowed)")

# Get the absolute path to the project root directory
# First try from environment variable, then fallback to computed path
PROJECT_ROOT = os.environ.get('BASE_DIR', 
                             os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

print(f"Project root directory: {PROJECT_ROOT}")
print(f"Current working directory: {os.getcwd()}")

# Survey results directory from environment or default
survey_results_dir = os.environ.get('SURVEY_RESULTS_DIR', 
                                   os.path.join(PROJECT_ROOT, 'UserInfo_and_Match', 'survey_results'))

# Log directory details
print(f"Survey results directory: {survey_results_dir}")
print(f"Directory exists: {os.path.exists(survey_results_dir)}")

# Create directory if it doesn't exist
try:
    os.makedirs(survey_results_dir, exist_ok=True)
    print(f"Survey results directory initialized: {survey_results_dir}")
    
    # Test write permissions
    test_file = os.path.join(survey_results_dir, "write_test.txt")
    with open(test_file, 'w') as f:
        f.write("Write test successful")
    os.remove(test_file)
    print(f"Write permissions verified for: {survey_results_dir}")
    
    # Show directory contents
    if os.path.exists(survey_results_dir):
        print(f"Directory contents of {survey_results_dir}: {os.listdir(survey_results_dir)}")
except Exception as e:
    print(f"ERROR creating survey directory: {e}")
    print(traceback.format_exc())

@app.route('/', methods=['GET'])
def root():
    """
    Root endpoint that provides API information and available endpoints.
    This makes the API more user-friendly when accessed directly.
    """
    api_info = {
        "name": "WanderMatch API",
        "version": "1.0.0",
        "description": "API for WanderMatch travel companion matching and travel planning",
        "status": "online",
        "documentation": "See README.md for API documentation",
        "available_endpoints": [
            {"path": "/api/health", "methods": ["GET"], "description": "Health check endpoint"},
            {"path": "/api/survey", "methods": ["POST"], "description": "Submit survey responses"},
            {"path": "/api/embedding", "methods": ["GET"], "description": "Calculate embeddings and find matches"},
            {"path": "/api/generate_blog", "methods": ["POST"], "description": "Generate a travel blog"},
            {"path": "/api/answer_question", "methods": ["POST"], "description": "Answer travel-related questions using LLM providers"}
        ],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Return API information as JSON
    return jsonify(api_info)

@app.route('/api/survey', methods=['POST'])
def save_survey():
    """
    API endpoint to save survey data.
    Accepts POST requests with JSON data and saves it to a CSV file.
    """
    try:
        # Log the incoming request with environment info
        print(f"Received survey submission request at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Survey directory: {survey_results_dir}")
        
        # Get JSON data
        data = request.json
        if not data:
            print("ERROR: No JSON data received")
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400
        
        print(f"Survey data received: {len(data)} fields")
        
        # Create timestamp for filename only, not storing it in the data
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"user_answer_{timestamp}.csv"
        
        # Convert data to DataFrame and save
        df = pd.DataFrame([data])
        
        # Ensure directory exists (double-check)
        try:
            os.makedirs(survey_results_dir, exist_ok=True)
            print(f"Ensured survey directory exists: {survey_results_dir}")
            print(f"Directory contents: {os.listdir(survey_results_dir)}")
        except Exception as e:
            error_msg = f"Error creating directory: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({
                "success": False, 
                "message": error_msg,
                "directory": survey_results_dir
            }), 500
        
        # Save the CSV file with detailed error handling
        try:
            # Save the CSV file
            filepath = os.path.join(survey_results_dir, filename)
            print(f"Attempting to save survey to: {filepath}")
            
            # Check if directory exists before saving
            if not os.path.exists(os.path.dirname(filepath)):
                error_msg = f"Directory does not exist: {os.path.dirname(filepath)}"
                print(error_msg)
                return jsonify({
                    "success": False, 
                    "message": error_msg
                }), 500
            
            # Save the file
            df.to_csv(filepath, index=False)
            
            # Verify the file was created
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"Survey saved successfully: {filepath} ({file_size} bytes)")
                
                return jsonify({
                    "success": True,
                    "message": "Survey saved successfully",
                    "filename": filename,
                    "filepath": filepath,
                    "size": file_size
                })
            else:
                error_msg = f"File was not created after save attempt: {filepath}"
                print(error_msg)
                return jsonify({
                    "success": False, 
                    "message": error_msg
                }), 500
                
        except Exception as e:
            error_msg = f"Error saving survey: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({
                "success": False, 
                "message": error_msg,
                "traceback": traceback.format_exc()
            }), 500
            
    except Exception as e:
        error_msg = f"Unexpected error processing survey submission: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({
            "success": False, 
            "message": error_msg,
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    # Check if survey directory exists and is writable
    dir_exists = os.path.exists(survey_results_dir)
    dir_writable = os.access(survey_results_dir, os.W_OK) if dir_exists else False
    
    return jsonify({
        "status": "healthy",
        "message": "WanderMatch API is running",
        "survey_dir": survey_results_dir,
        "dir_exists": dir_exists,
        "dir_writable": dir_writable,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/routes', methods=['GET'])
def generate_routes():
    """
    Generate transport route options between two cities
    
    Query parameters:
        origin: The origin city (default: London)
        destination: The destination city (default: Paris)
    """
    origin = request.args.get('origin', 'London')
    destination = request.args.get('destination', 'Paris')
    
    print(f"Generating transport routes from {origin} to {destination}")
    
    # Try to generate routes with LLMs first
    routes = []
    method_used = "default"
    
    # Check for OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        print("Found OpenAI API key - attempting to generate routes with OpenAI")
        try:
            routes = generate_routes_with_openai(origin, destination, openai_api_key)
            if routes:
                print(f"Successfully generated {len(routes)} routes with OpenAI")
                method_used = "openai"
        except Exception as e:
            print(f"Error generating routes with OpenAI: {str(e)}")
    else:
        print("OpenAI API key not found")
    
    # If OpenAI failed, try Gemini
    if not routes:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if gemini_api_key:
            print("Found Gemini API key - attempting to generate routes with Gemini")
            try:
                routes = generate_routes_with_gemini(origin, destination, gemini_api_key)
                if routes:
                    print(f"Successfully generated {len(routes)} routes with Gemini")
                    method_used = "gemini"
            except Exception as e:
                print(f"Error generating routes with Gemini: {str(e)}")
        else:
            print("Gemini API key not found")
    
    # If both LLMs failed, use default options
    if not routes:
        print("Using default transport options as fallback")
        routes = get_default_transport_options(origin, destination)
        method_used = "default"
    
    # Ensure we have 5-6 options
    if len(routes) < 5:
        print(f"Only generated {len(routes)} routes, adding default options to reach minimum of 5")
        default_routes = get_default_transport_options(origin, destination)
        # Add only missing transportation modes
        existing_modes = {route['mode'].lower() for route in routes}
        for route in default_routes:
            if route['mode'].lower() not in existing_modes and len(routes) < 6:
                routes.append(route)
                existing_modes.add(route['mode'].lower())
    
    # Limit to 6 options maximum
    routes = routes[:6]
    
    return jsonify({
        "success": True,
        "origin": origin,
        "destination": destination,
        "routes": routes,
        "method_used": method_used
    })

def generate_routes_with_openai(origin, destination, api_key):
    """
    Generate route options using OpenAI.
    
    Args:
        origin: Starting city
        destination: Destination city
        api_key: OpenAI API key
        
    Returns:
        List of transport option dictionaries
    """
    try:
        from openai import OpenAI
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Define the prompt
        prompt = f"""
        I need 5-6 detailed transport options to travel from {origin} to {destination}.
        
        For each transport mode (flight, train, bus, car, ferry, etc.), provide:
        - Duration (e.g., "2h 30m")
        - Approximate cost range in USD (e.g., "$120-150")
        - Carbon footprint level (e.g., "High", "Medium", "Low")
        - Comfort level (1-5 stars)
        - Brief pros and cons (1-2 short points each)
        
        BE CREATIVE and DIVERSE with the options. Include both common and less common but viable options.
        
        Format your response as a JSON array of objects, where each object follows this structure:
        {{
            "mode": "Flight",
            "duration": "2h 30m",
            "cost": "$200-300",
            "carbon_footprint": "High",
            "comfort_level": 4,
            "pros": ["Fastest option", "Direct connections available"],
            "cons": ["Security hassles", "Limited luggage"]
        }}
        
        Only include reasonable transport options for this route.
        Your response should contain ONLY the JSON array, nothing else.
        """
        
        # Generate content with OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a transportation expert that always responds with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        # Extract response text
        response_text = response.choices[0].message.content.strip()
        
        # Find JSON content (usually between code fences or brackets)
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_content = response_text[start_idx:end_idx]
            
            try:
                # Parse the JSON
                import json
                transport_options = json.loads(json_content)
                
                # Validate the results
                if isinstance(transport_options, list) and len(transport_options) > 0:
                    return transport_options
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from OpenAI: {str(e)}")
        
        # If we couldn't extract valid JSON, return an empty list
        print("Could not extract valid transport options from OpenAI response.")
        return []
    
    except Exception as e:
        print(f"Error generating transport options with OpenAI: {str(e)}")
        return []

def generate_routes_with_gemini(origin, destination, api_key):
    """
    Generate route options using Google's Gemini API.
    
    Args:
        origin: Starting city
        destination: Destination city
        api_key: Gemini API key
        
    Returns:
        List of transport option dictionaries
    """
    try:
        import google.generativeai as genai
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Set up the model
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 8192,
        }
        
        # Define the prompt
        prompt = f"""
        I need 5-6 detailed transport options to travel from {origin} to {destination}.
        
        For each transport mode (flight, train, bus, car, ferry, etc.), provide:
        - Duration (e.g., "2h 30m")
        - Approximate cost range in USD (e.g., "$120-150")
        - Carbon footprint level (e.g., "High", "Medium", "Low")
        - Comfort level (1-5 stars)
        - Brief pros and cons (1-2 short points each)
        
        BE CREATIVE and DIVERSE with the options. Include both common and less common but viable options.
        
        Format your response as a JSON array of objects, where each object follows this structure:
        {{
            "mode": "Flight",
            "duration": "2h 30m",
            "cost": "$200-300",
            "carbon_footprint": "High",
            "comfort_level": 4,
            "pros": ["Fastest option", "Direct connections available"],
            "cons": ["Security hassles", "Limited luggage"]
        }}
        
        Only include reasonable transport options for this route.
        """
        
        # Generate content with Gemini
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        
        # Find JSON content (usually between code fences or brackets)
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_content = response_text[start_idx:end_idx]
            
            try:
                # Parse the JSON
                import json
                transport_options = json.loads(json_content)
                
                # Validate the results
                if isinstance(transport_options, list) and len(transport_options) > 0:
                    return transport_options
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from Gemini: {str(e)}")
        
        # If we couldn't extract valid JSON, return an empty list
        print("Could not extract valid transport options from Gemini response.")
        return []
    
    except Exception as e:
        print(f"Error generating transport options with Gemini: {str(e)}")
        return []

def get_default_transport_options(origin, destination):
    """
    Generate default transport options for any city pair.
    
    Args:
        origin: Starting city
        destination: Destination city
        
    Returns:
        List of transport option dictionaries
    """
    # Default options that work for most city pairs
    return [
        {
            "mode": "Flight",
            "duration": "1h 30m - 4h",
            "cost": "$150-400",
            "carbon_footprint": "High",
            "comfort_level": 4,
            "pros": ["Fastest option", "Most reliable for long distances"],
            "cons": ["Environmental impact", "Airport hassles"]
        },
        {
            "mode": "Train",
            "duration": "3h - 8h",
            "cost": "$40-120",
            "carbon_footprint": "Medium",
            "comfort_level": 3,
            "pros": ["Scenic views", "City center to city center"],
            "cons": ["Limited schedules", "Can be delayed"]
        },
        {
            "mode": "Bus",
            "duration": "4h - 10h",
            "cost": "$20-60",
            "carbon_footprint": "Medium-Low",
            "comfort_level": 2,
            "pros": ["Budget-friendly", "Flexible booking"],
            "cons": ["Longer travel time", "Less comfort for long journeys"]
        },
        {
            "mode": "Car Rental",
            "duration": "Flexible",
            "cost": "$80-150 per day",
            "carbon_footprint": "Medium-High",
            "comfort_level": 4,
            "pros": ["Maximum flexibility", "Door-to-door convenience"],
            "cons": ["Parking challenges", "Driver fatigue on long trips"]
        },
        {
            "mode": "Rideshare",
            "duration": "Varies by distance",
            "cost": "$30-80",
            "carbon_footprint": "Medium",
            "comfort_level": 3,
            "pros": ["Share costs with others", "More environmentally friendly than solo driving"],
            "cons": ["Limited schedule flexibility", "Dependent on driver availability"]
        },
        {
            "mode": "Private Transfer",
            "duration": "Direct route timing",
            "cost": "$100-300",
            "carbon_footprint": "Medium-High",
            "comfort_level": 5,
            "pros": ["Door-to-door convenience", "Professional driver"],
            "cons": ["Higher cost", "Less environmentally friendly"]
        }
    ]

@app.route('/api/embedding', methods=['GET'])
def run_embedding():
    """
    API endpoint to trigger embedding calculation and partner matching.
    
    Returns:
        JSON with the results of the matching process.
    """
    try:
        print(f"Received embedding calculation request at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Survey directory: {survey_results_dir}")
        
        # List available survey files to confirm they exist
        try:
            survey_files = os.listdir(survey_results_dir)
            print(f"Survey files available: {survey_files}")
        except Exception as e:
            print(f"Error listing survey files: {e}")
        
        # Check if the embedding module exists
        get_user_info_dir = os.path.join(PROJECT_ROOT, "get_user_info")
        embed_info_path = os.path.join(get_user_info_dir, "embed_info.py")
        
        print(f"Checking for embed_info module at: {embed_info_path}")
        if not os.path.exists(embed_info_path):
            return jsonify({
                "success": False,
                "message": "Embedding calculation module not found",
                "path_checked": embed_info_path
            }), 404
        
        # Set up Python path to ensure proper imports
        if get_user_info_dir not in sys.path:
            sys.path.insert(0, get_user_info_dir)
            print(f"Added to sys.path: {get_user_info_dir}")
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
            print(f"Added to sys.path: {PROJECT_ROOT}")
        
        # Check for OpenAI API key in environment
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            # Look for a .env file in the project root
            from dotenv import load_dotenv
            
            # Try different possible locations for .env file
            possible_env_paths = [
                os.path.join(PROJECT_ROOT, ".env"),
                os.path.join(get_user_info_dir, ".env"),
                os.path.join(os.path.dirname(__file__), ".env")
            ]
            
            env_loaded = False
            for env_path in possible_env_paths:
                if os.path.exists(env_path):
                    print(f"Loading environment variables from: {env_path}")
                    load_dotenv(env_path)
                    env_loaded = True
                    break
            
            # Check if API key is available after loading .env
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                if env_loaded:
                    return jsonify({
                        "success": False,
                        "message": "OpenAI API key not found in environment variables. Please make sure OPENAI_API_KEY is set in the .env file."
                    }), 500
                else:
                    return jsonify({
                        "success": False,
                        "message": "No .env file found and no OPENAI_API_KEY in environment variables."
                    }), 500
        
        try:
            # Import the embedding module directly
            print("Importing embed_info module...")
            sys.path.append(os.path.dirname(get_user_info_dir))  # Add parent directory too
            
            # Use direct import with full path
            import get_user_info.embed_info as embed_info_module
            
            # Create partner matches directory if it doesn't exist
            partner_matches_dir = os.path.join(PROJECT_ROOT, "UserInfo_and_Match", "partner_matches")
            os.makedirs(partner_matches_dir, exist_ok=True)
            
            try:
                # Run the matching process
                print("Running partner matching...")
                top_matches = embed_info_module.run_matching(top_k=5, output_dir=partner_matches_dir, silent=True)
                
                if not top_matches:
                    return jsonify({
                        "success": False,
                        "message": "No matches found. Please check the logs for more details."
                    }), 500
                
                # Get match details from user pool
                try:
                    user_pool = embed_info_module.load_user_pool()
                    
                    matches = []
                    for idx, (user_idx, score) in enumerate(top_matches):
                        user_row = user_pool.iloc[user_idx]
                        match_data = {
                            "id": user_idx,
                            "name": user_row.get("real_name", f"User {user_idx+1}"),
                            "nationality": user_row.get("nationality", "Unknown"),
                            "age_group": user_row.get("age_group", "Unknown"),
                            "interests": user_row.get("bucket_list", "Various interests"),
                            "score": round(score * 100, 2)  # Format score as percentage
                        }
                        matches.append(match_data)
                    
                    return jsonify({
                        "success": True,
                        "message": "Embedding calculation and partner matching completed successfully",
                        "matches": matches,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                except Exception as e:
                    error_msg = f"Error processing match details: {str(e)}"
                    print(error_msg)
                    print(traceback.format_exc())
                    return jsonify({
                        "success": False,
                        "message": error_msg
                    }), 500
            
            except Exception as e:
                error_msg = str(e)
                print(f"Error in partner matching: {error_msg}")
                print(traceback.format_exc())
                
                # Check for OpenAI quota errors
                if "quota" in error_msg.lower() or "insufficient_quota" in error_msg:
                    return jsonify({
                        "success": False,
                        "message": "OpenAI API quota exceeded. The embedding service is currently unavailable due to API usage limits. Please try again later or contact the administrator to update the API key.",
                        "error_type": "quota_exceeded"
                    }), 429
                
                return jsonify({
                    "success": False,
                    "message": f"Error in partner matching: {error_msg}"
                }), 500
        
        except Exception as e:
            error_msg = f"Error importing embedding module: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            # Check for OpenAI quota errors
            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg:
                return jsonify({
                    "success": False,
                    "message": "OpenAI API quota exceeded. The embedding service is currently unavailable due to API usage limits. Please try again later or contact the administrator to update the API key.",
                    "error_type": "quota_exceeded"
                }), 429
                
            return jsonify({
                "success": False,
                "message": error_msg
            }), 500
    
    except Exception as e:
        error_msg = f"Unexpected error in embedding calculation: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": error_msg,
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the Flask server."""
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return jsonify({"status": "success", "message": "Server shutting down..."})
    except Exception as e:
        print(f"Error shutting down server: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/generate_blog', methods=['POST'])
def generate_blog():
    """Generate a travel blog using the blog_generator.py module."""
    try:
        # Log the incoming request
        print(f"Received blog generation request at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
        
        # Set up paths properly - multiple ways to ensure blog_generator.py is found
        # 1. First try using PROJECT_ROOT
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
            print(f"Added project root to sys.path: {PROJECT_ROOT}")
        
        # 2. Also try the parent directory of deploy/backend
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            print(f"Added parent directory to sys.path: {parent_dir}")
        
        # 3. Add current working directory as fallback
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
            print(f"Added current working directory to sys.path: {cwd}")
            
        # Try all possible locations for blog_generator.py
        possible_paths = [
            os.path.join(PROJECT_ROOT, "blog_generator.py"),
            os.path.join(parent_dir, "blog_generator.py"),
            os.path.join(cwd, "blog_generator.py"),
            "blog_generator.py" # Relative to current directory
        ]
        
        blog_generator_path = None
        for path in possible_paths:
            if os.path.exists(path):
                blog_generator_path = path
                print(f"Found blog_generator.py at: {blog_generator_path}")
                break
                
        if not blog_generator_path:
            error_msg = f"blog_generator.py not found in any of these locations: {possible_paths}"
            print(error_msg)
            return jsonify({'success': False, 'error': error_msg}), 404
        
        # Try importing with detailed error handling
        try:
            print(f"Python sys.path: {sys.path}")
            print(f"Attempting to import blog_generator from {os.path.dirname(blog_generator_path)}")
            
            # Add the directory containing blog_generator.py to the path
            blog_dir = os.path.dirname(blog_generator_path)
            if blog_dir and blog_dir not in sys.path:
                sys.path.insert(0, blog_dir)
            
            # Try direct import
            from blog_generator import generate_blog_post
            print("Successfully imported generate_blog_post function")
        except ImportError as e:
            error_msg = f"Error importing blog_generator: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            # Try a fallback approach - load the module directly from file
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("blog_generator", blog_generator_path)
                blog_generator = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(blog_generator)
                generate_blog_post = blog_generator.generate_blog_post
                print("Successfully imported generate_blog_post function using importlib")
            except Exception as e2:
                error_msg = f"Failed to import blog_generator.py using alternative methods: {str(e2)}"
                print(error_msg)
                print(traceback.format_exc())
                return jsonify({'success': False, 'error': error_msg}), 500
        
        # Get JSON data from request
        data = request.json
        if not data:
            print("ERROR: No JSON data received for blog generation")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get route information
        route_info = data.get('route_info', {})
        
        # Get partner information if provided
        partner_info = data.get('partner_info')
        
        # Get user information from the latest survey file
        user_info = {}
        try:
            # Make sure survey results directory exists
            if not os.path.exists(survey_results_dir):
                os.makedirs(survey_results_dir, exist_ok=True)
                print(f"Created survey_results_dir: {survey_results_dir}")
            
            # Get most recent user answer file
            files = [f for f in os.listdir(survey_results_dir) if f.startswith("user_answer_") and f.endswith(".csv")]
            
            if files:
                file_path = os.path.join(survey_results_dir, sorted(files)[-1])
                df = pd.read_csv(file_path)
                user_info = df.iloc[0].to_dict()
                print(f"User data loaded from {file_path}")
            else:
                print("No user data files found, using default values")
        except Exception as e:
            print(f"Error loading user data: {str(e)}")
            print(traceback.format_exc())
        
        # If no user info is available, create default values
        if not user_info:
            # Create some default user values
            user_info = {
                'name': 'Anonymous Traveler',
                'age': '25-34',
                'nationality': 'International',
                'interests': 'Travel and exploration'
            }
            # Update with origin/destination from route info if available
            if route_info:
                if 'origin' in route_info:
                    user_info['origin_city'] = route_info['origin']
                if 'destination' in route_info:
                    user_info['destination_city'] = route_info['destination']
        
        # Create blog output directory with proper error handling
        blog_output_dir = os.path.join(PROJECT_ROOT, "wandermatch_output", "blogs")
        try:
            os.makedirs(blog_output_dir, exist_ok=True)
            print(f"Ensured blog output directory exists: {blog_output_dir}")
            
            # Check if directory was actually created
            if not os.path.exists(blog_output_dir):
                error_msg = f"Failed to create blog output directory: {blog_output_dir}"
                print(error_msg)
                return jsonify({'success': False, 'error': error_msg}), 500
                
            # Set directory permissions
            try:
                os.chmod(blog_output_dir, 0o777)
                print(f"Set permissions on blog output directory: {blog_output_dir}")
                
                # Verify permissions with a test file
                test_file = os.path.join(blog_output_dir, "write_test.txt")
                with open(test_file, 'w') as f:
                    f.write("Write test successful")
                os.remove(test_file)
                print(f"Successfully verified write permissions on {blog_output_dir}")
            except Exception as e:
                print(f"Warning: Could not set permissions on blog directory: {str(e)}")
                print(traceback.format_exc())
                # Continue anyway - it might still work
        except Exception as e:
            error_msg = f"Error creating blog output directory: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': error_msg}), 500
        
        # Call the blog generator function with detailed logging
        print("Calling generate_blog_post with:")
        print(f"User info: {json.dumps(user_info, indent=2)}")
        print(f"Partner info: {partner_info}")
        print(f"Route info: {json.dumps(route_info, indent=2)}")
        
        result = generate_blog_post(user_info, partner_info, route_info)
        print(f"Blog generator returned: {json.dumps(result, indent=2)}")
        
        # Return the result
        return jsonify({
            'success': result.get('success', False),
            'md_path': result.get('md_path'),
            'html_path': result.get('html_path'),
            'error': result.get('error')
        })
    
    except Exception as e:
        error_msg = f"Error generating blog: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/favicon.ico', methods=['GET'])
def favicon():
    """
    Route to handle favicon.ico requests from browsers.
    Returns a 204 No Content response instead of a 404.
    """
    return '', 204

@app.route('/api/cors-test', methods=['GET', 'POST', 'OPTIONS'])
def cors_test():
    """
    Simple endpoint to test CORS configuration.
    This endpoint will always return success and includes detailed request information.
    """
    response_data = {
        "success": True,
        "message": "CORS test successful",
        "request": {
            "method": request.method,
            "headers": {k: v for k, v in request.headers.items()},
            "origin": request.headers.get('Origin', 'Unknown'),
            "referrer": request.headers.get('Referer', 'Unknown')
        },
        "server": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": os.environ.get('ENVIRONMENT', 'development'),
            "allowed_origins": os.environ.get('ALLOWED_ORIGINS', 'Not set')
        }
    }
    
    return jsonify(response_data)

@app.route('/api/answer_question', methods=['POST'])
def answer_question():
    """
    API endpoint to answer travel-related questions using LLM providers.
    
    This endpoint attempts to use multiple LLM providers in sequence:
    1. OpenAI GPT-3.5-turbo
    2. Google Gemini 1.5
    3. Fallback approach
    
    Returns:
        JSON with the answer and information about which provider was used
    """
    try:
        # Log the incoming request
        print(f"Received question answering request at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Import the LLM service
        from llm_service import LLMService
        
        # Get JSON data from request
        data = request.json
        if not data:
            print("ERROR: No JSON data received for question answering")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get the question
        question = data.get('question')
        if not question:
            print("ERROR: No question provided")
            return jsonify({'success': False, 'error': 'No question provided'}), 400
        
        # Get context information if provided
        context = data.get('context', {})
        
        # Create LLM service instance
        llm_service = LLMService()
        
        # Get answer
        print(f"Calling LLM service to answer question: {question}")
        result = llm_service.answer_question(question, context)
        
        # Return the result
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'provider': result['provider']
        })
    
    except Exception as e:
        error_msg = f"Error answering question: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Flask server on port {port}")
    print(f"Survey results directory: {survey_results_dir}")
    print(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 