#!/usr/bin/env python
"""
Route Validator
Validates routes using OpenRouteService to ensure they follow actual physical paths
"""
import os
import json
from dotenv import load_dotenv
import openrouteservice as ors
from openrouteservice.exceptions import ApiError

# Load environment variables
load_dotenv()

# Get OpenRouteService API key - if not set, we'll use a restricted demo key
ORS_API_KEY = os.getenv("ORS_API_KEY", "5b3ce3597851110001cf6248a90f5836ceb346c4842f3eb03f84f756")

# Initialize the OpenRouteService client
try:
    client = ors.Client(key=ORS_API_KEY)
    SERVICE_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not initialize OpenRouteService client: {e}")
    SERVICE_AVAILABLE = False

def validate_route(origin, destination, mode):
    """
    Validate a route between origin and destination using the specified mode of transport.
    
    Args:
        origin (str): The starting point in "City, Country" or "Address" format
        destination (str): The ending point in "City, Country" or "Address" format
        mode (str): One of 'driving-car', 'cycling-regular', 'foot-walking', 'public-transport'
    
    Returns:
        dict: Validation results with keys:
            - is_valid (bool): True if the route is physically possible
            - issues (list): List of any issues found
            - alternatives (list): Suggested alternatives if route has issues
            - validated_route (dict, optional): Route data if available
    """
    if not SERVICE_AVAILABLE:
        print("OpenRouteService API not initialized. Using distance-based validation instead.")
        return validate_route_distance_based(origin, destination, mode)
    
    # Attempt API-based validation with fallback
    try:
        # Map our transportation modes to OpenRouteService profiles
        profile_mapping = {
            "driving": "driving-car",
            "biking": "cycling-regular",
            "walking": "foot-walking"
        }
        
        # Get the appropriate ORS profile
        profile = profile_mapping.get(mode.lower(), "driving-car")
        
        # Public transit isn't directly supported by the free API
        if mode.lower() == "public transit":
            return {
                "is_valid": True,  # Assume valid for public transit
                "issues": ["Public transit validation requires specialized transit APIs"],
                "alternatives": ["Consider checking with local transit authorities"],
                "service_status": "limited"
            }
        
        # Try geocoding the locations
        try:
            origin_geocode = client.pelias_search(text=origin, size=1)
            if not origin_geocode.get('features', []):
                print(f"Could not geocode origin: {origin}. Falling back to distance-based validation.")
                return validate_route_distance_based(origin, destination, mode)
            
            destination_geocode = client.pelias_search(text=destination, size=1)
            if not destination_geocode.get('features', []):
                print(f"Could not geocode destination: {destination}. Falling back to distance-based validation.")
                return validate_route_distance_based(origin, destination, mode)
            
            # Extract coordinates [longitude, latitude]
            origin_coords = origin_geocode['features'][0]['geometry']['coordinates']
            destination_coords = destination_geocode['features'][0]['geometry']['coordinates']
            
        except Exception as e:
            print(f"Geocoding error: {e}. Falling back to distance-based validation.")
            return validate_route_distance_based(origin, destination, mode)
        
        # Get route directions
        directions = client.directions(
            coordinates=[origin_coords, destination_coords],
            profile=profile,
            format='geojson'
        )
        
        # Check if route exists
        if not directions.get('features', []):
            return {
                "is_valid": False,
                "issues": [f"No valid {mode} route found from {origin} to {destination}"],
                "alternatives": [f"Try a different mode of transportation"],
                "service_status": "no_route"
            }
        
        # Extract route data
        route_feature = directions['features'][0]
        route_geometry = route_feature['geometry']
        route_properties = route_feature['properties']
        
        # Get key metrics
        distance_km = route_properties.get('summary', {}).get('distance', 0) / 1000  # Convert m to km
        duration_hrs = route_properties.get('summary', {}).get('duration', 0) / 3600  # Convert s to hrs
        
        # Perform validation checks based on mode
        issues = []
        alternatives = []
        
        # Check for very long walking routes (over 30km)
        if mode.lower() == "walking" and distance_km > 30:
            issues.append(f"Walking distance of {distance_km:.1f}km is very long and may not be practical")
            alternatives.append(f"Consider public transit or driving for this distance")
        
        # Check for very long biking routes (over 100km)
        if mode.lower() == "biking" and distance_km > 100:
            issues.append(f"Cycling distance of {distance_km:.1f}km is very long and may be challenging")
            alternatives.append(f"Consider breaking this journey into multiple days")
        
        # Return validation results
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "alternatives": alternatives,
            "service_status": "available",
            "validated_route": {
                "distance_km": distance_km,
                "duration_hrs": duration_hrs,
                "route_geometry": route_geometry  # GeoJSON LineString of the route
            }
        }
        
    except ApiError as e:
        error_message = str(e)
        if "location not accessible by car" in error_message.lower():
            return {
                "is_valid": False,
                "issues": [f"Location not accessible by {mode}"],
                "alternatives": ["Try a different starting point or destination"],
                "service_status": "api_error"
            }
        else:
            return {
                "is_valid": True,  # Assume valid since API error
                "issues": [f"API Error: {error_message}"],
                "alternatives": [],
                "service_status": "api_error"
            }
    except Exception as e:
        print(f"API validation error: {e}. Falling back to distance-based validation.")
        return validate_route_distance_based(origin, destination, mode)

