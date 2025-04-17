#!/usr/bin/env python
"""
Transport-related functions for WanderMatch.
Contains functions for selecting and generating transport options.
"""
import os
import sys
import webbrowser
import json
from typing import Dict, Any, List
from ui_utils import print_header, print_info, print_success, print_warning, print_error, input_prompt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    output_dir = os.path.join(WORKSPACE_DIR, "wandermatch_output", "maps")
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
        transport_options = get_default_transport_options(origin_city, destination_city)
    
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
            comfort = option.get("comfort_level", 3)
            
            # Convert comfort rating to stars
            comfort_stars = "⭐" * min(int(comfort), 5)
            
            table.add_row(
                str(i),
                mode,
                duration,
                cost,
                carbon,
                comfort_stars
            )
        
        console.print(table)
        
        # Let user select a transport option
        selection = input_prompt(f"Select a transport option (1-{len(transport_options)})", default="1")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(transport_options):
                selected_option = transport_options[idx]
                print_success(f"You selected: {selected_option.get('mode', 'Custom transport')}")
                return selected_option
            else:
                print_warning(f"Invalid selection. Using option 1 by default.")
                return transport_options[0]
        except (ValueError, IndexError):
            print_warning(f"Invalid selection. Using option 1 by default.")
            return transport_options[0]
            
    except ImportError:
        # Fallback to simple selection
        for i, option in enumerate(transport_options, 1):
            print(f"{i}. {option.get('mode', 'Option ' + str(i))}")
            print(f"   Duration: {option.get('duration', 'Unknown')}")
            print(f"   Cost: {option.get('cost', 'Unknown')}")
            print()
        
        selection = input_prompt(f"Select a transport option (1-{len(transport_options)})", default="1")
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(transport_options):
                return transport_options[idx]
            else:
                return transport_options[0]
        except (ValueError, IndexError):
            return transport_options[0]

def generate_transport_options_with_gemini(origin_city, destination_city, api_key):
    """
    Generate transport options using Google's Gemini API.
    
    Args:
        origin_city: Starting city
        destination_city: Destination city
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
        I need detailed transport options to travel from {origin_city} to {destination_city}.
        
        For each transport mode (flight, train, bus, car, ferry, etc.), provide:
        - Duration (e.g., "2h 30m")
        - Approximate cost range in USD (e.g., "$120-150")
        - Carbon footprint level (e.g., "High", "Medium", "Low")
        - Comfort level (1-5 stars)
        - Brief pros and cons (1-2 short points each)
        
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
            
            # Parse the JSON
            transport_options = json.loads(json_content)
            
            # Validate the results
            if isinstance(transport_options, list) and len(transport_options) > 0:
                return transport_options
        
        # If we couldn't extract valid JSON, return an empty list
        print_warning("Could not extract valid transport options from Gemini response.")
        return []
    
    except Exception as e:
        print_error(f"Error generating transport options with Gemini: {str(e)}")
        return []

def generate_transport_options_with_openai(origin_city, destination_city, api_key):
    """
    Generate transport options using OpenAI API.
    
    Args:
        origin_city: Starting city
        destination_city: Destination city
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
        I need detailed transport options to travel from {origin_city} to {destination_city}.
        
        For each transport mode (flight, train, bus, car, ferry, etc.), provide:
        - Duration (e.g., "2h 30m")
        - Approximate cost range in USD (e.g., "$120-150")
        - Carbon footprint level (e.g., "High", "Medium", "Low")
        - Comfort level (1-5 stars)
        - Brief pros and cons (1-2 short points each)
        
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
            
            # Parse the JSON
            transport_options = json.loads(json_content)
            
            # Validate the results
            if isinstance(transport_options, list) and len(transport_options) > 0:
                return transport_options
        
        # If we couldn't extract valid JSON, return an empty list
        print_warning("Could not extract valid transport options from OpenAI response.")
        return []
    
    except Exception as e:
        print_error(f"Error generating transport options with OpenAI: {str(e)}")
        return []

