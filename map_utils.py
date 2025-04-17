#!/usr/bin/env python
"""
Map generation utilities for WanderMatch.
Contains functions for generating maps and getting city coordinates.
"""
import os
import folium
from folium.plugins import MarkerCluster
import math
import requests
from typing import Dict, Any, List, Tuple
from ui_utils import print_header, print_info, print_success, print_warning, print_error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_city_coordinates(city_name):
    """
    Get the latitude and longitude of a city using OpenStreetMap Nominatim API.
    
    Args:
        city_name: Name of the city
        
    Returns:
        Tuple of (latitude, longitude) or default coordinates if not found
    """
    try:
        # Use Nominatim API for geocoding
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {
            "User-Agent": "WanderMatch/1.0",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
        
        # If OpenStreetMap fails, try Google Maps API if available
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if google_api_key:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city_name}&key={google_api_key}"
            response = requests.get(url)
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results") and len(data["results"]) > 0:
                location = data["results"][0]["geometry"]["location"]
                return (location["lat"], location["lng"])
        
        # Return default coordinates if not found (center of Europe)
        print_warning(f"Could not find coordinates for {city_name}. Using default.")
        return (48.8566, 2.3522)  # Paris coordinates as fallback
        
    except Exception as e:
        print_error(f"Error getting coordinates for {city_name}: {str(e)}")
        # Return default coordinates
        return (48.8566, 2.3522)  # Paris coordinates as fallback

def generate_route_map(origin_city, destination_city, transport_option, route_info, maps_dir):
    """
    Generate an interactive map with the travel route.
    
    Args:
        origin_city: Starting city
        destination_city: Destination city
        transport_option: Selected transport option
        route_info: Dictionary containing route information
        maps_dir: Directory to save the map HTML file
        
    Returns:
        String path to the generated HTML map file
    """
    try:
        # Create the maps directory if it doesn't exist
        os.makedirs(maps_dir, exist_ok=True)
        
        # Get coordinates for origin and destination
        origin_coords = get_city_coordinates(origin_city)
        dest_coords = get_city_coordinates(destination_city)
        
        # Calculate the center point between origin and destination
        center_lat = (origin_coords[0] + dest_coords[0]) / 2
        center_lon = (origin_coords[1] + dest_coords[1]) / 2
        
        # Create a new map centered between the two cities
        route_map = folium.Map(location=[center_lat, center_lon], zoom_start=6)
        
        # Extract route points (if available)
        route_points = route_info.get('route_points', [])
        if not route_points:
            # If no specific route points, just use origin and destination
            route_points = [
                {'name': origin_city, 'coords': origin_coords},
                {'name': destination_city, 'coords': dest_coords}
            ]
        
        # Add markers for each point in the route
        for point in route_points:
            if isinstance(point, dict) and 'coords' in point:
                coords = point['coords']
                name = point.get('name', 'Stop')
                
                # Create a popup with information
                popup_html = f"""
                <div style="width: 200px; height: auto;">
                    <h4>{name}</h4>
                </div>
                """
                
                # Add marker to the map
                folium.Marker(
                    location=coords,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=name,
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(route_map)
        
        # Create a line connecting all points
        if len(route_points) >= 2:
            points = [point['coords'] for point in route_points if 'coords' in point]
            folium.PolyLine(
                points,
                color='red',
                weight=3,
                opacity=0.7,
                tooltip=f"{transport_option.get('mode', 'Custom')} route"
            ).add_to(route_map)
        
        # Add attractions if available
        attractions = route_info.get('attractions', [])
        if attractions:
            # Create a marker cluster for attractions
            marker_cluster = MarkerCluster(name="Attractions").add_to(route_map)
            
            for attraction in attractions:
                if isinstance(attraction, dict):
                    name = attraction.get('name', 'Attraction')
                    
                    # Get coordinates for the attraction
                    if 'coords' in attraction:
                        coords = attraction['coords']
                    else:
                        # Try to get coordinates based on name and city
                        location = f"{name}, {destination_city}"
                        coords = get_city_coordinates(location)
                    
                    description = attraction.get('description', '')
                    
                    # Create a popup with information
                    popup_html = f"""
                    <div style="width: 200px; height: auto;">
                        <h4>{name}</h4>
                        <p>{description}</p>
                    </div>
                    """
                    
                    # Add marker to the cluster
                    folium.Marker(
                        location=coords,
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=name,
                        icon=folium.Icon(color='green', icon='star')
                    ).add_to(marker_cluster)
        
        # Add a layer control
        folium.LayerControl().add_to(route_map)
        
        # Save the map to an HTML file
        timestamp = route_info.get('timestamp', '')
        if timestamp:
            map_file = f"route_map_{timestamp}.html"
        else:
            import time
            map_file = f"route_map_{int(time.time())}.html"
            
        map_path = os.path.join(maps_dir, map_file)
        route_map.save(map_path)
        
        print_success(f"Route map saved to: {map_path}")
        return map_path
        
    except Exception as e:
        print_error(f"Error generating route map: {str(e)}")
        return None