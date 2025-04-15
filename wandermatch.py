#!/usr/bin/env python
"""
WanderMatch: Travel Matchmaking & Route Recommendation Platform

This script integrates all components of WanderMatch:
1. User Profile Creation & Partner Matching (using cached embeddings)
2. Travel Route Generation
3. Blog Post Creation

To run: python wandermatch.py
"""
import os
import sys
import traceback
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import random
import webbrowser
import csv
import re
import time

# Import local modules
from utils import (
    print_header, print_info, print_success, 
    print_error, print_warning, get_env_var
)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Constants
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check required environment variables
required_keys = [
    "PORTIA_API_KEY",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "ORS_API_KEY",
    "GOOGLE_API_KEY"
]

missing_keys = [key for key in required_keys if not get_env_var(key)]
if missing_keys:
    print_error(f"Missing required environment variables: {', '.join(missing_keys)}")
    print_info("Please add these to your .env file at: " + os.path.join(WORKSPACE_DIR, '.env'))
    sys.exit(1)
else:
    print_success("All required environment variables loaded successfully.")

def main():
    """Main function to run the WanderMatch application"""
    clear_screen()
    print_header("WanderMatch", emoji="✈️", color="green")
    print_info("All required environment variables loaded successfully.")
    print_info(" ")
    
    # Get user info
    user_info = get_user_info()
    
    # Display potential travel partners and let user choose
    partner_info = select_travel_partner(user_info)
    
    # Select origin and destination
    origin_city = input_prompt("Enter your origin city: ")
    destination_city = input_prompt("Enter your destination city: ")
    
    # Store these in user_info for later use
    user_info['origin_city'] = origin_city
    user_info['destination_city'] = destination_city
    
    # Select transport mode
    transport_option = select_transport_mode(origin_city, destination_city)
    
    # Generate travel route
    route_info = generate_travel_route(user_info, partner_info, transport_option)
    
    # Generate blog post
    blog_result = generate_blog_post(user_info, partner_info, route_info)
    
    # Create output directories
    output_dir = os.path.join(WORKSPACE_DIR, "wandermatch_output")
    blogs_dir = os.path.join(output_dir, "blogs")
    maps_dir = os.path.join(output_dir, "maps")
    for directory in [output_dir, blogs_dir, maps_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Display summary
    print_header("Your WanderMatch Journey is Ready!", emoji="✨", color="green")
    print_success(f"Origin: {origin_city}")
    print_success(f"Destination: {destination_city}")
    if partner_info:
        print_success(f"Travel Partner: {partner_info.get('name', 'Travel Companion')}")
    else:
        print_success("Travel Mode: Solo")
    print_success(f"Transportation: {transport_option.get('mode', 'Custom')}")
    print_success(f"Blog saved to: {blog_result.get('html_path', 'wandermatch_output/blogs/')}")
    
    print_info("\nThank you for using WanderMatch! Safe travels!")

def select_transport_mode(origin_city, destination_city):
    """
    Let the user select from available transport modes between cities.
    
    Args:
        origin_city: The starting city
        destination_city: The destination city
        
    Returns:
        Dictionary containing the selected transport mode details
    """
    print_header(f"Transportation Options")
    print_info(f"Finding the best ways to travel from {origin_city} to {destination_city}...")
    
    # Create output directory
    output_dir = os.path.join("wandermatch_output", "maps")
    os.makedirs(output_dir, exist_ok=True)
    
    # Try to generate transport options with AI APIs
    transport_options = []
    
    # Check if we can use Gemini API
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            print_info("Using Gemini to generate transport options...")
            transport_options = generate_transport_options_with_gemini(origin_city, destination_city, gemini_api_key)
            if transport_options:
                print_success("Successfully generated transport options with Gemini.")
        except Exception as e:
            print_warning(f"Error using Gemini API: {str(e)}")
    
    # If Gemini failed, try OpenAI
    if not transport_options:
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            try:
                print_info("Using OpenAI to generate transport options...")
                transport_options = generate_transport_options_with_openai(origin_city, destination_city, openai_api_key)
                if transport_options:
                    print_success("Successfully generated transport options with OpenAI.")
            except Exception as e:
                print_warning(f"Error using OpenAI API: {str(e)}")
    
    # If all API-based methods failed, use default options
    if not transport_options:
        print_info("Using default transport options...")
        transport_options = get_transport_options(origin_city, destination_city)
    
    # Generate HTML visualization
    try:
        html_output = generate_transport_html(origin_city, destination_city, transport_options)
        html_path = os.path.join(output_dir, "transport_options.html")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Write the HTML file
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        
        # Try to open the HTML file in a browser
        try:
            webbrowser.open('file://' + os.path.abspath(html_path))
            print_success(f"Transport options visualization opened in your browser")
        except Exception as e:
            print_warning(f"Could not open browser: {str(e)}")
            print_info(f"Transport options HTML saved to: {html_path}")
    except Exception as e:
        print_warning(f"Error generating transport visualization: {str(e)}")
    
    # Display transport options in a visually appealing way
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        
        console = Console()
        
        # Create a table for transport options
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2), expand=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Mode", style="green")
        table.add_column("Duration", style="magenta")
        table.add_column("Cost", style="yellow")
        table.add_column("🌱 Carbon", style="blue")
        table.add_column("⭐ Comfort", style="cyan")
        
        # Add rows for each transport option
        for i, option in enumerate(transport_options, 1):
            # Get values with fallbacks
            mode = option.get("mode", "Unknown")
            duration = option.get("duration", "Unknown")
            cost = option.get("cost", "Unknown")
            carbon = option.get("carbon_footprint", "Unknown")
            
            # Convert comfort rating to stars
            comfort_rating = option.get("comfort_rating", 5)
            if isinstance(comfort_rating, str) and comfort_rating.isdigit():
                comfort_rating = int(comfort_rating)
            elif not isinstance(comfort_rating, (int, float)):
                comfort_rating = 5
                
            # Limit comfort rating to 1-10 range
            comfort_rating = max(1, min(10, comfort_rating))
            comfort_stars = "★" * (comfort_rating // 2) + "☆" * ((10 - comfort_rating) // 2)
            
            # Add row to table
            table.add_row(
                str(i),
                mode,
                duration,
                cost,
                carbon,
                comfort_stars
            )
        
        # Print the table
        console.print("\n")
        console.print(Panel(table, title="[bold]Travel Options[/bold]", expand=False, border_style="green"))
        console.print("\n")
        
    except ImportError:
        # Fallback to simple output if rich is not available
        print_info("\nAvailable transport options:")
        for i, option in enumerate(transport_options, 1):
            print(f"{i}. {option.get('mode', 'Unknown')}: {option.get('duration', 'Unknown')} - {option.get('cost', 'Unknown')}")
    
    # Let user choose a transport option
    while True:
        try:
            choice = input_prompt(f"Select a transport option (1-{len(transport_options)}): ")
            idx = int(choice) - 1
            if 0 <= idx < len(transport_options):
                selected = transport_options[idx]
                print_success(f"You selected: {selected.get('mode', 'Unknown Transport')}")
                
                # Print details about the selected option
                print_info("\nDetails about your selected transport mode:")
                print(f"Duration: {selected.get('duration', 'Unknown')}")
                print(f"Cost: {selected.get('cost', 'Unknown')}")
                print(f"Distance: {selected.get('distance', 'Unknown')}")
                print(f"Carbon footprint: {selected.get('carbon_footprint', 'Unknown')}")
                
                # Print pros if available
                if 'pros' in selected and selected['pros']:
                    print_info("\nAdvantages:")
                    for pro in selected['pros'][:5]:  # Show up to 5 pros
                        print(f"✓ {pro}")
                
                return selected
            else:
                print_warning(f"Please enter a number between 1 and {len(transport_options)}")
        except ValueError:
            print_warning("Please enter a valid number")

def generate_transport_options_with_gemini(origin_city, destination_city, api_key):
    """Generate transport options using Google Gemini API"""
    import google.generativeai as genai
    import json
    
    print_info("Generating comprehensive transport options with Gemini...")
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Set up the model
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config
    )
    
    prompt = f"""
    Generate detailed and accurate transportation options for a journey from {origin_city} to {destination_city}.
    
    I need exactly 7 different transportation modes that are feasible for this journey (if possible). 
    Consider options such as:
    - Flights (direct and indirect)
    - Train (high-speed, regional, sleeper)
    - Bus (express, regular)
    - Car (rental, private, rideshare)
    - Ferry (if applicable)
    - Combination routes (e.g., train + bus)
    - Specialized options (e.g., scenic routes, luxury services)
    
    For each transportation mode, provide:
    1. Estimated travel time (with range if variable)
    2. Estimated cost range (in USD or local currency)
    3. Distance in kilometers/miles
    4. Environmental impact rating (Low/Medium/High) with carbon estimate if possible
    5. At least 3 detailed pros
    6. At least 3 detailed cons
    7. Weather considerations
    8. Comfort rating (1-10)
    9. Reliability rating (1-10)
    10. Any unique features
    
    Provide the information in this exact JSON format:
    ```json
    {{
      "options": [
        {{
          "mode": "transportation_mode",
          "duration": "estimated_time",
          "cost": "cost_range",
          "distance": "distance",
          "carbon_footprint": "environmental_impact",
          "weather_impact": "weather_considerations",
          "comfort_rating": 8,
          "reliability_rating": 9,
          "unique_features": "any_special_features",
          "pros": ["pro1", "pro2", "pro3", "pro4", "pro5"],
          "cons": ["con1", "con2", "con3", "con4", "con5"]
        }}
      ]
    }}
    ```
    
    Make sure the JSON is properly formatted with no errors. All transportation modes must be realistic and feasible for this journey.
    """
    
    try:
        # Generate content
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON part
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        # Try to fix common JSON formatting issues
        response_text = response_text.replace("'", "\"")
        
        # Try to parse JSON directly
        try:
            transport_data = json.loads(response_text)
        except json.JSONDecodeError:
            # If parsing fails, attempt additional cleaning
            import re
            
            # Fix trailing commas in arrays and objects
            response_text = re.sub(r',\s*]', ']', response_text)
            response_text = re.sub(r',\s*}', '}', response_text)
            
            # Fix missing quotes around property names
            response_text = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', response_text)
            
            # Ensure numeric values don't have quotes
            response_text = re.sub(r'"(\d+)"', r'\1', response_text)
            
            # Try parsing again after fixes
            transport_data = json.loads(response_text)
        
        return transport_data.get("options", [])
    except Exception as e:
        print_warning(f"Error in Gemini transport options generation: {str(e)}")
        # Return empty list to trigger fallback
        return []