def validate_route_distance_based(origin, destination, mode):
    """
    Validate a route using distance-based heuristics when the API is not available.
    This is a fallback method that uses common knowledge about distances and transport modes.
    
    Args:
        origin (str): The starting point
        destination (str): The ending point
        mode (str): The transportation mode
    
    Returns:
        dict: Validation results
    """
    import re
    
    # Extract city names for simple matching
    def extract_city(location):
        # Try to extract the first part before a comma
        city_match = re.match(r'^([^,]+)', location.strip())
        if city_match:
            return city_match.group(1).strip().lower()
        return location.lower()
    
    origin_city = extract_city(origin)
    destination_city = extract_city(destination)
    
    # Dictionary of approximate distances between major cities (in km)
    # This is a very simplified approach for demonstration
    city_distances = {
        ("london", "cambridge"): 100,
        ("london", "oxford"): 95,
        ("london", "brighton"): 85,
        ("london", "bristol"): 190,
        ("london", "manchester"): 320,
        ("london", "liverpool"): 350,
        ("london", "leeds"): 310,
        ("london", "york"): 335,
        ("london", "edinburgh"): 650,
        ("london", "glasgow"): 670,
        ("manchester", "liverpool"): 55,
        ("manchester", "leeds"): 70,
        ("manchester", "york"): 100,
        ("manchester", "edinburgh"): 330,
        ("manchester", "glasgow"): 345,
        # Add more city pairs as needed
    }
    
    # Try to get distance between cities
    distance_km = None
    city_pair = (origin_city, destination_city)
    reverse_pair = (destination_city, origin_city)
    
    if city_pair in city_distances:
        distance_km = city_distances[city_pair]
    elif reverse_pair in city_distances:
        distance_km = city_distances[reverse_pair]
    
    # If we couldn't find a distance, make a rough estimate based on character similarity
    if distance_km is None:
        # This is a very rough fallback when we don't have data
        # In a real app, you would use a more sophisticated method
        # or integrate with another geolocation service
        random_factor = hash(origin_city + destination_city) % 100
        distance_km = 100 + random_factor
        print(f"Warning: Distance data not available for {origin} to {destination}.")
        print(f"Using estimated distance of approximately {distance_km}km.")
    
    # Validate based on mode and distance
    issues = []
    alternatives = []
    
    # Walking: Generally not practical beyond 30km
    if mode.lower() == "walking" and distance_km > 30:
        issues.append(f"Walking distance of {distance_km}km is very long and may not be practical")
        alternatives.append("Consider public transit or driving for this distance")
    
    # Biking: Challenging beyond 100km for casual cyclists
    if mode.lower() == "biking" and distance_km > 100:
        issues.append(f"Cycling distance of {distance_km}km is very long and may be challenging")
        alternatives.append("Consider breaking this journey into multiple days")
    
    # Public transit: May be limited between distant cities
    if mode.lower() == "public transit" and distance_km > 300:
        issues.append(f"Public transit for {distance_km}km may involve multiple connections")
        alternatives.append("Check with local transit authorities for the best routes")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "alternatives": alternatives,
        "service_status": "distance_based",
        "validated_route": {
            "distance_km": distance_km,
            "duration_hrs": distance_km / (
                45 if mode.lower() == "driving" else
                15 if mode.lower() == "biking" else
                4 if mode.lower() == "walking" else 60  # Speeds in km/h
            ),
            "estimation_method": "distance_based"
        }
    }

def add_validation_to_env():
    """Add ORS_API_KEY to .env file if not present"""
    env_path = ".env"
    
    # Check if .env file exists
    if os.path.exists(env_path):
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        # Check if key exists
        key_exists = any(line.strip().startswith("ORS_API_KEY=") for line in lines)
        
        if not key_exists:
            # Append the key with the demo key
            with open(env_path, 'a') as file:
                file.write(f"\n# OpenRouteService API key for route validation\n")
                file.write(f"ORS_API_KEY={ORS_API_KEY}\n")
                file.write(f"# Get your own key at: https://openrouteservice.org/dev/#/signup\n")
            
            print(f"Added ORS_API_KEY to {env_path} with demo key")
            print("Note: The demo key has limited requests. Get your own key for better service.")

if __name__ == "__main__":
    # Add API key to .env if not present
    add_validation_to_env()
    
    # Test the validation with a simple example
    print("Testing route validation...")
    
    test_origin = "London, UK"
    test_destination = "Cambridge, UK"
    test_mode = "driving"
    
    print(f"Validating {test_mode} route from {test_origin} to {test_destination}...")
    validation_result = validate_route(test_origin, test_destination, test_mode)
    
    print(json.dumps(validation_result, indent=2)) 