def get_default_transport_options(origin_city, destination_city):
    """
    Generate default transport options for any city pair.
    
    Args:
        origin_city: Starting city
        destination_city: Destination city
        
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
        }
    ]

def generate_transport_html(origin_city, destination_city, transport_options):
    """
    Generate an HTML visualization of transport options.
    
    Args:
        origin_city: Starting city
        destination_city: Destination city
        transport_options: List of transport option dictionaries
        
    Returns:
        HTML content as a string
    """
    # HTML template for the transport comparison
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transport Options: {origin} to {destination}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            h1, h2 {{
                color: #2c3e50;
                text-align: center;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                background-color: #3498db;
                color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .container {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
                margin-top: 30px;
            }}
            .card {{
                background-color: white;
                border-radius: 8px;
                overflow: hidden;
                width: 300px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }}
            .card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }}
            .card-header {{
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                font-size: 1.2em;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .card-body {{
                padding: 20px;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            .label {{
                font-weight: bold;
                color: #7f8c8d;
            }}
            .value {{
                text-align: right;
                color: #2c3e50;
            }}
            .pros-cons {{
                margin-top: 15px;
            }}
            .pros, .cons {{
                margin-bottom: 10px;
            }}
            .pros h4, .cons h4 {{
                margin-bottom: 5px;
                color: #555;
                font-size: 0.9em;
                text-transform: uppercase;
            }}
            .pros ul {{
                color: #27ae60;
            }}
            .cons ul {{
                color: #e74c3c;
            }}
            ul {{
                padding-left: 20px;
                margin: 5px 0;
            }}
            li {{
                margin-bottom: 5px;
            }}
            .icon {{
                font-size: 24px;
                margin-right: 10px;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                color: #7f8c8d;
                font-size: 0.9em;
            }}
            .carbon {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: bold;
                text-transform: uppercase;
            }}
            .carbon.high {{
                background-color: #ffebee;
                color: #e53935;
            }}
            .carbon.medium {{
                background-color: #fff8e1;
                color: #ffb300;
            }}
            .carbon.low {{
                background-color: #e8f5e9;
                color: #43a047;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Transport Options</h1>
            <h2>{origin} to {destination}</h2>
        </div>
        
        <div class="container">
            {cards}
        </div>
        
        <div class="footer">
            <p>Generated by WanderMatch • Compare options and select your preferred mode in the terminal</p>
        </div>
    </body>
    </html>
    """
    
    # Generate a card for each transport option
    cards = []
    
    for option in transport_options:
        # Get transport mode data with fallbacks
        mode = option.get('mode', 'Custom Transport')
        duration = option.get('duration', 'Varies')
        cost = option.get('cost', 'Variable')
        carbon = option.get('carbon_footprint', 'Unknown')
        comfort = option.get('comfort_level', 3)
        pros = option.get('pros', ['Convenient option'])
        cons = option.get('cons', ['Varies by conditions'])
        
        # Determine carbon footprint class
        carbon_class = "medium"
        if "high" in carbon.lower():
            carbon_class = "high"
        elif "low" in carbon.lower():
            carbon_class = "low"
        
        # Generate comfort stars
        comfort_stars = "★" * min(int(comfort), 5) + "☆" * (5 - min(int(comfort), 5))
        
        # Create pros and cons HTML
        pros_html = "<ul>" + "".join([f"<li>{pro}</li>" for pro in pros]) + "</ul>"
        cons_html = "<ul>" + "".join([f"<li>{con}</li>" for con in cons]) + "</ul>"
        
        # Generate the card HTML
        card_html = f"""
        <div class="card">
            <div class="card-header">
                <span class="icon">🚀</span> {mode}
            </div>
            <div class="card-body">
                <div class="info-row">
                    <span class="label">Duration:</span>
                    <span class="value">⏱️ {duration}</span>
                </div>
                <div class="info-row">
                    <span class="label">Cost:</span>
                    <span class="value">💰 {cost}</span>
                </div>
                <div class="info-row">
                    <span class="label">Carbon:</span>
                    <span class="value"><span class="carbon {carbon_class}">{carbon}</span></span>
                </div>
                <div class="info-row">
                    <span class="label">Comfort:</span>
                    <span class="value">{comfort_stars}</span>
                </div>
                <div class="pros-cons">
                    <div class="pros">
                        <h4>✅ Pros</h4>
                        {pros_html}
                    </div>
                    <div class="cons">
                        <h4>❌ Cons</h4>
                        {cons_html}
                    </div>
                </div>
            </div>
        </div>
        """
        
        cards.append(card_html)
    
    # Join all cards and replace placeholders in the template
    all_cards = "\n".join(cards)
    html_content = html_template.format(
        origin=origin_city,
        destination=destination_city,
        cards=all_cards
    )
    
    return html_content

def get_transport_icon(transport_mode):
    """
    Get an appropriate icon for the transport mode.
    
    Args:
        transport_mode: Name of the transport mode
        
    Returns:
        String containing an appropriate emoji
    """
    transport_mode = transport_mode.lower()
    
    if "plane" in transport_mode or "flight" in transport_mode or "air" in transport_mode:
        return "✈️"
    elif "train" in transport_mode or "rail" in transport_mode:
        return "🚆"
    elif "bus" in transport_mode or "coach" in transport_mode:
        return "🚌"
    elif "car" in transport_mode or "drive" in transport_mode or "taxi" in transport_mode:
        return "🚗"
    elif "boat" in transport_mode or "ferry" in transport_mode or "ship" in transport_mode:
        return "⛴️"
    elif "bike" in transport_mode or "bicycle" in transport_mode or "cycle" in transport_mode:
        return "🚲"
    elif "walk" in transport_mode or "foot" in transport_mode or "hiking" in transport_mode:
        return "🚶"
    elif "subway" in transport_mode or "metro" in transport_mode or "underground" in transport_mode:
        return "🚇"
    elif "tram" in transport_mode or "streetcar" in transport_mode:
        return "🚊"
    elif "motorcycle" in transport_mode or "motorbike" in transport_mode:
        return "🏍️"
    else:
        return "🚀" 