def generate_transport_options_with_openai(origin_city, destination_city, api_key):
    """Generate transport options using OpenAI API"""
    from openai import OpenAI
    
    print_info("Generating comprehensive transport options with OpenAI...")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Create prompt for transport options
    prompt = f"""
    Generate detailed and accurate transportation options for a journey from {origin_city} to {destination_city}.
    
    I need exactly 7 different transportation modes that are feasible for this journey (if possible). 
    Consider options such as:
    - Flights (direct and indirect)
    - Train (high-speed, regional, sleeper)
    - Bus (express, regular)
    - Car (rental, private, rideshare)
    - Ferry (if applicable)
    - Combination routes (e.g., train + bus)
    - Specialized options (e.g., scenic routes, luxury services)
    
    For each transportation mode, provide:
    1. Estimated travel time (with range if variable)
    2. Estimated cost range (in USD or local currency)
    3. Distance in kilometers/miles
    4. Environmental impact rating (Low/Medium/High) with carbon estimate if possible
    5. At least 5 detailed pros
    6. At least 5 detailed cons
    7. Weather considerations
    8. Comfort rating (1-10)
    9. Reliability rating (1-10)
    10. Unique features or considerations
    
    Your response must be in JSON format with this structure:
    {{
        "options": [
            {{
                "mode": "Detailed name of transportation mode",
                "duration": "Estimated travel time with range",
                "distance": "Estimated distance with units",
                "cost": "Estimated cost range",
                "carbon_footprint": "Environmental impact rating",
                "carbon_estimate": "Estimated CO2 emissions",
                "weather_impact": "How weather might affect this transport mode",
                "comfort_rating": 7,
                "reliability_rating": 8,
                "unique_features": "Any unique aspects of this transportation mode",
                "pros": [
                    "Detailed pro 1",
                    "Detailed pro 2",
                    "Detailed pro 3",
                    "Detailed pro 4",
                    "Detailed pro 5"
                ],
                "cons": [
                    "Detailed con 1", 
                    "Detailed con 2",
                    "Detailed con 3",
                    "Detailed con 4",
                    "Detailed con 5"
                ]
            }},
            ... 6 more transportation options ...
        ]
    }}
    
    Be realistic about what options are actually feasible for this specific journey.
    Provide accurate time and cost estimates based on current transportation information.
    If exactly 7 modes aren't feasible, provide as many realistic options as possible.
    Make sure each transportation mode is distinct enough to offer real choice.
    """
    
    try:
        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a travel logistics expert providing accurate, detailed transportation information in JSON format."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse JSON response
        import json
        transport_data = json.loads(response.choices[0].message.content)
        
        return transport_data.get("options", [])
    except Exception as e:
        print_warning(f"Error in OpenAI transport options generation: {str(e)}")
        # Return empty list to trigger fallback
        return []

