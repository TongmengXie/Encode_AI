#!/usr/bin/env python
"""
Enhanced Visualization Module for Route Data
Provides advanced visualization features including:
- Interactive map generation
- Route animation
- Image generation from geographic data
"""
import os
import json
import folium
from folium.plugins import AntPath, MarkerCluster
import webbrowser
from datetime import datetime
import tempfile
import time
import base64
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

# Import route validator for real route paths
try:
    from route_validator import validate_route
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    print("Route validator not available. Will use simplified route estimation.")

# Initialize rich console for better terminal output
console = Console()

def geocode_location(location_name, api_key=None):
    """Get latitude and longitude for a location name using either Google's API or Gemini."""
    # Note: In a production environment, you would use a real geocoding API
    # This is a simplified version using Gemini as a fallback
    
    # Hardcoded geocoding for common locations (for demo/testing purposes)
    geocode_cache = {
        "san francisco, ca": (37.7749, -122.4194),
        "palo alto, ca": (37.4419, -122.1430),
        "new york, ny": (40.7128, -74.0060),
        "los angeles, ca": (34.0522, -118.2437),
        "chicago, il": (41.8781, -87.6298),
        "seattle, wa": (47.6062, -122.3321),
        "boston, ma": (42.3601, -71.0589),
        "austin, tx": (30.2672, -97.7431),
        "denver, co": (39.7392, -104.9903),
        "portland, or": (45.5051, -122.6750),
        "washington, dc": (38.9072, -77.0369),
        "miami, fl": (25.7617, -80.1918),
        "london, uk": (51.5074, -0.1278),
        "paris, france": (48.8566, 2.3522),
        "tokyo, japan": (35.6762, 139.6503),
        "sydney, australia": (-33.8688, 151.2093),
        "rome, italy": (41.9028, 12.4964),
    }
    
    location_key = location_name.lower().strip()
    if location_key in geocode_cache:
        return geocode_cache[location_key]
    
    # For locations not in our cache, attempt to estimate coordinates
    import google.generativeai as genai
    from dotenv import load_dotenv
    import os
    import json
    
    # Load API key if available
    load_dotenv()
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        console.print("[yellow]No API key available for geocoding[/yellow]")
        # Return a random location as fallback
        import random
        return (random.uniform(30, 50), random.uniform(-100, -70))
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        I need the latitude and longitude coordinates for this location: "{location_name}"
        
        Respond in JSON format only:
        {{
            "latitude": 00.0000,
            "longitude": 00.0000
        }}
        
        Be as accurate as possible. Return ONLY the JSON with no additional text.
        """
        
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 200,
                "temperature": 0,
            }
        )
        
        # Extract JSON from the response
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text.split("```json")[1]
        if "```" in result_text:
            result_text = result_text.split("```")[0]
            
        result = json.loads(result_text.strip())
        
        return (float(result["latitude"]), float(result["longitude"]))
    except Exception as e:
        console.print(f"[yellow]Geocoding error: {str(e)}[/yellow]")
        # Return a random location as fallback
        import random
        return (random.uniform(30, 50), random.uniform(-100, -70))

def generate_route_points(origin_coords, destination_coords, mode="driving", via_points=5):
    """Generate intermediate points for the route animation.
    
    Attempts to use OpenRouteService if available for realistic routes,
    falls back to approximation if not available.
    """
    # If route_validator is available, try to get a real route
    if VALIDATOR_AVAILABLE:
        try:
            # Convert coordinates to location names for the validator
            origin_name = f"{origin_coords[0]},{origin_coords[1]}"
            destination_name = f"{destination_coords[0]},{destination_coords[1]}"
            
            # Get validated route
            validation_result = validate_route(origin_name, destination_name, mode)
            
            # Check if we got route geometry back
            if validation_result.get("service_status") == "available" and "validated_route" in validation_result:
                route_data = validation_result["validated_route"]
                if "route_geometry" in route_data:
                    # Extract coordinates from GeoJSON LineString
                    # OpenRouteService returns [lon, lat] so we swap to [lat, lon] for folium
                    coords = [(point[1], point[0]) for point in route_data["route_geometry"]["coordinates"]]
                    console.print("[green]Using real route path from mapping service[/green]")
                    return coords
        except Exception as e:
            console.print(f"[yellow]Error getting real route path: {e}. Using simplified route.[/yellow]")
    
    # Fallback: Linear interpolation with slight randomization
    console.print("[yellow]Using simplified route estimation (straight line with variations)[/yellow]")
    
    lat1, lon1 = origin_coords
    lat2, lon2 = destination_coords
    
    points = [(lat1, lon1)]
    
    # Generate intermediate points
    for i in range(1, via_points + 1):
        ratio = i / (via_points + 1)
        lat = lat1 + (lat2 - lat1) * ratio
        lon = lon1 + (lon2 - lon1) * ratio
        
        # Add a small random deviation to make it look more realistic
        import random
        lat += random.uniform(-0.01, 0.01)
        lon += random.uniform(-0.01, 0.01)
        
        points.append((lat, lon))
    
    points.append((lat2, lon2))
    return points

def create_animated_map(route_data, output_path="route_map.html"):
    """Create an interactive map with animated route visualization."""
    # Extract key information
    query = route_data.get("query", {})
    origin = query.get("origin", "Unknown Origin")
    destination = query.get("destination", "Unknown Destination")
    selected_mode = route_data.get("selected_mode", "Unknown")
    
    # Get coordinates
    try:
        # Try to geocode the locations
        origin_coords = geocode_location(origin)
        destination_coords = geocode_location(destination)
        
        # Calculate center point for map
        center_lat = (origin_coords[0] + destination_coords[0]) / 2
        center_lon = (origin_coords[1] + destination_coords[1]) / 2
        
        # Create the map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles="OpenStreetMap"
        )
        
        # Add origin marker
        folium.Marker(
            location=origin_coords,
            popup=f"Origin: {origin}",
            tooltip=origin,
            icon=folium.Icon(color="green", icon="play", prefix="fa")
        ).add_to(m)
        
        # Add destination marker
        folium.Marker(
            location=destination_coords,
            popup=f"Destination: {destination}",
            tooltip=destination,
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
        ).add_to(m)
        
        # First try to extract route geometry from final_route if it exists
        route_points = None
        final_route = route_data.get("final_route", {})
        validation_data = final_route.get("validation", {})
        
        # Check if we already have real route geometry in the data
        if "validated_route" in validation_data and "route_geometry" in validation_data["validated_route"]:
            try:
                geometry = validation_data["validated_route"]["route_geometry"]
                # Convert [lon, lat] to [lat, lon] for folium
                route_points = [(point[1], point[0]) for point in geometry["coordinates"]]
                console.print("[green]Using saved route geometry from validation data[/green]")
            except (KeyError, TypeError) as e:
                console.print(f"[yellow]Could not extract saved route geometry: {e}[/yellow]")
                route_points = None
        
        # If no route points yet, generate them
        if not route_points:
            route_points = generate_route_points(origin_coords, destination_coords, mode=selected_mode, via_points=8)
        
        # Create animated path using AntPath
        ant_path = AntPath(
            locations=route_points,
            popup=f"Route: {origin} to {destination}",
            tooltip=f"Transportation Mode: {selected_mode}",
            delay=1000,
            dash_array=[10, 20],
            color=get_color_for_mode(selected_mode),
            weight=5,
            pulse_color="#FFF"
        )
        ant_path.add_to(m)
        
        # Also add a regular polyline for better visibility
        folium.PolyLine(
            locations=route_points,
            color=get_color_for_mode(selected_mode),
            weight=3,
            opacity=0.7,
            tooltip=f"{selected_mode.capitalize()} route"
        ).add_to(m)
        
        # Add waypoints/stops if available in the route data
        steps = final_route.get("steps", [])
        if steps:
            waypoints = MarkerCluster(name="Waypoints").add_to(m)
            
            # Add up to 10 waypoints to avoid cluttering the map
            step_count = len(steps)
            step_interval = max(1, step_count // 10)
            
            for i in range(0, step_count, step_interval):
                if i == 0:  # Skip the first point as we already have the origin marker
                    continue
                    
                step = steps[i]
                # Try to extract location from step instruction
                instruction = step.get("instruction", "")
                
                # Add marker at a point along the route
                if i < len(route_points):
                    point_idx = int((i / step_count) * len(route_points))
                    point = route_points[point_idx]
                    
                    folium.Marker(
                        location=point,
                        popup=f"Step {step.get('number', i)}: {instruction}",
                        tooltip=f"Step {step.get('number', i)}",
                        icon=folium.Icon(color="blue", icon="info-sign", prefix="fa")
                    ).add_to(waypoints)
        
        # Add legend
        legend_html = f"""
        <div style="position: fixed; bottom: 50px; left: 50px; background-color: white; 
        border: 2px solid grey; z-index: 9999; padding: 10px; border-radius: 5px;">
        <p><b>Route Details:</b></p>
        <p>From: {origin}</p>
        <p>To: {destination}</p>
        <p>Mode: {selected_mode.upper()}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save the map
        m.save(output_path)
        
        return output_path, True
    except Exception as e:
        console.print(f"[bold red]Error creating map: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()
        return output_path, False

def get_color_for_mode(mode):
    """Return a color based on transportation mode."""
    mode_colors = {
        "driving": "#FF5733",
        "walking": "#33FF57",
        "biking": "#3357FF",
        "public transit": "#F3FF33",
        "bus": "#F3FF33",
        "train": "#FF33F3"
    }
    
    return mode_colors.get(mode.lower(), "#FF5733")

def create_enhanced_visualization(route_data, output_dir=None):
    """Create enhanced visualizations including maps and animations."""
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    
    # Extract key information
    query = route_data.get("query", {})
    origin = query.get("origin", "Unknown Origin")
    destination = query.get("destination", "Unknown Destination")
    
    console.print(Panel(f"[bold]Creating Enhanced Visualizations[/bold]\nFrom [green]{origin}[/green] to [green]{destination}[/green]"))
    
    with Progress() as progress:
        map_task = progress.add_task("[green]Creating interactive map...", total=100)
        
        # Create filenames for outputs
        base_filename = f"route_{origin.replace(' ', '_')}_to_{destination.replace(' ', '_')}"
        map_filename = os.path.join(output_dir, f"{base_filename}_map.html")
        
        # Generate progress for tasks
        for i in range(10):
            progress.update(map_task, advance=10)
            time.sleep(0.1)
        
        # Create map
        map_path, map_success = create_animated_map(route_data, map_filename)
        
        # Finish progress
        progress.update(map_task, completed=100)
    
    # Show results
    if map_success:
        console.print(f"\n[green]Interactive map created: {map_path}[/green]")
        console.print("[yellow]Opening map in browser...[/yellow]")
        webbrowser.open(f"file://{os.path.abspath(map_path)}")
    else:
        console.print("[red]Failed to create some visualizations[/red]")
    
    return map_path if map_success else None

def main():
    """Test function for enhanced visualization."""
    # Check if a route file is provided
    import sys
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Try to find the most recent route file
        route_files = [f for f in os.listdir() if f.startswith("route_") and f.endswith(".json")]
        if not route_files:
            console.print("[bold red]No route files found. Please generate a route first.[/bold red]")
            return
        
        # Sort by modification time (most recent first)
        route_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        json_file = route_files[0]
        console.print(f"[yellow]Using most recent file: {json_file}[/yellow]")
    
    # Load the JSON data
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        
        # Create enhanced visualizations
        create_enhanced_visualization(data)
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")

if __name__ == "__main__":
    main() 