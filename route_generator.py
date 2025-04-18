#!/usr/bin/env python
"""
Route generation module for WanderMatch.
Contains functions for generating travel routes between cities.
"""
import os
import sys
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from ui_utils import print_header, print_info, print_success, print_warning, print_error
from dotenv import load_dotenv
from map_utils import get_city_coordinates

# Load environment variables
load_dotenv()

# Constants
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_travel_route(user_info, partner_info, transport_option):
    """
    Generate a travel route based on user preferences and transport option.
    
    Args:
        user_info: Dictionary containing user information
        partner_info: Dictionary containing partner information (or None if solo)
        transport_option: Dictionary containing selected transport mode
        
    Returns:
        Dictionary containing route information
    """
    print_header("Generating Your Travel Route", emoji="🗺️")
    
    # Extract necessary information
    origin_city = user_info.get("origin_city", "Unknown Origin")
    destination_city = user_info.get("destination_city", "Unknown Destination")
    transport_mode = transport_option.get("mode", "Unknown Transport")
    
    print_info(f"Creating travel route from {origin_city} to {destination_city} by {transport_mode}")
    
    # Try to generate a route with AI APIs if available
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    route_info = None
    
    # Try AI-based route generation
    if openai_api_key or gemini_api_key:
        try:
            # Set up parameters for route generation
            # Get number of days for the trip (random between 3-7 if not specified)
            trip_days = user_info.get("trip_days", random.randint(3, 7))
            
            # Generate start and end dates
            current_date = datetime.now()
            start_date = current_date + timedelta(days=7)  # Default to one week from now
            end_date = start_date + timedelta(days=trip_days)
            
            # Format dates as strings
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Call fallback route generation
            route_info = fallback_route_generation(
                user_info, 
                partner_info, 
                transport_option,
                origin_city,
                destination_city,
                trip_days,
                start_date_str,
                end_date_str
            )
            
            if route_info:
                print_success("Successfully generated travel route!")
                
        except Exception as e:
            print_warning(f"Error in AI route generation: {str(e)}")
    
    # If AI-based generation failed, use fallback method
    if not route_info:
        print_info("Using fallback route generation...")
        
        # Set default parameters
        trip_days = random.randint(3, 7)
        current_date = datetime.now()
        start_date = current_date + timedelta(days=7)
        end_date = start_date + timedelta(days=trip_days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Generate route with fallback method
        route_info = fallback_route_generation(
            user_info, 
            partner_info, 
            transport_option,
            origin_city,
            destination_city,
            trip_days,
            start_date_str,
            end_date_str
        )
    
    # Generate map if route was successfully created
    if route_info:
        try:
            # Create maps directory
            maps_dir = os.path.join(WORKSPACE_DIR, "wandermatch_output", "maps")
            os.makedirs(maps_dir, exist_ok=True)
            
            # Generate and save the route map
            from map_utils import generate_route_map
            map_path = generate_route_map(
                origin_city,
                destination_city,
                transport_option,
                route_info,
                maps_dir
            )
            
            if map_path:
                route_info["map_path"] = map_path
                print_success(f"Route map saved to: {map_path}")
                
                # Try to open the map in a browser
                try:
                    import webbrowser
                    webbrowser.open('file://' + os.path.abspath(map_path))
                    print_success("Route map opened in your browser!")
                except Exception as e:
                    print_warning(f"Could not open browser: {str(e)}")
                
        except Exception as e:
            print_warning(f"Error generating route map: {str(e)}")
    
    return route_info

def fallback_route_generation(user_info, partner_info, transport_option, 
                             origin_city, destination_city, trip_days, 
                             start_date_str, end_date_str):
    """
    Generate a travel route using a template-based approach when AI generation fails.
    
    Args:
        user_info: Dictionary containing user information
        partner_info: Dictionary containing partner information (or None if solo)
        transport_option: Dictionary containing selected transport mode
        origin_city: Starting city name
        destination_city: Destination city name
        trip_days: Number of days for the trip
        start_date_str: Start date in YYYY-MM-DD format
        end_date_str: End date in YYYY-MM-DD format
        
    Returns:
        Dictionary containing route information
    """
    def extract_cost(cost_string):
        """Helper function to extract cost as a number from string."""
        if not cost_string:
            return 0
        
        # Try to find a number in the string
        import re
        numbers = re.findall(r'\d+', cost_string.replace(',', ''))
        if numbers:
            # Get the first number found
            return float(numbers[0])
        
        return 0
    
    try:
        # Get transportation details
        transport_mode = transport_option.get("mode", "Custom Transport")
        transport_cost = extract_cost(transport_option.get("cost", "100"))
        transport_duration = transport_option.get("duration", "Varies")
        
        # Get coordinates for origin and destination
        origin_coords = get_city_coordinates(origin_city)
        dest_coords = get_city_coordinates(destination_city)
        
        # Generate itinerary based on trip length
        daily_budget = 100  # Default daily budget in USD
        
        if user_info and "budget" in user_info:
            budget_str = user_info.get("budget", "")
            budget_num = extract_cost(budget_str)
            if budget_num > 0:
                daily_budget = budget_num
        
        # Calculate total budget
        total_budget = daily_budget * trip_days + transport_cost
        
        # Generate attractions based on destination
        attractions = generate_attractions(destination_city)
        
        # Create route points
        route_points = [
            {"name": origin_city, "coords": origin_coords},
            {"name": destination_city, "coords": dest_coords}
        ]
        
        # Add intermediate points for longer trips
        if trip_days > 3:
            # Generate some intermediate points between origin and destination
            num_stops = random.randint(1, 2)
            
            for _ in range(num_stops):
                # Create a point somewhere between origin and destination
                lat = (origin_coords[0] + dest_coords[0]) / 2 + random.uniform(-0.5, 0.5)
                lon = (origin_coords[1] + dest_coords[1]) / 2 + random.uniform(-0.5, 0.5)
                
                # Add to route points
                route_points.insert(1, {
                    "name": f"Scenic Stop",
                    "coords": (lat, lon)
                })
        
        # Create budget breakdown
        budget_breakdown = {
            "Transportation": transport_cost,
            "Accommodation": daily_budget * 0.4 * trip_days,
            "Food": daily_budget * 0.3 * trip_days,
            "Activities": daily_budget * 0.2 * trip_days,
            "Miscellaneous": daily_budget * 0.1 * trip_days
        }
        
        # Assemble the route information
        route_info = {
            "origin": origin_city,
            "destination": destination_city,
            "transport_mode": transport_mode,
            "transport_cost": transport_cost,
            "transport_duration": transport_duration,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "trip_days": trip_days,
            "daily_budget": daily_budget,
            "total_budget": total_budget,
            "budget": budget_breakdown,
            "attractions": attractions,
            "route_points": route_points,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        
        return route_info
    
    except Exception as e:
        print_error(f"Error in fallback route generation: {str(e)}")
        
        # Return minimal route info
        return {
            "origin": origin_city,
            "destination": destination_city,
            "transport_mode": transport_option.get("mode", "Custom Transport"),
            "trip_days": trip_days,
            "start_date": start_date_str,
            "end_date": end_date_str
        }

def generate_attractions(destination_city):
    """
    Generate a list of attractions for the destination city.
    
    Args:
        destination_city: Name of the destination city
        
    Returns:
        List of attraction dictionaries
    """
    # Try to get coordinates for the city
    city_coords = get_city_coordinates(destination_city)
    
    # Predefined attractions by city (for common destinations)
    city_attractions = {
        "Paris": [
            {"name": "Eiffel Tower", "description": "Iconic iron tower offering city views"},
            {"name": "Louvre Museum", "description": "World-famous art museum home to the Mona Lisa"},
            {"name": "Notre-Dame Cathedral", "description": "Medieval Catholic cathedral"},
            {"name": "Montmartre", "description": "Historic arts district with Sacré-Cœur Basilica"}
        ],
        "London": [
            {"name": "British Museum", "description": "Museum of human history and culture"},
            {"name": "Tower of London", "description": "Historic castle and former prison"},
            {"name": "Buckingham Palace", "description": "Royal residence and administrative headquarters"},
            {"name": "Westminster Abbey", "description": "Gothic abbey church and UNESCO site"}
        ],
        "New York": [
            {"name": "Statue of Liberty", "description": "Iconic neoclassical statue symbolizing freedom"},
            {"name": "Central Park", "description": "Urban park spanning 843 acres"},
            {"name": "Empire State Building", "description": "Art Deco skyscraper with observation deck"},
            {"name": "Metropolitan Museum of Art", "description": "One of the world's largest art museums"}
        ],
        "Tokyo": [
            {"name": "Tokyo Skytree", "description": "Broadcasting and observation tower"},
            {"name": "Senso-ji Temple", "description": "Ancient Buddhist temple in Asakusa"},
            {"name": "Meiji Shrine", "description": "Shinto shrine dedicated to Emperor Meiji"},
            {"name": "Shibuya Crossing", "description": "Famous scramble crossing in Shibuya district"}
        ],
        "Rome": [
            {"name": "Colosseum", "description": "Ancient amphitheater in the center of Rome"},
            {"name": "Vatican Museums", "description": "Museums displaying works from the papal collection"},
            {"name": "Trevi Fountain", "description": "Baroque fountain in Rome city center"},
            {"name": "Roman Forum", "description": "Ancient government buildings and ruins"}
        ]
    }
    
    # Check if we have predefined attractions for this city
    if destination_city in city_attractions:
        attractions = city_attractions[destination_city]
        
        # Add coordinates to each attraction
        for attraction in attractions:
            # Create slightly offset coordinates for each attraction
            lat_offset = random.uniform(-0.02, 0.02)
            lon_offset = random.uniform(-0.02, 0.02)
            
            attraction["coords"] = (
                city_coords[0] + lat_offset,
                city_coords[1] + lon_offset
            )
        
        return attractions
    
    # Generate generic attractions for unknown cities
    generic_attractions = [
        {"name": "City Museum", "description": "Learn about the local history and culture"},
        {"name": "Central Park", "description": "Relax and enjoy nature in the heart of the city"},
        {"name": "Historic District", "description": "Explore the charming old town area"},
        {"name": "Local Market", "description": "Experience authentic food and crafts"}
    ]
    
    # Add coordinates to each attraction
    for attraction in generic_attractions:
        # Create slightly offset coordinates for each attraction
        lat_offset = random.uniform(-0.02, 0.02)
        lon_offset = random.uniform(-0.02, 0.02)
        
        attraction["coords"] = (
            city_coords[0] + lat_offset,
            city_coords[1] + lon_offset
        )
        
        # Customize the name to include city
        if "City Museum" in attraction["name"]:
            attraction["name"] = f"{destination_city} Museum"
        elif "Central Park" in attraction["name"]:
            attraction["name"] = f"{destination_city} Central Park"
    
    return generic_attractions 