def generate_transport_html(origin_city, destination_city, transport_options):
    """Generate an HTML file with transport options"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transport Options: {origin_city} to {destination_city}</title>
        <style>
            :root {{
                --primary-color: #3498db;
                --secondary-color: #2ecc71;
                --accent-color: #f39c12;
                --warning-color: #e74c3c;
                --text-color: #333;
                --light-bg: #f9f9f9;
                --card-shadow: 0 4px 8px rgba(0,0,0,0.1);
                --border-radius: 8px;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            
            body {{
                background-color: #f5f5f5;
                color: var(--text-color);
                padding: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            
            header {{
                background: linear-gradient(135deg, var(--primary-color), #1a6ca4);
                color: white;
                padding: 25px;
                border-radius: var(--border-radius);
                margin-bottom: 30px;
                text-align: center;
                box-shadow: var(--card-shadow);
            }}
            
            h1 {{
                margin-bottom: 10px;
                font-size: 2.2rem;
            }}
            
            .journey-details {{
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            
            .transport-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 25px;
                margin-bottom: 30px;
            }}
            
            .transport-card {{
                background: white;
                border-radius: var(--border-radius);
                padding: 20px;
                box-shadow: var(--card-shadow);
                transition: transform 0.3s, box-shadow 0.3s;
                position: relative;
                overflow: hidden;
            }}
            
            .transport-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }}
            
            .card-header {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
                border-bottom: 1px solid #eee;
                padding-bottom: 15px;
            }}
            
            .transport-icon {{
                font-size: 2rem;
                margin-right: 15px;
                color: var(--primary-color);
            }}
            
            .transport-name {{
                font-size: 1.5rem;
                font-weight: bold;
            }}
            
            .detail-row {{
                display: flex;
                margin-bottom: 10px;
                align-items: center;
            }}
            
            .detail-label {{
                min-width: 120px;
                font-weight: 600;
                color: #666;
            }}
            
            .detail-value {{
                flex: 1;
            }}
            
            .badge {{
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.85rem;
                font-weight: 600;
                color: white;
                display: inline-block;
            }}
            
            .impact-low {{
                background-color: var(--secondary-color);
            }}
            
            .impact-medium {{
                background-color: var(--accent-color);
            }}
            
            .impact-high {{
                background-color: var(--warning-color);
            }}
            
            .rating {{
                display: inline-block;
                background-color: var(--light-bg);
                border-radius: 12px;
                padding: 3px 10px;
                font-weight: 600;
            }}
            
            .rating-good {{
                color: var(--secondary-color);
            }}
            
            .rating-medium {{
                color: var(--accent-color);
            }}
            
            .rating-poor {{
                color: var(--warning-color);
            }}
            
            .lists-container {{
                display: flex;
                margin-top: 15px;
                gap: 15px;
            }}
            
            .pros-list, .cons-list {{
                flex: 1;
                padding: 15px;
                border-radius: var(--border-radius);
            }}
            
            .pros-list {{
                background-color: rgba(46, 204, 113, 0.1);
                border-left: 4px solid var(--secondary-color);
            }}
            
            .cons-list {{
                background-color: rgba(231, 76, 60, 0.1);
                border-left: 4px solid var(--warning-color);
            }}
            
            h3 {{
                margin-bottom: 10px;
                font-size: 1.1rem;
            }}
            
            ul {{
                margin-left: 20px;
            }}
            
            li {{
                margin-bottom: 5px;
            }}
            
            footer {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                color: #666;
                font-size: 0.9rem;
            }}
            
            .unique-features {{
                margin-top: 15px;
                padding: 10px;
                background-color: #f0f8ff;
                border-radius: var(--border-radius);
                font-style: italic;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Transport Options</h1>
                <div class="journey-details">From <strong>{origin_city}</strong> to <strong>{destination_city}</strong></div>
            </header>
            
            <div class="transport-grid">
    """
    
    # Add cards for each transport option
    for option in transport_options:
        # Get transport mode icon
        icon = get_transport_icon(option.get('mode', 'Other').lower())
        
        # Determine carbon impact class
        carbon_impact = option.get('carbon_footprint', '').lower()
        if 'low' in carbon_impact:
            impact_class = 'impact-low'
        elif 'medium' in carbon_impact:
            impact_class = 'impact-medium'
        elif 'high' in carbon_impact:
            impact_class = 'impact-high'
        else:
            impact_class = 'impact-medium'
        
        # Determine comfort rating class
        comfort_rating = option.get('comfort_rating', 5)
        if isinstance(comfort_rating, str):
            try:
                comfort_rating = int(comfort_rating.split('/')[0])
            except:
                comfort_rating = 5
        
        if comfort_rating >= 7:
            comfort_class = 'rating-good'
        elif comfort_rating >= 5:
            comfort_class = 'rating-medium'
        else:
            comfort_class = 'rating-poor'
        
        # Determine reliability rating class
        reliability_rating = option.get('reliability_rating', 5)
        if isinstance(reliability_rating, str):
            try:
                reliability_rating = int(reliability_rating.split('/')[0])
            except:
                reliability_rating = 5
        
        if reliability_rating >= 7:
            reliability_class = 'rating-good'
        elif reliability_rating >= 5:
            reliability_class = 'rating-medium'
        else:
            reliability_class = 'rating-poor'
        
        # Get pros and cons
        pros = option.get('pros', [])
        cons = option.get('cons', [])
        
        # Create card HTML
        html += f"""
            <div class="transport-card">
                <div class="card-header">
                    <div class="transport-icon">{icon}</div>
                    <div class="transport-name">{option.get('mode', 'Transport Option')}</div>
                </div>
                
                <div class="detail-row">
                    <div class="detail-label">Duration:</div>
                    <div class="detail-value">{option.get('duration', 'Unknown')}</div>
                </div>
                
                <div class="detail-row">
                    <div class="detail-label">Cost:</div>
                    <div class="detail-value">{option.get('cost', 'Varies')}</div>
                </div>
                
                <div class="detail-row">
                    <div class="detail-label">Distance:</div>
                    <div class="detail-value">{option.get('distance', 'Unknown')}</div>
                </div>
                
                <div class="detail-row">
                    <div class="detail-label">Carbon Footprint:</div>
                    <div class="detail-value">
                        <span class="badge {impact_class}">{option.get('carbon_footprint', 'Medium')}</span>
                    </div>
                </div>
                
                <div class="detail-row">
                    <div class="detail-label">Comfort:</div>
                    <div class="detail-value">
                        <span class="rating {comfort_class}">{option.get('comfort_rating', '5')}/10</span>
                    </div>
                </div>
                
                <div class="detail-row">
                    <div class="detail-label">Reliability:</div>
                    <div class="detail-value">
                        <span class="rating {reliability_class}">{option.get('reliability_rating', '5')}/10</span>
                    </div>
                </div>
                
                <div class="lists-container">
                    <div class="pros-list">
                        <h3>Pros</h3>
                        <ul>
        """
        
        # Add pros
        for pro in pros:
            html += f"<li>{pro}</li>"
        
        if not pros:
            html += "<li>Information not available</li>"
        
        html += """
                        </ul>
                    </div>
                    <div class="cons-list">
                        <h3>Cons</h3>
                        <ul>
        """
        
        # Add cons
        for con in cons:
            html += f"<li>{con}</li>"
        
        if not cons:
            html += "<li>Information not available</li>"
        
        html += """
                        </ul>
                    </div>
                </div>
        """
        
        # Add unique features if available
        if option.get('unique_features'):
            html += f"""
                <div class="unique-features">
                    <strong>Unique Features:</strong> {option.get('unique_features')}
                </div>
            """
        
        html += """
            </div>
        """
    
    # Complete the HTML
    html += """
            </div>
            <footer>
                <p>Generated by WanderMatch &copy; 2023 | Transport options are estimates and subject to change</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_travel_route(user_info, partner_info, transport_option):
    """Generate a travel route using Gemini or OpenAI API"""
    print_header("Travel Route Generation")
    
    # Get time period from user
    print_info("How many days would you like to travel?")
    
    try:
        trip_days = int(input_prompt("Enter number of days (1-30): "))
        if trip_days < 1 or trip_days > 30:
            print_warning("Invalid number of days. Setting to default of 7 days.")
            trip_days = 7
    except ValueError:
        print_warning("Invalid input. Setting to default of 7 days.")
        trip_days = 7
    
    # Set default start and end dates automatically without asking the user
    start_date = datetime.now() + timedelta(days=10)  # Default start in 10 days
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date = start_date + timedelta(days=trip_days)
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    try:
        # Extract origin and destination from user info and transport option
        origin_city = user_info.get('origin_city', transport_option.get('origin', 'London'))
        destination_city = user_info.get('destination_city', transport_option.get('destination', 'Paris'))
        
        # Generate route information using Gemini API if available
        try:
            # Try with Gemini first
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if gemini_api_key:
                import google.generativeai as genai
                import json
                import re
                
                # Configure Gemini API
                genai.configure(api_key=gemini_api_key)
                
                # Set up the model with appropriate parameters
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 8192,
                }
                
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",
                    generation_config=generation_config
                )
                
                # Create a detailed travel prompt
                travel_prompt = f"""
                Generate a detailed travel itinerary for a {trip_days}-day trip from {origin_city} to {destination_city}.
                The trip starts on {start_date_str} and ends on {end_date_str}.
                
                The traveler is {user_info.get('name', 'A traveler')} who likes {user_info.get('interests', ['exploring', 'food', 'culture'])}.
                
                {f"They'll be traveling with {partner_info.get('name', 'a partner')} who likes {', '.join(partner_info.get('interests', ['sightseeing', 'relaxing']))}." if partner_info else "They'll be traveling solo."}
                
                The chosen transportation mode is {transport_option.get('mode', 'Unknown')} which takes {transport_option.get('duration', 'some time')} and costs approximately {transport_option.get('cost', 'Unknown')}.
                
                Please structure the response as a JSON object with the following format:
                
                {{
                  "trip_summary": {{
                    "origin": "{origin_city}",
                    "destination": "{destination_city}",
                    "duration": {trip_days},
                    "transportation": "{transport_option.get('mode', 'Unknown')}",
                    "start_date": "{start_date_str}",
                    "end_date": "{end_date_str}"
                  }},
                  "daily_plan": [
                    {{
                      "day": 1,
                      "date": "{start_date_str}",
                      "activities": [
                        {{
                          "time": "Morning",
                          "description": "detailed activity",
                          "location": "specific place",
                          "cost": "estimated cost"
                        }},
                        {{
                          "time": "Afternoon",
                          "description": "detailed activity",
                          "location": "specific place",
                          "cost": "estimated cost"
                        }},
                        {{
                          "time": "Evening",
                          "description": "detailed activity",
                          "location": "specific place",
                          "cost": "estimated cost"
                        }}
                      ],
                      "accommodation": {{
                        "name": "Hotel/Accommodation name",
                        "type": "type of accommodation",
                        "cost": "estimated cost"
                      }}
                    }}
                  ],
                  "budget_breakdown": {{
                    "accommodation": "total accommodation cost",
                    "transportation": "total transportation cost",
                    "activities": "total activities cost",
                    "food": "estimated food cost",
                    "misc": "miscellaneous costs",
                    "total": "total trip cost"
                  }},
                  "packing_recommendations": [
                    "item 1",
                    "item 2"
                  ],
                  "tips": [
                    "tip 1",
                    "tip 2"
                  ]
                }}
                
                Make the itinerary realistic, with accurate timing and appropriate activities for each day.
                Suggest actual attractions, restaurants, and accommodations that exist in {destination_city}.
                Consider the travelers' preferences and budget in all recommendations.
                
                The response MUST be a VALID JSON object that can be parsed with json.loads().
                DO NOT include any explanations, comments, or text outside the JSON structure.
                DO NOT use placeholders like "// Repeat for each day" in the response.
                """
                
                # Get response from Gemini
                response = model.generate_content(travel_prompt)
                response_text = response.text
                
                # Extract JSON if it's embedded in code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                # Clean the response text
                response_text = response_text.strip()
                
                # Replace comments (like // Repeat for each day) with empty string
                response_text = re.sub(r'//.*\n', '\n', response_text)
                
                # Fix trailing commas
                response_text = re.sub(r',(\s*[\]}])', r'\1', response_text)
                
                # Fix malformed JSON - common errors from LLM responses
                # Replace single quotes with double quotes
                response_text = response_text.replace("'", '"')
                
                # Fix unquoted property names
                response_text = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', response_text)
                
                # Fix missing commas between elements
                response_text = re.sub(r'(["}\]])\s*(["{\[])', r'\1,\2', response_text)
                
                # Try to parse the JSON
                try:
                    route_data = json.loads(response_text)
                    print_success("Successfully generated travel route with Gemini.")
                    return route_data
                except json.JSONDecodeError as e:
                    print_warning(f"Error parsing JSON response: {str(e)}")
                    
                    # More aggressive JSON repair attempt
                    try:
                        # Try to find and extract just the most complete JSON object
                        import re
                        json_pattern = re.compile(r'{.*}', re.DOTALL)
                        match = json_pattern.search(response_text)
                        if match:
                            potential_json = match.group(0)
                            # Try parsing the extracted JSON
                            route_data = json.loads(potential_json)
                            print_success("Successfully extracted and parsed partial JSON.")
                            return route_data
                    except:
                        # If all attempts fail, use fallback
                        print_warning("JSON repair failed. Falling back to alternative method.")
                        
                    route_info = fallback_route_generation(user_info, partner_info, transport_option, 
                                                        origin_city, destination_city, trip_days, 
                                                        start_date_str, end_date_str)
                    return route_info
            else:
                # Fallback to simple route generation if no Gemini API key
                print_info("No Gemini API key found. Using fallback route generation.")
                route_info = fallback_route_generation(user_info, partner_info, transport_option, 
                                                       origin_city, destination_city, trip_days, 
                                                       start_date_str, end_date_str)
                return route_info
                
        except Exception as e:
            print_error(f"Error generating travel route: {str(e)}")
            # Fallback to simple route generation
            route_info = fallback_route_generation(user_info, partner_info, transport_option, 
                                                   origin_city, destination_city, trip_days, 
                                                   start_date_str, end_date_str)
            return route_info
            
    except Exception as e:
        print_error(f"Error generating travel route: {str(e)}")
        return fallback_route_generation(user_info, partner_info, transport_option, 
                                       origin_city, destination_city, trip_days, 
                                       start_date_str, end_date_str)

def fallback_route_generation(user_info, partner_info, transport_option, 
                             origin_city, destination_city, trip_days, 
                             start_date_str, end_date_str):
    """Generate a basic travel route as a fallback when API methods fail"""
    print_info("Generating a basic travel route...")
    
    # Safely convert transport cost to integer
    def extract_cost(cost_string):
        if not cost_string:
            return 500
        
        # Remove currency symbol and commas
        cost_string = str(cost_string).replace('$', '').replace('€', '').replace('£', '').replace(',', '')
        
        # Extract just the numeric part
        import re
        numeric_match = re.search(r'\d+', cost_string)
        if numeric_match:
            try:
                return int(numeric_match.group())
            except ValueError:
                return 500
        return 500  # Default value
    
    # Extract transport cost
    transport_cost = extract_cost(transport_option.get("cost", "$500"))
    
    # Create route structure
    route_info = {
        "trip_summary": {
            "origin": origin_city,
            "destination": destination_city,
            "duration": trip_days,
            "transportation": transport_option.get("mode", "Custom"),
            "start_date": start_date_str,
            "end_date": end_date_str
        },
        "daily_plan": [],
        "budget_breakdown": {
            "accommodation": f"${trip_days * 100}",
            "transportation": f"${transport_cost}",
            "activities": f"${trip_days * 50}",
            "food": f"${trip_days * 60}",
            "misc": f"${trip_days * 20}",
            "total": f"${trip_days * 230 + transport_cost}"
        },
        "packing_recommendations": [
            "Weather-appropriate clothing",
            "Comfortable walking shoes",
            "Travel adapter",
            "Camera",
            "Travel documents",
            "Medications"
        ],
        "tips": [
            f"Check the weather forecast for {destination_city} before packing",
            "Exchange some currency before departure",
            "Learn a few basic phrases in the local language",
            "Make copies of important documents"
        ]
    }
    
    # Create a start date object for incrementing
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        start_date = datetime.now()
    
    # Generate activities based on destination
    # Dictionary of common tourist activities by city
    city_activities = {
        "Paris": [
            {"time": "Morning", "description": "Visit the Eiffel Tower", "location": "Eiffel Tower", "cost": "$25"},
            {"time": "Morning", "description": "Explore the Louvre Museum", "location": "Louvre Museum", "cost": "$20"},
            {"time": "Morning", "description": "Walk along the Seine River", "location": "Seine River", "cost": "$0"},
            {"time": "Afternoon", "description": "Visit Notre Dame Cathedral", "location": "Notre Dame", "cost": "$0"},
            {"time": "Afternoon", "description": "Explore Montmartre", "location": "Montmartre", "cost": "$0"},
            {"time": "Afternoon", "description": "Visit the Orsay Museum", "location": "Orsay Museum", "cost": "$15"},
            {"time": "Evening", "description": "Enjoy dinner at a café", "location": "Le Marais", "cost": "$40"},
            {"time": "Evening", "description": "Take a Seine River cruise", "location": "Seine River", "cost": "$30"},
            {"time": "Evening", "description": "Experience Parisian nightlife", "location": "Bastille", "cost": "$50"}
        ],
        "London": [
            {"time": "Morning", "description": "Visit the Tower of London", "location": "Tower of London", "cost": "$30"},
            {"time": "Morning", "description": "Explore the British Museum", "location": "British Museum", "cost": "$0"},
            {"time": "Morning", "description": "See the Changing of the Guard", "location": "Buckingham Palace", "cost": "$0"},
            {"time": "Afternoon", "description": "Visit Westminster Abbey", "location": "Westminster", "cost": "$25"},
            {"time": "Afternoon", "description": "Explore Camden Market", "location": "Camden", "cost": "$0"},
            {"time": "Afternoon", "description": "See the views from the London Eye", "location": "London Eye", "cost": "$35"},
            {"time": "Evening", "description": "Enjoy a West End show", "location": "West End", "cost": "$80"},
            {"time": "Evening", "description": "Experience a traditional pub", "location": "Soho", "cost": "$30"},
            {"time": "Evening", "description": "Take a Jack the Ripper tour", "location": "East End", "cost": "$20"}
        ],
        "New York": [
            {"time": "Morning", "description": "Visit the Statue of Liberty", "location": "Liberty Island", "cost": "$25"},
            {"time": "Morning", "description": "Explore Central Park", "location": "Central Park", "cost": "$0"},
            {"time": "Morning", "description": "Visit the Metropolitan Museum", "location": "The Met", "cost": "$25"},
            {"time": "Afternoon", "description": "Explore Times Square", "location": "Times Square", "cost": "$0"},
            {"time": "Afternoon", "description": "Shop on Fifth Avenue", "location": "Fifth Avenue", "cost": "varies"},
            {"time": "Afternoon", "description": "Visit the Empire State Building", "location": "Empire State Building", "cost": "$45"},
            {"time": "Evening", "description": "See a Broadway show", "location": "Broadway", "cost": "$100"},
            {"time": "Evening", "description": "Enjoy dinner in Little Italy", "location": "Little Italy", "cost": "$50"},
            {"time": "Evening", "description": "Experience NYC nightlife", "location": "Lower East Side", "cost": "$60"}
        ]
    }
    
    # Accommodations by city
    city_accommodations = {
        "Paris": [
            {"name": "Hotel de Seine", "type": "Boutique Hotel", "cost": "$150"},
            {"name": "Le Marais Apartment", "type": "Apartment", "cost": "$180"},
            {"name": "Saint Germain B&B", "type": "Bed & Breakfast", "cost": "$120"}
        ],
        "London": [
            {"name": "The Savoy", "type": "Luxury Hotel", "cost": "$300"},
            {"name": "Covent Garden Inn", "type": "Boutique Hotel", "cost": "$180"},
            {"name": "Camden Apartment", "type": "Apartment", "cost": "$150"}
        ],
        "New York": [
            {"name": "The Plaza", "type": "Luxury Hotel", "cost": "$400"},
            {"name": "Greenwich Village Inn", "type": "Boutique Hotel", "cost": "$220"},
            {"name": "Manhattan Apartment", "type": "Apartment", "cost": "$200"}
        ]
    }
    
    # Get activities for destination, or use generic activities
    destination_activities = city_activities.get(destination_city, [
        {"time": "Morning", "description": "Explore local attractions", "location": "City center", "cost": "$20"},
        {"time": "Morning", "description": "Visit a local museum", "location": "Museum district", "cost": "$15"},
        {"time": "Morning", "description": "Take a walking tour", "location": "Historic district", "cost": "$10"},
        {"time": "Afternoon", "description": "Visit local landmarks", "location": "Various locations", "cost": "$0"},
        {"time": "Afternoon", "description": "Shop at local markets", "location": "Market district", "cost": "varies"},
        {"time": "Afternoon", "description": "Explore nature areas", "location": "City park", "cost": "$0"},
        {"time": "Evening", "description": "Enjoy local cuisine", "location": "Restaurant district", "cost": "$40"},
        {"time": "Evening", "description": "Experience local entertainment", "location": "Entertainment district", "cost": "$30"},
        {"time": "Evening", "description": "Relax at a local venue", "location": "City center", "cost": "$20"}
    ])
    
    # Get accommodations for destination, or use generic ones
    destination_accommodations = city_accommodations.get(destination_city, [
        {"name": "City Center Hotel", "type": "Hotel", "cost": "$150"},
        {"name": "Traveler's Apartment", "type": "Apartment", "cost": "$120"},
        {"name": "Budget Inn", "type": "Hostel", "cost": "$80"}
    ])
    
    # Select an accommodation
    selected_accommodation = random.choice(destination_accommodations)
    
    # Generate an itinerary for each day
    for day in range(1, trip_days + 1):
        # Calculate date for this day
        current_date = start_date + timedelta(days=day-1)
        current_date_str = current_date.strftime("%Y-%m-%d")
        
        # Select random activities for each time period, without repeats across days
        available_morning = [a for a in destination_activities if a["time"] == "Morning" and 
                             not any(d.get("day") == day-i and any(act["description"] == a["description"] for act in d.get("activities", [])) 
                                    for i in range(1, min(day, 3)) for d in route_info["daily_plan"])]
        
        available_afternoon = [a for a in destination_activities if a["time"] == "Afternoon" and 
                               not any(d.get("day") == day-i and any(act["description"] == a["description"] for act in d.get("activities", [])) 
                                      for i in range(1, min(day, 3)) for d in route_info["daily_plan"])]
        
        available_evening = [a for a in destination_activities if a["time"] == "Evening" and 
                             not any(d.get("day") == day-i and any(act["description"] == a["description"] for act in d.get("activities", [])) 
                                    for i in range(1, min(day, 3)) for d in route_info["daily_plan"])]
        
        # If we've run out of unique activities, reset the availability
        if not available_morning:
            available_morning = [a for a in destination_activities if a["time"] == "Morning"]
        if not available_afternoon:
            available_afternoon = [a for a in destination_activities if a["time"] == "Afternoon"]
        if not available_evening:
            available_evening = [a for a in destination_activities if a["time"] == "Evening"]
        
        # Select activities for the day
        morning_activity = random.choice(available_morning) if available_morning else {"time": "Morning", "description": "Free time to explore", "location": "Various", "cost": "$0"}
        afternoon_activity = random.choice(available_afternoon) if available_afternoon else {"time": "Afternoon", "description": "Leisure time", "location": "Various", "cost": "$0"}
        evening_activity = random.choice(available_evening) if available_evening else {"time": "Evening", "description": "Dinner at local restaurant", "location": "Restaurant district", "cost": "$30"}
        
        # Adjust first and last day activities
        if day == 1:
            # First day often involves arrival
            morning_activity = {"time": "Morning", "description": f"Arrive in {destination_city} via {transport_option.get('mode', 'transportation')}", "location": f"{destination_city} arrival point", "cost": "$0"}
        elif day == trip_days:
            # Last day often involves departure
            evening_activity = {"time": "Evening", "description": f"Depart from {destination_city} to {origin_city}", "location": f"{destination_city} departure point", "cost": "$0"}
        
        # Create day plan
        day_plan = {
            "day": day,
            "date": current_date_str,
            "activities": [morning_activity, afternoon_activity, evening_activity],
            "accommodation": selected_accommodation
        }
        
        # Add to itinerary
        route_info["daily_plan"].append(day_plan)
    
    print_success("Basic travel route generated successfully.")
    return route_info

def generate_route_map(origin_city, destination_city, transport_option, route_info, maps_dir):
    """
    Generate an HTML file with a map showing the route using Leaflet and OpenStreetMap
    instead of Google Maps (no API key required)
    """
    os.makedirs(maps_dir, exist_ok=True)
    map_file = os.path.join(maps_dir, "route_map.html")
    
    # Get coordinates
    origin_coords = get_city_coordinates(origin_city)
    destination_coords = get_city_coordinates(destination_city)
    
    # Default coordinates if unable to find specific city
    if not origin_coords:
        origin_coords = (51.5074, -0.1278)  # London
        print_warning(f"Could not find coordinates for {origin_city}, using default.")
    
    if not destination_coords:
        destination_coords = (48.8566, 2.3522)  # Paris
        print_warning(f"Could not find coordinates for {destination_city}, using default.")
        
    # Get waypoints from route info
    waypoints = []
    if route_info and "daily_activities" in route_info:
        for day_info in route_info["daily_activities"]:
            if "locations" in day_info:
                for location in day_info["locations"]:
                    if isinstance(location, dict) and "coordinates" in location:
                        waypoints.append(location["coordinates"])
                    elif isinstance(location, str):
                        # Try to get coordinates for location name
                        coords = get_city_coordinates(location)
                        if coords:
                            waypoints.append(coords)
    
    # Create HTML content with Leaflet map
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WanderMatch Route: {origin_city} to {destination_city}</title>
        
        <!-- Leaflet CSS -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
        crossorigin=""/>
        
        <!-- Leaflet JavaScript -->
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
        crossorigin=""></script>
        
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            
            body {{
                background-color: #f5f7fa;
                color: #333;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            
            header {{
                text-align: center;
                margin-bottom: 20px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }}
            
            h1 {{
                color: #2980b9;
                margin-bottom: 10px;
            }}
            
            .journey-details {{
                font-size: 1.2rem;
                color: #555;
            }}
            
            .transport-info {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                border-left: 4px solid #3498db;
            }}
            
            #map {{
                height: 600px;
                width: 100%;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }}
            
            .legend {{
                margin-top: 20px;
                padding: 15px;
                background-color: #f4f6f8;
                border-radius: 8px;
            }}
            
            .legend-item {{
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }}
            
            .legend-color {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 10px;
            }}
            
            .origin-color {{
                background-color: #e74c3c;
            }}
            
            .destination-color {{
                background-color: #2ecc71;
            }}
            
            .waypoint-color {{
                background-color: #f39c12;
            }}
            
            footer {{
                text-align: center;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #7f8c8d;
                font-size: 0.9rem;
            }}
            
            .highlight {{
                font-weight: bold;
                color: #2980b9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>WanderMatch Route Map</h1>
                <div class="journey-details">
                    From <span class="highlight">{origin_city}</span> to 
                    <span class="highlight">{destination_city}</span>
                </div>
            </header>
            
            <div class="transport-info">
                <strong>Transport Mode:</strong> {transport_option.get('mode', 'Not specified')}<br>
                <strong>Duration:</strong> {transport_option.get('duration', 'Not specified')}<br>
                <strong>Distance:</strong> {transport_option.get('distance', 'Not specified')}
            </div>
            
            <div id="map"></div>
            
            <div class="legend">
                <h3>Map Legend</h3>
                <div class="legend-item">
                    <div class="legend-color origin-color"></div>
                    <div>Origin: {origin_city}</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color destination-color"></div>
                    <div>Destination: {destination_city}</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color waypoint-color"></div>
                    <div>Waypoints & Activities</div>
                </div>
            </div>
            
            <footer>
                <p>Generated by WanderMatch &copy; 2023 | Map data &copy; OpenStreetMap contributors</p>
            </footer>
        </div>
        
        <script>
            // Initialize the map
            const map = L.map('map').setView([
                {(origin_coords[0] + destination_coords[0]) / 2}, 
                {(origin_coords[1] + destination_coords[1]) / 2}
            ], 6);
            
            // Add OpenStreetMap tile layer
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
            
            // Define icon options
            const originIcon = L.divIcon({{
                className: 'custom-div-icon',
                html: '<div style="background-color:#e74c3c;width:20px;height:20px;border-radius:50%;"></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            }});
            
            const destinationIcon = L.divIcon({{
                className: 'custom-div-icon',
                html: '<div style="background-color:#2ecc71;width:20px;height:20px;border-radius:50%;"></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            }});
            
            const waypointIcon = L.divIcon({{
                className: 'custom-div-icon',
                html: '<div style="background-color:#f39c12;width:15px;height:15px;border-radius:50%;"></div>',
                iconSize: [15, 15],
                iconAnchor: [7.5, 7.5]
            }});
            
            // Add markers
            L.marker([{origin_coords[0]}, {origin_coords[1]}], {{icon: originIcon}})
                .bindPopup('<strong>{origin_city}</strong><br>Starting point')
                .addTo(map);
                
            L.marker([{destination_coords[0]}, {destination_coords[1]}], {{icon: destinationIcon}})
                .bindPopup('<strong>{destination_city}</strong><br>Destination')
                .addTo(map);
            
            // Add waypoints
            const waypointCoordinates = [
    """
    
    # Add waypoint coordinates
    for i, coords in enumerate(waypoints):
        try:
            lat, lng = coords
            day_num = i // 3 + 1  # Approximate day number
            html += f"                [{lat}, {lng}],  // Day {day_num} activity\n"
        except:
            continue
    
    html += """
            ];
            
            // Add waypoint markers
            waypointCoordinates.forEach((coords, i) => {
                const dayNum = Math.floor(i / 3) + 1;
                L.marker([coords[0], coords[1]], {icon: waypointIcon})
                    .bindPopup(`<strong>Day ${dayNum} Activity</strong>`)
                    .addTo(map);
            });
            
            // Create a polyline for the main route
            const routeCoordinates = [
                [{origin_coords[0]}, {origin_coords[1]}],
    """
    
    # Add waypoints to route if available
    if waypoints:
        for coords in waypoints:
            try:
                lat, lng = coords
                html += f"                [{lat}, {lng}],\n"
            except:
                continue
    
    html += f"""
                [{destination_coords[0]}, {destination_coords[1]}]
            ];
            
            L.polyline(routeCoordinates, {{color: '#3498db', weight: 4, opacity: 0.7}}).addTo(map);
            
            // Fit map bounds to show all markers
            map.fitBounds([
                [{origin_coords[0]}, {origin_coords[1]}],
                [{destination_coords[0]}, {destination_coords[1]}]
            ]);
        </script>
    </body>
    </html>
    """
    
    # Write the HTML file
    with open(map_file, "w") as f:
        f.write(html)
    
    print_success(f"Route map generated: {map_file}")
    
    # Try to open the HTML file in a browser
    try:
        webbrowser.open(f"file://{os.path.abspath(map_file)}")
    except Exception as e:
        print_warning(f"Could not open map in browser: {str(e)}")
    
    return map_file

def get_city_coordinates(city_name):
    """Get approximate coordinates for common cities"""
    city_coords = {
        'london': (51.5074, -0.1278),
        'paris': (48.8566, 2.3522),
        'rome': (41.9028, 12.4964),
        'berlin': (52.5200, 13.4050),
        'madrid': (40.4168, -3.7038),
        'amsterdam': (52.3676, 4.9041),
        'brussels': (50.8503, 4.3517),
        'vienna': (48.2082, 16.3738),
        'zurich': (47.3769, 8.5417),
        'geneva': (46.2044, 6.1432),
        'new york': (40.7128, -74.0060),
        'washington': (38.9072, -77.0369),
        'los angeles': (34.0522, -118.2437),
        'chicago': (41.8781, -87.6298),
        'tokyo': (35.6762, 139.6503),
        'beijing': (39.9042, 116.4074),
        'delhi': (28.6139, 77.2090),
        'sydney': (33.8688, 151.2093),
        'rio de janeiro': (-22.9068, -43.1729),
        'cape town': (-33.9249, 18.4241)
    }
    
    # Default to London if city not found
    return city_coords.get(city_name.lower(), (51.5074, -0.1278))

def get_transport_icon(transport_mode):
    """Get appropriate icon for transport mode"""
    mode = transport_mode.lower()
    if "car" in mode or "driving" in mode:
        return "🚗"
    elif "train" in mode or "rail" in mode:
        return "🚄"
    elif "bus" in mode:
        return "🚌"
    elif "plane" in mode or "fly" in mode or "air" in mode:
        return "✈️"
    elif "walk" in mode or "foot" in mode:
        return "🚶"
    elif "bike" in mode or "cycle" in mode:
        return "🚲"
    elif "boat" in mode or "ferry" in mode or "ship" in mode:
        return "🚢"
    else:
        return "🚀"

def render_budget_breakdown(route_info):
    """Render budget breakdown HTML section if available"""
    budget = route_info.get('budget_breakdown')
    if not budget:
        return ""
    
    # Calculate total if not provided
    if 'total' not in budget:
        total = sum([float(str(cost).replace('$', '').replace(',', '')) 
                    for item, cost in budget.items() 
                    if item != 'total' and isinstance(cost, (int, float)) or 
                    (isinstance(cost, str) and cost.replace('$', '').replace(',', '').isdigit())])
        budget['total'] = f"${total}"
    
    html = """
    <div class="trip-details">
        <h2>Budget Breakdown</h2>
        <div class="budget-container">
            <table style="width: 100%; border-collapse: collapse;">
                <thead style="background-color: #f5f7fa;">
                    <tr>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Category</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid #e5e7eb;">Cost</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add each budget item
    for item, cost in budget.items():
        if item.lower() != 'total':
            item_name = item.replace('_', ' ').title()
            html += f"""
                    <tr>
                        <td style="padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb;">{item_name}</td>
                        <td style="padding: 12px; text-align: right; border-bottom: 1px solid #e5e7eb;">{cost}</td>
                    </tr>
            """
    
    # Add total row
    html += f"""
                    <tr style="background-color: #f5f7fa; font-weight: bold;">
                        <td style="padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb;">Total</td>
                        <td style="padding: 12px; text-align: right; border-bottom: 1px solid #e5e7eb;">{budget.get('total', 'Not specified')}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """
    
    return html

def generate_blog_post(user_info, partner_info, route_info):
    """Generate a travel blog post based on user information and travel route"""
    print_header("Blog Post Generation")
    
    # Create default route_info if it's None
    if route_info is None:
        # Extract info from user_info
        origin_city = user_info.get('origin_city', 'Your city')
        destination_city = user_info.get('destination_city', 'Paris')
        
        # Create a default route_info structure
        route_info = {
            "trip_summary": {
                "origin": origin_city,
                "destination": destination_city,
                "duration": 7,
                "transportation": "Flight",
                "start_date": datetime.now().strftime('%Y-%m-%d'),
                "end_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            },
            "daily_plan": [
                {
                    "day": 1,
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "activities": [
                        {
                            "time": "Morning",
                            "description": "Arrival and hotel check-in",
                            "location": "Hotel",
                            "cost": "$0"
                        },
                        {
                            "time": "Afternoon",
                            "description": "Explore the neighborhood",
                            "location": "Local area",
                            "cost": "$0"
                        },
                        {
                            "time": "Evening",
                            "description": "Dinner at local restaurant",
                            "location": "Restaurant",
                            "cost": "$30"
                        }
                    ],
                    "accommodation": {
                        "name": "City Hotel",
                        "type": "Hotel",
                        "cost": "$100"
                    }
                }
            ],
            "budget_breakdown": {
                "accommodation": "$700",
                "transportation": "$500",
                "activities": "$300",
                "food": "$400",
                "misc": "$100",
                "total": "$2000"
            }
        }
        print_info("Created default route information for blog generation")
    
    # Create output directory
    output_dir = os.path.join("wandermatch_output", "blogs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Try to generate blog with OpenAI or Gemini
    blog_content = None
    
    # Try with Gemini
    gemini_api_key = get_env_var("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            print_info("Generating blog post with Gemini...")
            blog_content = generate_blog_with_gemini(user_info, partner_info, route_info, gemini_api_key)
            if blog_content:
                print_success("Successfully generated blog with Gemini.")
        except Exception as e:
            print_warning(f"Error generating blog with Gemini: {str(e)}")
    
    # If Gemini fails, try with OpenAI
    if not blog_content:
        openai_api_key = get_env_var("OPENAI_API_KEY")
        if openai_api_key:
            try:
                print_info("Generating blog post with OpenAI...")
                blog_content = generate_blog_with_openai(user_info, partner_info, route_info, openai_api_key)
                if blog_content:
                    print_success("Successfully generated blog with OpenAI.")
            except Exception as e:
                print_warning(f"Error generating blog with OpenAI: {str(e)}")
    
    # If both API methods fail, use a template-based approach
    if not blog_content:
        print_info("Using template-based blog generation...")
        blog_content = generate_blog_with_template(user_info, partner_info, route_info)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save blog as Markdown
    md_path = os.path.join(output_dir, f"travel_blog_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(blog_content)
    
    # Convert to HTML
    html_content = convert_to_html(blog_content, user_info, partner_info, route_info)
    html_path = os.path.join(output_dir, f"travel_blog_{timestamp}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Open the HTML file in the default browser
    try:
        webbrowser.open(f"file://{os.path.abspath(html_path)}")
        print_success(f"Blog opened in your web browser: {html_path}")
    except Exception as e:
        print_warning(f"Unable to open blog in browser: {str(e)}")
    
    return {
        "content": blog_content,
        "file_path": md_path,
        "html_path": html_path
    }

def generate_blog_with_llm(user_info, partner_info, route_info, openai_api_key=None, gemini_api_key=None):
    """Generate a blog post using available LLM APIs"""
    
    # First try Gemini if available
    if gemini_api_key:
        try:
            return generate_blog_with_gemini(user_info, partner_info, route_info, gemini_api_key)
        except Exception as e:
            print_warning(f"Error generating blog with Gemini: {str(e)}")
            # Fall back to OpenAI if available
            if openai_api_key:
                return generate_blog_with_openai(user_info, partner_info, route_info, openai_api_key)
    
    # Try OpenAI if available
    if openai_api_key:
        try:
            return generate_blog_with_openai(user_info, partner_info, route_info, openai_api_key)
        except Exception as e:
            print_warning(f"Error generating blog with OpenAI: {str(e)}")
    
    # Fall back to template if no APIs are available or both failed
    return generate_blog_with_template(user_info, partner_info, route_info)

def generate_blog_with_gemini(user_info, partner_info, route_info, api_key):
    """Generate a blog post using Gemini API"""
    import google.generativeai as genai
    import json
    
    print_info("Generating blog post with Gemini...")
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Set up the model
    generation_config = {
        "temperature": 0.8,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config
    )
    
    # Create a detailed prompt
    destination = route_info.get("trip_summary", {}).get("destination", route_info.get("destination", "your destination"))
    origin = route_info.get("trip_summary", {}).get("origin", route_info.get("origin", "your city"))
    duration = route_info.get("trip_summary", {}).get("duration", route_info.get("duration", 7))
    transport_mode = route_info.get("trip_summary", {}).get("transportation", route_info.get("transportation", {}).get("mode", "transportation"))
    
    # Get user/partner info
    user_name = user_info.get("name", user_info.get("real_name", "Traveler"))
    partner_name = partner_info.get("name", "travel companion") if partner_info else None
    
    # Get daily plan if available
    daily_plan = route_info.get("daily_plan", route_info.get("itinerary", []))
    
    blog_prompt = f"""
    Write an engaging and personal travel blog post about a {duration}-day trip from {origin} to {destination}.
    The traveler is {user_name} {'traveling with ' + partner_name if partner_name else 'traveling solo'}.
    They traveled by {transport_mode}.
    
    The blog should be written in first person perspective, as if {user_name} is telling the story.
    Make it conversational, engaging, and authentic. Include personal observations, emotions, and experiences.
    
    The blog should have a well-structured flow with an introduction, body paragraphs, and conclusion.
    Use descriptive language to paint vivid pictures of the locations visited.
    Include references to local culture, food, and experiences.
    
    The blog should be 800-1200 words total.
    Do not use headers or subheaders in your response.
    Return ONLY the blog post text without any additional formatting or metadata.
    """
    
    try:
        response = model.generate_content(blog_prompt)
        blog_content = response.text.strip()
        return blog_content
    except Exception as e:
        print_warning(f"Error in Gemini blog generation: {str(e)}")
        return None

def generate_blog_with_openai(user_info, partner_info, route_info, api_key):
    """Generate a blog post using OpenAI API"""
    import openai
    
    print_info("Generating blog post with OpenAI...")
    
    # Configure the API
    openai.api_key = api_key
    
    # Create a detailed prompt
    destination = route_info.get("trip_summary", {}).get("destination", route_info.get("destination", "your destination"))
    origin = route_info.get("trip_summary", {}).get("origin", route_info.get("origin", "your city"))
    duration = route_info.get("trip_summary", {}).get("duration", route_info.get("duration", 7))
    transport_mode = route_info.get("trip_summary", {}).get("transportation", route_info.get("transportation", {}).get("mode", "transportation"))
    
    # Get user/partner info
    user_name = user_info.get("name", user_info.get("real_name", "Traveler"))
    partner_name = partner_info.get("name", "travel companion") if partner_info else None
    
    # Get daily plan if available
    daily_plan = route_info.get("daily_plan", route_info.get("itinerary", []))
    
    blog_prompt = f"""
    Write an engaging and personal travel blog post about a {duration}-day trip from {origin} to {destination}.
    The traveler is {user_name} {'traveling with ' + partner_name if partner_name else 'traveling solo'}.
    They traveled by {transport_mode}.
    
    The blog should be written in first person perspective, as if {user_name} is telling the story.
    Make it conversational, engaging, and authentic. Include personal observations, emotions, and experiences.
    
    The blog should have a well-structured flow with an introduction, body paragraphs, and conclusion.
    Use descriptive language to paint vivid pictures of the locations visited.
    Include references to local culture, food, and experiences.
    
    The blog should be 800-1200 words total.
    Do not use headers or subheaders in your response.
    Return ONLY the blog post text without any additional formatting or metadata.
    """
    
    try:
        # Call the API for text generation
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a skilled travel writer who creates engaging blog posts."},
                {"role": "user", "content": blog_prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        blog_content = response.choices[0].message.content.strip()
        return blog_content
    except Exception as e:
        print_warning(f"Error in OpenAI blog generation: {str(e)}")
        return None

def generate_blog_with_template(user_info, partner_info, route_info):
    """Generate a blog post using a template approach"""
    # Get basic information with fallbacks
    destination = route_info.get("trip_summary", {}).get("destination", route_info.get("destination", "your destination"))
    origin = route_info.get("trip_summary", {}).get("origin", route_info.get("origin", "your city"))
    duration = route_info.get("trip_summary", {}).get("duration", route_info.get("duration", 7))
    transportation = route_info.get("trip_summary", {}).get("transportation", route_info.get("transportation", {}).get("mode", "transportation"))
    
    # Get user/partner info
    user_name = user_info.get("name", user_info.get("real_name", "Traveler"))
    partner_name = partner_info.get("name", "my travel companion") if partner_info else None
    
    # Create title
    title = f"My {duration}-day Adventure to {destination}"
    
    # Create intro paragraph
    intro = f"""
I recently had the opportunity to embark on an incredible {duration}-day journey to {destination}. 
The trip began in {origin}, and I chose to travel by {transportation}.
"""

    # Add partner info if available
    if partner_info:
        intro += f" I was fortunate to have {partner_name} join me on this adventure, which made the experience even more memorable."
    else:
        intro += " I decided to travel solo, allowing me to fully immerse myself in the experience at my own pace."
    
    # Generate day-by-day content
    daily_content = ""
    
    # Check if we have daily_plan or itinerary
    daily_plan = route_info.get("daily_plan", route_info.get("itinerary", []))
    
    if daily_plan:
        # For each day in the itinerary
        for day_info in daily_plan[:min(len(daily_plan), duration)]:
            day_num = day_info.get("day", "")
            day_date = day_info.get("date", "")
            day_title = f"Day {day_num}: {day_date}"
            
            # Get activities
            activities = day_info.get("activities", [])
            morning = next((a.get("description", a.get("activity", "Explored the area")) for a in activities if a.get("time", "").lower() == "morning"), day_info.get("morning", "Explored the area"))
            afternoon = next((a.get("description", a.get("activity", "Continued sightseeing")) for a in activities if a.get("time", "").lower() == "afternoon"), day_info.get("afternoon", "Continued sightseeing"))
            evening = next((a.get("description", a.get("activity", "Enjoyed the local cuisine")) for a in activities if a.get("time", "").lower() == "evening"), day_info.get("evening", "Enjoyed the local cuisine"))
            
            # Get accommodation
            accommodation = day_info.get("accommodation", {}).get("name", day_info.get("accommodation", "a local hotel"))
            if isinstance(accommodation, dict):
                accommodation = accommodation.get("name", "a local hotel")
            
            # Create day content
            daily_content += f"""
## {day_title}

In the morning, I {morning.lower() if morning[0].isupper() else morning}. 
The weather was perfect for exploring and I was excited to see what the day would bring.

After lunch, I {afternoon.lower() if afternoon[0].isupper() else afternoon}. 
This was definitely a highlight of the day and provided a deeper understanding of the local culture.

As evening approached, I {evening.lower() if evening[0].isupper() else evening}. 
I stayed at {accommodation} for the night, which provided a comfortable place to rest and reflect on the day's adventures.

"""
    else:
        # Create generic daily content if no specific itinerary provided
        for day in range(1, duration + 1):
            daily_content += f"""
## Day {day}

On this day, I explored {destination} and discovered its unique charm. The morning was spent visiting local attractions,
followed by a delightful lunch sampling the regional cuisine. In the afternoon, I continued my exploration, 
taking in the sights and sounds of this wonderful place. The evening was a perfect time to relax and reflect on the day's adventures.

"""
    
    # Create conclusion
    conclusion = f"""
My trip to {destination} was truly a remarkable experience. {'Traveling with ' + partner_name + ' added a special dimension to the journey.' if partner_info else 'Traveling solo allowed me to fully immerse myself in the experience.'} 
The {duration} days spent exploring this beautiful destination provided memories that will last a lifetime. 
From the moment we left {origin} until our return, every aspect of the journey contributed to an unforgettable adventure.

If you're considering a trip to {destination}, I highly recommend it. The culture, the people, and the experiences are all worth every moment spent there.
"""

    # Combine all sections
    blog_content = f"{intro}\n\n{daily_content}\n{conclusion}"
    
    return blog_content

def convert_to_html(blog_content, user_info, partner_info, route_info):
    """Convert the blog content to HTML with styling"""
    # Extract destination from route_info
    destination = route_info.get("trip_summary", {}).get("destination", route_info.get("destination", "Your Destination"))
    
    # Convert markdown content to HTML
    try:
        # Try to use markdown library if available
        import markdown
        content_html = markdown.markdown(blog_content)
    except ImportError:
        # Simple conversion if markdown library not available
        content_html = blog_content.replace('\n\n', '</p><p>')
        content_html = content_html.replace('\n', '<br>')
        content_html = f'<p>{content_html}</p>'
        content_html = content_html.replace('## ', '</p><h2>')
        content_html = content_html.replace('# ', '</p><h1>')
        parts = content_html.split('</h2>')
        for i in range(1, len(parts)):
            if not parts[i].startswith('<p>'):
                parts[i] = '<p>' + parts[i]
        content_html = '</h2>'.join(parts)
    
    # HTML template with CSS
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Travel Blog: {destination}</title>
        <style>
            :root {{
                --primary-color: #4a6fa5;
                --secondary-color: #ff9e5e;
                --background-color: #f9f9f9;
                --text-color: #333;
                --accent-color: #e67e22;
                --light-accent: #ffeedd;
                --font-main: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                --font-accent: 'Georgia', serif;
            }}
            
            body {{
                font-family: var(--font-main);
                line-height: 1.6;
                color: var(--text-color);
                background-color: var(--background-color);
                margin: 0;
                padding: 0;
            }}
            
            .container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            
            header {{
                text-align: center;
                padding-bottom: 20px;
                border-bottom: 2px solid var(--light-accent);
                margin-bottom: 30px;
            }}
            
            h1 {{
                color: var(--primary-color);
                font-family: var(--font-accent);
                font-size: 2.5em;
                margin-bottom: 5px;
            }}
            
            h2 {{
                color: var(--primary-color);
                font-family: var(--font-accent);
                border-bottom: 1px solid var(--light-accent);
                padding-bottom: 10px;
                margin-top: 30px;
            }}
            
            .subtitle {{
                color: var(--secondary-color);
                font-size: 1.2em;
                font-style: italic;
                margin-top: 0;
            }}
            
            .meta {{
                display: flex;
                justify-content: space-between;
                margin: 20px 0;
                font-size: 0.9em;
                color: #666;
                flex-wrap: wrap;
            }}
            
            .meta-item {{
                background-color: var(--light-accent);
                padding: 5px 10px;
                border-radius: 15px;
                margin: 5px;
            }}
            
            .content {{
                margin-top: 20px;
            }}
            
            p {{
                margin-bottom: 1.2em;
            }}
            
            blockquote {{
                background-color: var(--light-accent);
                border-left: 5px solid var(--accent-color);
                padding: 15px;
                margin: 20px 0;
                font-style: italic;
            }}
            
            img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                margin: 20px 0;
            }}
            
            .highlight {{
                background-color: var(--light-accent);
                padding: 3px 5px;
                border-radius: 3px;
            }}
            
            footer {{
                text-align: center;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 2px solid var(--light-accent);
                color: #666;
                font-size: 0.9em;
            }}
            
            /* Responsive */
            @media (max-width: 600px) {{
                .container {{
                    padding: 15px;
                }}
                
                h1 {{
                    font-size: 2em;
                }}
                
                .meta {{
                    flex-direction: column;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Travel Adventures: {destination}</h1>
                <p class="subtitle">A Journey of Discovery and Experience</p>
            </header>
            
            <div class="meta">
                <span class="meta-item">📅 Date: {datetime.now().strftime('%B %d, %Y')}</span>
                <span class="meta-item">✈️ Destination: {destination}</span>
                <span class="meta-item">👤 Traveler: {user_info.get('name', user_info.get('real_name', 'Anonymous'))}</span>
                {f'<span class="meta-item">👥 Travel Partner: {partner_info.get("name", "Solo")}</span>' if partner_info else ''}
            </div>
            
            <div class="content">
                {content_html}
            </div>
            
            <footer>
                <p>Generated by WanderMatch | {datetime.now().strftime('%Y')}</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    return html_template

def select_travel_partner(user_info):
    """Select a compatible travel partner using the recommendation API and embeddings"""
    print_header("Travel Partner Selection")
    
    # Path to get_user_info folder
    get_user_info_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "get_user_info")
    backend_dir = os.path.join(get_user_info_dir, "backend")
    user_pool_path = os.path.join(get_user_info_dir, "user_pool.csv")
    app_path = os.path.join(backend_dir, "app.py")
    
    # Default values for NaN or blank fields
    default_values = {
        'real_name': 'Travel Partner',
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
        'past_insurance_issues': 'None'
    }
    
    # List to store all potential partners
    potential_partners = []
    
    # First check if app.py exists for the recommendation API
    if os.path.exists(app_path):
        try:
            import subprocess
            import sys
            import time
            import requests
            import json
            import pandas as pd
            import numpy as np
            
            print_info("Starting recommendation service...")
            
            # Check if the API is already running
            api_running = False
            try:
                response = requests.options("http://localhost:5000/api/submit", timeout=2)
                if response.status_code == 200:
                    api_running = True
                    print_info("Recommendation API is already running.")
            except requests.exceptions.RequestException:
                api_running = False
            
            # Start the API if not already running
            if not api_running:
                # Start the Flask app in a separate process
                app_process = subprocess.Popen(
                    [sys.executable, app_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=backend_dir  # Run from the backend directory
                )
                
                # Wait for the API to start
                print_info("Waiting for recommendation API to start...")
                for _ in range(5):  # Try for 5 seconds
                    try:
                        response = requests.options("http://localhost:5000/api/submit", timeout=1)
                        if response.status_code == 200:
                            api_running = True
                            print_success("Recommendation API started successfully.")
                            break
                    except requests.exceptions.RequestException:
                        time.sleep(1)
            
            if api_running:
                # Check if we have user answers from the survey
                csv_files = [f for f in os.listdir(backend_dir) if f.startswith("user_answer_") and f.endswith(".csv")]
                if csv_files:
                    # Sort files by timestamp to get the most recent one
                    latest_file = sorted(csv_files, reverse=True)[0]
                    user_csv_path = os.path.join(backend_dir, latest_file)
                    
                    # Read the user data
                    user_df = pd.read_csv(user_csv_path)
                    
                    if not user_df.empty:
                        # Use the recommendation API to find matching partners
                        print_info("Calculating travel partner matches using embedding similarity...")
                        
                        try:
                            # Clean and prepare data for JSON serialization
                            # Replace NaN values with None for JSON serialization
                            user_data = user_df.iloc[0].replace({np.nan: None})
                            
                            # Convert numpy types to native Python types for JSON serialization
                            user_data = {
                                k: v.item() if isinstance(v, np.number) else v 
                                for k, v in user_data.items()
                            }
                            
                            response = requests.post(
                                "http://localhost:5000/api/recommend", 
                                json={"answers": list(user_data.values())},
                                timeout=60  # Allow up to 60 seconds for embedding calculations
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                recommendations = result.get("recommendations", [])
                                
                                if recommendations:
                                    print_success(f"Found {len(recommendations)} potential travel partners.")
                                    
                                    # Load the user pool to get partner details
                                    if os.path.exists(user_pool_path):
                                        user_pool_df = pd.read_csv(user_pool_path)
                                        
                                        # Replace NaN values with defaults
                                        user_pool_df = user_pool_df.fillna(default_values)
                                        
                                        # Replace empty strings with defaults
                                        for col in user_pool_df.columns:
                                            if col in default_values:
                                                user_pool_df[col] = user_pool_df[col].apply(
                                                    lambda x: default_values[col] if pd.isna(x) or x == '' else x
                                                )
                                        
                                        # Process the top matches (up to 5)
                                        for match in recommendations[:5]:
                                            match_index = match.get("index", 0)
                                            match_score = match.get("score", 0) * 100  # Convert to percentage
                                            
                                            if match_index < len(user_pool_df):
                                                partner_data = user_pool_df.iloc[match_index].to_dict()
                                                
                                                # Ensure all fields have values
                                                for key, default in default_values.items():
                                                    if key not in partner_data or pd.isna(partner_data[key]) or partner_data[key] == '':
                                                        partner_data[key] = default
                                                
                                                # Map fields to match the expected format
                                                partner = {
                                                    "name": partner_data.get("real_name", "Travel Partner"),
                                                    "age": partner_data.get("age_group", "25-34").split('–')[0] if '–' in partner_data.get("age_group", "25-34") else "30",
                                                    "gender": partner_data.get("gender", "Not specified"),
                                                    "nationality": partner_data.get("nationality", "International"),
                                                    "interests": [
                                                        partner_data.get("cultural_symbol", "Local culture"),
                                                        partner_data.get("bucket_list", "Nature exploration"),
                                                        "travel",
                                                        "food"
                                                    ],
                                                    "travel_style": "Balanced explorer",
                                                    "budget_preference": "Medium", 
                                                    "match_percentage": int(match_score),
                                                    "ideal_destination": partner_data.get('preferred_residence', 'Various locations')
                                                }
                                                
                                                # Add to potential partners list
                                                potential_partners.append(partner)
                        except requests.exceptions.RequestException as e:
                            print_warning(f"Error connecting to recommendation API: {str(e)}")
                            print_info("Falling back to alternative method.")
        except Exception as e:
            print_warning(f"Error using recommendation API: {str(e)}")
            print_info("Falling back to alternative method.")
    
    # If we don't have enough partners, try using embed_info.py
    if len(potential_partners) < 3:
        embed_info_path = os.path.join(get_user_info_dir, "embed_info.py")
        if os.path.exists(embed_info_path):
            try:
                import subprocess
                import sys
                import pandas as pd
                import numpy as np
                import json
                
                print_info("Using embed_info.py to calculate match scores...")
                
                # Run the embed_info.py script to calculate matches
                embed_process = subprocess.run(
                    [sys.executable, embed_info_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8',  # Explicitly use UTF-8 instead of universal_newlines
                    errors='replace',  # Replace any problematic characters rather than failing
                    cwd=get_user_info_dir  # Run from the get_user_info directory
                )
                
                if embed_process.returncode == 0:
                    print_success("Match calculation completed successfully.")
                    
                    # Try to find the matches file
                    matches_dir = os.path.join(get_user_info_dir, "results")
                    if not os.path.exists(matches_dir):
                        # Fallback to previous locations
                        matches_dir = os.path.join(get_user_info_dir, "cache")
                        if not os.path.exists(matches_dir):
                            matches_dir = os.getcwd()
                    
                    matches_files = [f for f in os.listdir(matches_dir) if f.startswith("top_matches_") and f.endswith(".csv")]
                    if matches_files:
                        # Sort by modified time to get the most recent
                        matches_files.sort(key=lambda x: os.path.getmtime(os.path.join(matches_dir, x)), reverse=True)
                        latest_matches = matches_files[0]
                        matches_path = os.path.join(matches_dir, latest_matches)
                        
                        # Read the matches file
                        matches_df = pd.read_csv(matches_path)
                        if not matches_df.empty:
                            # Load the user pool to get partner details
                            if os.path.exists(user_pool_path):
                                user_pool_df = pd.read_csv(user_pool_path)
                                
                                # Replace NaN values with defaults
                                user_pool_df = user_pool_df.fillna(default_values)
                                
                                # Replace empty strings with defaults
                                for col in user_pool_df.columns:
                                    if col in default_values:
                                        user_pool_df[col] = user_pool_df[col].apply(
                                            lambda x: default_values[col] if pd.isna(x) or x == '' else x
                                        )
                                
                                # Process each match (up to 5)
                                for _, row in matches_df.iterrows():
                                    if len(potential_partners) >= 5:
                                        break
                                        
                                    match_idx = row.get("User Index", 0)
                                    match_score = row.get("Score", 0) * 100  # Convert to percentage
                                    
                                    # Check if we already have this partner
                                    partner_exists = False
                                    for existing_partner in potential_partners:
                                        if existing_partner.get("name") == user_pool_df.iloc[match_idx].get("real_name", "Travel Partner"):
                                            partner_exists = True
                                            break
                                    
                                    if not partner_exists and match_idx < len(user_pool_df):
                                        partner_data = user_pool_df.iloc[match_idx].to_dict()
                                        
                                        # Ensure all fields have values
                                        for key, default in default_values.items():
                                            if key not in partner_data or pd.isna(partner_data[key]) or partner_data[key] == '':
                                                partner_data[key] = default
                                        
                                        # Map fields to match the expected format
                                        partner = {
                                            "name": partner_data.get("real_name", "Travel Partner"),
                                            "age": partner_data.get("age_group", "25-34").split('–')[0] if '–' in partner_data.get("age_group", "25-34") else "30",
                                            "gender": partner_data.get("gender", "Not specified"),
                                            "nationality": partner_data.get("nationality", "International"),
                                            "interests": [
                                                partner_data.get("cultural_symbol", "Local culture"),
                                                partner_data.get("bucket_list", "Nature exploration"),
                                                "travel",
                                                "food"
                                            ],
                                            "travel_style": "Balanced explorer",
                                            "budget_preference": "Medium", 
                                            "match_percentage": int(match_score),
                                            "ideal_destination": partner_data.get('preferred_residence', 'Various locations')
                                        }
                                        
                                        # Add to potential partners list
                                        potential_partners.append(partner)
                else:
                    print_warning(f"Match calculation returned code {embed_process.returncode}")
                    print_warning(f"Error: {embed_process.stderr}")
            except Exception as e:
                print_warning(f"Error using embed_info.py: {str(e)}")
    
    # If we still don't have enough partners, use the user pool directly
    if len(potential_partners) < 3 and os.path.exists(user_pool_path):
        try:
            import pandas as pd
            import numpy as np
            import random
            
            # Load user pool
            user_pool_df = pd.read_csv(user_pool_path)
            
            # Replace NaN values with defaults
            user_pool_df = user_pool_df.fillna(default_values)
            
            # Replace empty strings with defaults
            for col in user_pool_df.columns:
                if col in default_values:
                    user_pool_df[col] = user_pool_df[col].apply(
                        lambda x: default_values[col] if pd.isna(x) or x == '' else x
                    )
            
            # Filter out user's own name if it exists in the pool
            user_name = user_info.get("name", "")
            if user_name in user_pool_df["real_name"].values:
                user_pool_df = user_pool_df[user_pool_df["real_name"] != user_name]
            
            # Filter out already selected partners
            already_selected_names = [p.get("name") for p in potential_partners]
            user_pool_df = user_pool_df[~user_pool_df["real_name"].isin(already_selected_names)]
            
            if not user_pool_df.empty:
                # Select random partners to fill up to 5 slots
                num_to_select = min(5 - len(potential_partners), len(user_pool_df))
                selected_indices = random.sample(range(len(user_pool_df)), num_to_select)
                
                for idx in selected_indices:
                    partner_data = user_pool_df.iloc[idx].to_dict()
                    
                    # Ensure all fields have values
                    for key, default in default_values.items():
                        if key not in partner_data or pd.isna(partner_data[key]) or partner_data[key] == '':
                            partner_data[key] = default
                    
                    # Map fields to match the expected format
                    partner = {
                        "name": partner_data.get("real_name", "Travel Partner"),
                        "age": partner_data.get("age_group", "25-34").split('–')[0] if '–' in partner_data.get("age_group", "25-34") else "30",
                        "gender": partner_data.get("gender", "Not specified"),
                        "nationality": partner_data.get("nationality", "International"),
                        "interests": [
                            partner_data.get("cultural_symbol", "Local culture"),
                            partner_data.get("bucket_list", "Nature exploration"),
                            "travel",
                            "food"
                        ],
                        "travel_style": "Balanced explorer",
                        "budget_preference": "Medium", 
                        "match_percentage": random.randint(70, 95),  # Random matching score for demonstration
                        "ideal_destination": partner_data.get('preferred_residence', 'Various locations')
                    }
                    
                    # Add to potential partners list
                    potential_partners.append(partner)
        
        except Exception as e:
            print_warning(f"Error finding travel partners: {str(e)}")
    
    # If we still don't have any partners, create default partners
    if not potential_partners:
        print_warning("No matching partners found. Creating default travel partners.")
        
        # Create default partners with different characteristics
        user_gender = user_info.get("gender", "").lower()
        opposite_gender = "Female" if user_gender == "male" else "Male" if user_gender == "female" else "Not specified"
        
        # Partner 1 - Adventure seeker
        partner1 = {
            "name": "Alex Adventure",
            "age": 28,
            "gender": opposite_gender,
            "nationality": "Canadian",
            "interests": ["hiking", "mountain climbing", "wildlife photography", "camping"],
            "travel_style": "Adventure Seeker",
            "budget_preference": "Medium",
            "match_percentage": 92,
            "ideal_destination": "New Zealand"
        }
        
        # Partner 2 - Cultural explorer
        partner2 = {
            "name": "Sam Culture",
            "age": 32,
            "gender": opposite_gender,
            "nationality": "Italian",
            "interests": ["museums", "local cuisine", "history", "architecture"],
            "travel_style": "Cultural Explorer",
            "budget_preference": user_info.get("budget_preference", "Medium"),
            "match_percentage": 85,
            "ideal_destination": "Japan"
        }
        
        # Partner 3 - Relaxation enthusiast
        partner3 = {
            "name": "Riley Relax",
            "age": 30,
            "gender": opposite_gender,
            "nationality": "Australian",
            "interests": ["beaches", "spas", "fine dining", "local markets"],
            "travel_style": "Relaxation Enthusiast",
            "budget_preference": "High" if user_info.get("budget_preference") == "High" else "Medium",
            "match_percentage": 78,
            "ideal_destination": "Maldives"
        }
        
        potential_partners = [partner1, partner2, partner3]
    
    # Display all potential partners with rich formatting if available
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.columns import Columns
        from rich.align import Align
        from rich.text import Text
        
        console = Console()
        console.print("\n")
        console.print(Align.center("[bold cyan]Your Potential Travel Partners[/bold cyan]"))
        console.print("\n")
        
        # Create panels for each partner
        panels = []
        for i, partner in enumerate(potential_partners, 1):
            # Create a summary table
            table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
            table.add_column("Attribute", style="dim")
            table.add_column("Value", style="green")
            
            table.add_row("Age", f"{partner['age']}")
            table.add_row("Gender", f"{partner['gender']}")
            table.add_row("Nationality", f"{partner.get('nationality', 'International')}")
            
            # Format interests nicely
            interests = ", ".join(partner['interests'][:3])
            if len(partner['interests']) > 3:
                interests += "..."
            table.add_row("Interests", interests)
            
            table.add_row("Travel Style", f"{partner['travel_style']}")
            table.add_row("Budget", f"{partner['budget_preference']}")
            
            if "ideal_destination" in partner:
                table.add_row("Dream Destination", f"{partner['ideal_destination']}")
            
            # Create match indicator
            match_percentage = partner['match_percentage']
            match_color = "green" if match_percentage > 85 else "yellow" if match_percentage > 70 else "red"
            match_text = Text(f"Match: {match_percentage}%", style=match_color)
            
            # Create panel with table
            title = f"[bold]Option {i}: {partner['name']}[/bold]"
            panel = Panel(
                table,
                title=title,
                title_align="left",
                subtitle=match_text,
                subtitle_align="right",
                width=40,
                border_style=match_color
            )
            panels.append(panel)
        
        # Display panels in columns
        console.print(Columns(panels, equal=True, expand=True))
        console.print("\n")
    
    except ImportError:
        # Fallback to plain text if rich is not available
        print_header("Your Potential Travel Partners", emoji="🧳")
        for i, partner in enumerate(potential_partners, 1):
            print_subheader(f"Option {i}: {partner['name']} ({partner['match_percentage']}% match)")
            print(f"Age: {partner['age']}")
            print(f"Gender: {partner['gender']}")
            if "nationality" in partner:
                print(f"Nationality: {partner['nationality']}")
            print(f"Interests: {', '.join(partner['interests'])}")
            print(f"Travel Style: {partner['travel_style']}")
            print(f"Budget Preference: {partner['budget_preference']}")
            if "ideal_destination" in partner:
                print(f"Ideal Destination: {partner['ideal_destination']}")
            print("\n")
    
    # Let user choose a partner or go solo
    while True:
        choice = input_prompt(f"Select a travel partner (1-{len(potential_partners)}) or type 'solo' to travel alone: ")
        
        if choice.lower() == 'solo':
            print_info("You've chosen to travel solo.")
            return None
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(potential_partners):
                selected_partner = potential_partners[choice_idx]
                print_success(f"You've selected {selected_partner['name']} as your travel partner!")
                return selected_partner
            else:
                print_warning(f"Please enter a number between 1 and {len(potential_partners)} or 'solo'.")
        except ValueError:
            print_warning(f"Please enter a number between 1 and {len(potential_partners)} or 'solo'.")

def clear_screen():
    """Clear the terminal screen based on operating system"""
    if os.name == 'nt':  # For Windows
        os.system('cls')
    else:  # For Unix/Linux/MacOS
        os.system('clear')

def print_header(text, emoji="🌍", color="blue", centered=True):
    """Print a formatted header with optional styling"""
    terminal_width = 80
    text = f" {text} "
    
    if centered:
        text = text.center(terminal_width - 4, "=")
    else:
        text = f"=== {text} " + "=" * (terminal_width - len(text) - 7)
    
    # Add emoji if provided
    if emoji:
        text = f"{emoji} {text}"
    
    # Print with color if specified
    if color == "blue":
        print(f"\033[1;34m{text}\033[0m")
    elif color == "green":
        print(f"\033[1;32m{text}\033[0m")
    elif color == "red":
        print(f"\033[1;31m{text}\033[0m")
    else:
        print(text)

def print_subheader(text):
    """Print a formatted subheader"""
    print(f"\n\033[1m{text}\033[0m")
    print("-" * len(text))

def print_info(text):
    """Print information message"""
    print(f"\033[0;34mℹ️  {text}\033[0m")

def print_success(text):
    """Print success message"""
    print(f"\033[0;32m✅ {text}\033[0m")

def print_warning(text):
    """Print warning message"""
    print(f"\033[0;33m⚠️  {text}\033[0m")

def print_error(text):
    """Print error message"""
    print(f"\033[0;31m❌ {text}\033[0m")

def input_prompt(prompt_text, default=None):
    """Display a prompt and get user input with optional default value"""
    if default:
        result = input(f"➤ {prompt_text} [{default}]: ")
        return result if result.strip() else default
    else:
        return input(f"➤ {prompt_text} ")

def get_user_info():
    """Get user information using the online survey from get_user_info folder"""
    print_header("User Profile Collection")
    
    # Path to get_user_info folder
    get_user_info_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "get_user_info")
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
            import sys
            import time
            
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
                        encoding='utf-8',  # Explicitly use UTF-8 instead of universal_newlines
                        errors='replace',  # Replace any problematic characters rather than failing
                        cwd=get_user_info_dir  # Run from the get_user_info directory
                    )
                    
                    if embed_process.returncode == 0:
                        print_success("Embeddings calculated successfully.")
                    else:
                        print_warning(f"Embeddings calculation returned code {embed_process.returncode}.")
                        print_warning(f"Error: {embed_process.stderr}")
                except Exception as e:
                    print_warning(f"Error calculating embeddings: {str(e)}")
            
            # Check for the latest user answer file
            if os.path.exists(backend_dir):
                csv_files = [f for f in os.listdir(backend_dir) if f.startswith("user_answer_") and f.endswith(".csv")]
                if csv_files:
                    # Sort files by timestamp to get the most recent one
                    latest_file = sorted(csv_files, reverse=True)[0]
                    user_csv_path = os.path.join(backend_dir, latest_file)
                    print_info(f"Using user data from: {latest_file}")
                    
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
                                'past_insurance_issues': 'None'
                            }
                            
                            # Replace NaN values with defaults
                            user_df = user_df.fillna(default_values)
                            
                            # Replace empty strings with defaults
                            for col in user_df.columns:
                                if col in default_values:
                                    user_df[col] = user_df[col].apply(lambda x: default_values[col] if pd.isna(x) or x == '' else x)
                            
                            # Convert first row to dictionary
                            user_info = user_df.iloc[0].to_dict()
                            print_success("User data collected successfully!")
                            
                            # Print user information summary
                            print_subheader("User Information")
                            for key, value in user_info.items():
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
        except Exception as e:
            print_warning(f"Error launching survey: {str(e)}")
    else:
        print_warning("Survey script not found. Using alternative method.")
    
    # Fall back to using existing user data if survey fails
    # Check if there are any user_answer_*.csv files in the backend directory
    user_info = {}
    if os.path.exists(backend_dir):
        csv_files = [f for f in os.listdir(backend_dir) if f.startswith("user_answer_") and f.endswith(".csv")]
        if csv_files:
            # Sort files by timestamp to get the most recent one
            latest_file = sorted(csv_files, reverse=True)[0]
            user_csv_path = os.path.join(backend_dir, latest_file)
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
                        'past_insurance_issues': 'None'
                    }
                    
                    # Replace NaN values with defaults
                    user_df = user_df.fillna(default_values)
                    
                    # Replace empty strings with defaults
                    for col in user_df.columns:
                        if col in default_values:
                            user_df[col] = user_df[col].apply(lambda x: default_values[col] if pd.isna(x) or x == '' else x)
                    
                    # Convert first row to dictionary
                    user_info = user_df.iloc[0].to_dict()
                    print_success("Existing user data loaded successfully!")
                    
                    # Print user information summary
                    print_subheader("User Information")
                    for key, value in user_info.items():
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
    
    # If no user_answer files or error, try to use a random entry from user_pool.csv
    user_pool_path = os.path.join(get_user_info_dir, "user_pool.csv")
    if os.path.exists(user_pool_path):
        try:
            import pandas as pd
            import random
            import numpy as np
            
            # Read user pool with default values for NaN
            user_pool_df = pd.read_csv(user_pool_path)
            
            if not user_pool_df.empty:
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
                    'past_insurance_issues': 'None'
                }
                
                # Replace NaN values with defaults
                user_pool_df = user_pool_df.fillna(default_values)
                
                # Replace empty strings with defaults
                for col in user_pool_df.columns:
                    if col in default_values:
                        user_pool_df[col] = user_pool_df[col].apply(lambda x: default_values[col] if pd.isna(x) or x == '' else x)
                
                # Select a random user from the pool
                random_user = user_pool_df.sample(1).iloc[0].to_dict()
                print_info("Using a random user from the user pool")
                
                # Update user_info with random user data
                user_info = random_user
                
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
                
                print_success("Random user profile selected!")
                
                # Print user information summary
                print_subheader("User Information")
                for key, value in user_info.items():
                    print(f"{key}: {value}")
                
                return user_info
                
        except Exception as e:
            print_warning(f"Error reading user pool: {str(e)}")
    
    # If all else fails, use default user info
    print_warning("No user data found. Using default user profile.")
    
    default_user = {
        "name": "Anonymous Traveler",
        "age": "30",
        "gender": "Not specified",
        "nationality": "International",
        "interests": ["Local culture", "Nature exploration"],
        "budget_preference": "Medium",
        "travel_style": "Cultural"
    }
    
    return default_user

if __name__ == "__main__":
    main() 