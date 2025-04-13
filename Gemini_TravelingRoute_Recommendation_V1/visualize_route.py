#!/usr/bin/env python
"""
Route Visualization Tool for JSON route data.
Creates a simple HTML visualization of route data generated by RouteGenerator.
"""
import json
import os
import webbrowser
from datetime import datetime
import folium
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

# Import route validator for real route paths
try:
    from route_validator import validate_route
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    print("Route validator not available. Will use simplified route estimation.")

# Try to import geocoding function from enhanced visualization if available
try:
    from enhanced_visualization import geocode_location, generate_route_points
    ENHANCED_VIZ_AVAILABLE = True
except ImportError:
    ENHANCED_VIZ_AVAILABLE = False
    # We'll define simplified versions of these functions below

# Initialize rich console for better terminal output
console = Console()

# Define these functions if enhanced visualization isn't available
if not ENHANCED_VIZ_AVAILABLE:
    def geocode_location(location_name, api_key=None):
        """Simplified geocoding function that uses a dictionary of major cities."""
        geocode_cache = {
            "london": (51.5074, -0.1278),
            "cambridge": (52.2053, 0.1218),
            "oxford": (51.7520, -1.2577),
            "brighton": (50.8225, -0.1372),
            "manchester": (53.4808, -2.2426),
            "liverpool": (53.4084, -2.9916),
            "york": (53.9599, -1.0873),
            "leeds": (53.8008, -1.5491),
            "edinburgh": (55.9533, -3.1883),
            "glasgow": (55.8642, -4.2518),
            "bath": (51.3781, -2.3597),
            "bristol": (51.4545, -2.5879),
            "cardiff": (51.4816, -3.1791),
            "birmingham": (52.4862, -1.8904),
            "newcastle": (54.9783, -1.6178),
            "san francisco": (37.7749, -122.4194),
            "new york": (40.7128, -74.0060),
            "palo alto": (37.4419, -122.1430),
        }
        
        # Try to match the location to our cache
        clean_name = location_name.lower().split(',')[0].strip()
        if clean_name in geocode_cache:
            return geocode_cache[clean_name]
        
        # Fallback: return a random location in the UK
        import random
        return (random.uniform(50, 55), random.uniform(-5, 2))
    
    def generate_route_points(origin_coords, destination_coords, mode="driving", via_points=5):
        """Generate intermediate points for the route animation."""
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
                        return coords
            except Exception as e:
                print(f"Error getting real route path: {e}. Using simplified route.")
        
        # Fallback: Linear interpolation with slight randomization
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
            lat += random.uniform(-0.005, 0.005)
            lon += random.uniform(-0.005, 0.005)
            
            points.append((lat, lon))
        
        points.append((lat2, lon2))
        return points

def create_html_visualization(data, output_path="route_visualization.html"):
    """Create an HTML visualization of the route data."""
    
    # Extract key information
    query = data.get("query", {})
    origin = query.get("origin", "Unknown Origin")
    destination = query.get("destination", "Unknown Destination")
    selected_mode = data.get("selected_mode", "Unknown")
    plan = data.get("plan", {})
    final_route = data.get("final_route", {})
    
    # Create a basic HTML structure
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Route from {origin} to {destination}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
            }}
            .section {{
                margin-bottom: 25px;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 6px;
                border-left: 4px solid #4CAF50;
            }}
            .weather-section {{
                background-color: #e3f2fd;
                border-left: 4px solid #2196F3;
            }}
            .walkability-section {{
                background-color: #fff8e1;
                border-left: 4px solid #FFC107;
            }}
            .transport-section {{
                background-color: #f1f8e9;
            }}
            .selected-transport {{
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
            }}
            .transport-option {{
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .steps-section {{
                background-color: #e8eaf6;
                border-left: 4px solid #3F51B5;
            }}
            .step {{
                margin-bottom: 10px;
                padding: 10px;
                background-color: white;
                border-radius: 4px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }}
            ul.pros-cons {{
                padding-left: 20px;
            }}
            .pros {{
                color: #4CAF50;
            }}
            .cons {{
                color: #F44336;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .recommendations {{
                background-color: #fce4ec;
                border-left: 4px solid #E91E63;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Route from {origin} to {destination}</h1>
                <p>Transportation Mode: {selected_mode.upper()}</p>
                <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
    """
    
    # Add Weather Section if available
    if "weather" in plan:
        weather = plan["weather"]
        html += f"""
            <div class="section weather-section">
                <h2>Weather Conditions in {destination}</h2>
                <p><strong>Description:</strong> {weather.get("description", "N/A")}</p>
                <p><strong>Temperature:</strong> {weather.get("temperature", "N/A")}</p>
                <p><strong>Conditions:</strong> {weather.get("conditions", "N/A")}</p>
                <p><strong>Recommendation:</strong> {weather.get("recommendation", "N/A")}</p>
            </div>
        """
    
    # Add Walkability Section if available
    if "walkability" in plan:
        walkability = plan["walkability"]
        html += f"""
            <div class="section walkability-section">
                <h2>Walkability Assessment</h2>
                <p><strong>Score:</strong> {walkability.get("score", "N/A")}</p>
                <p><strong>Description:</strong> {walkability.get("description", "N/A")}</p>
                <h3>Pros:</h3>
                <ul class="pros-cons pros">
        """
        for pro in walkability.get("pros", []):
            html += f"<li>{pro}</li>"
        html += """
                </ul>
                <h3>Cons:</h3>
                <ul class="pros-cons cons">
        """
        for con in walkability.get("cons", []):
            html += f"<li>{con}</li>"
        html += """
                </ul>
            </div>
        """
    
    # Add Transportation Options Section
    html += """
            <div class="section transport-section">
                <h2>Transportation Options</h2>
    """
    for option in plan.get("transportation_options", []):
        is_selected = option.get("mode", "").lower() == selected_mode.lower()
        class_name = "transport-option selected-transport" if is_selected else "transport-option"
        html += f"""
                <div class="{class_name}">
                    <h3>{option.get("mode", "").upper()}{" (Selected)" if is_selected else ""}</h3>
                    <p><strong>Time:</strong> {option.get("estimated_time", "N/A")}</p>
                    <p><strong>Distance:</strong> {option.get("distance", "N/A")}</p>
                    <p><strong>Cost:</strong> {option.get("cost", "N/A")}</p>
                    <p><strong>Weather Impact:</strong> {option.get("weather_impact", "N/A")}</p>
                    <h4>Pros:</h4>
                    <ul class="pros-cons pros">
        """
        for pro in option.get("pros", []):
            html += f"<li>{pro}</li>"
        html += """
                    </ul>
                    <h4>Cons:</h4>
                    <ul class="pros-cons cons">
        """
        for con in option.get("cons", []):
            html += f"<li>{con}</li>"
        html += """
                    </ul>
                </div>
        """
    html += """
            </div>
    """
    
    # Map section removed per user request
    # Add Route Summary Section if available
    if "route_summary" in final_route:
        summary = final_route["route_summary"]
        html += f"""
            <div class="section">
                <h2>Route Summary</h2>
                <p><strong>Mode:</strong> {summary.get("mode", "N/A")}</p>
                <p><strong>Total Time:</strong> {summary.get("total_time", "N/A")}</p>
                <p><strong>Total Distance:</strong> {summary.get("total_distance", "N/A")}</p>
                <p><strong>Weather Advisory:</strong> {summary.get("weather_advisory", "N/A")}</p>
            </div>
        """
    
    # Add Route Steps Section if available
    if "steps" in final_route:
        html += """
            <div class="section steps-section">
                <h2>Route Steps</h2>
                <table>
                    <tr>
                        <th>#</th>
                        <th>Instruction</th>
                        <th>Distance</th>
                        <th>Time</th>
                        <th>Notes</th>
                    </tr>
        """
        for step in final_route["steps"]:
            html += f"""
                    <tr>
                        <td>{step.get("number", "N/A")}</td>
                        <td>{step.get("instruction", "N/A")}</td>
                        <td>{step.get("distance", "N/A")}</td>
                        <td>{step.get("time", "N/A")}</td>
                        <td>{step.get("notes", "N/A")}</td>
                    </tr>
            """
        html += """
                </table>
            </div>
        """
    
    # Add Recommendations Section if available
    if "recommendations" in final_route:
        html += """
            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
        """
        for rec in final_route["recommendations"]:
            html += f"<li>{rec}</li>"
        html += """
                </ul>
            </div>
        """
    
    # Close the HTML structure
    html += """
        </div>
    </body>
    </html>
    """
    
    # Write the HTML to a file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return output_path

def display_terminal_visualization(data):
    """Display a rich text visualization in the terminal."""
    console.clear()
    
    # Extract key information
    query = data.get("query", {})
    origin = query.get("origin", "Unknown Origin")
    destination = query.get("destination", "Unknown Destination")
    selected_mode = data.get("selected_mode", "Unknown")
    plan = data.get("plan", {})
    final_route = data.get("final_route", {})
    
    # Create header
    console.print(Panel(f"[bold green]Route from {origin} to {destination}[/bold green]", 
                         subtitle=f"Transportation Mode: {selected_mode.upper()}"))
    
    # Display weather information
    if "weather" in plan:
        weather = plan["weather"]
        weather_table = Table(title="Weather Conditions", show_header=True, header_style="bold blue")
        weather_table.add_column("Attribute")
        weather_table.add_column("Value")
        weather_table.add_row("Description", weather.get("description", "N/A"))
        weather_table.add_row("Temperature", weather.get("temperature", "N/A"))
        weather_table.add_row("Conditions", weather.get("conditions", "N/A"))
        weather_table.add_row("Recommendation", weather.get("recommendation", "N/A"))
        console.print(weather_table)
    
    # Display walkability information
    if "walkability" in plan:
        walkability = plan["walkability"]
        console.print(Panel(f"[bold yellow]Walkability Score: {walkability.get('score', 'N/A')}[/bold yellow]"))
        console.print(f"[italic]{walkability.get('description', 'N/A')}[/italic]")
        
        pros_cons = Table(show_header=True)
        pros_cons.add_column("Pros", style="green")
        pros_cons.add_column("Cons", style="red")
        
        # Get the maximum length of pros and cons lists
        max_len = max(len(walkability.get("pros", [])), len(walkability.get("cons", [])))
        
        # Add rows with corresponding pros and cons
        for i in range(max_len):
            pro = walkability.get("pros", [])[i] if i < len(walkability.get("pros", [])) else ""
            con = walkability.get("cons", [])[i] if i < len(walkability.get("cons", [])) else ""
            pros_cons.add_row(pro, con)
        
        console.print(pros_cons)
    
    # Display route summary
    if "route_summary" in final_route:
        summary = final_route["route_summary"]
        summary_table = Table(title="Route Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Attribute")
        summary_table.add_column("Value")
        summary_table.add_row("Total Time", summary.get("total_time", "N/A"))
        summary_table.add_row("Total Distance", summary.get("total_distance", "N/A"))
        summary_table.add_row("Weather Advisory", summary.get("weather_advisory", "N/A"))
        console.print(summary_table)
    
    # Display first few route steps
    if "steps" in final_route:
        console.print("[bold blue]Route Steps:[/bold blue]")
        steps_table = Table(show_header=True)
        steps_table.add_column("#")
        steps_table.add_column("Instruction")
        steps_table.add_column("Distance")
        steps_table.add_column("Time")
        
        # Show only first 5 steps to avoid cluttering the terminal
        for step in final_route["steps"][:5]:
            steps_table.add_row(
                str(step.get("number", "N/A")),
                step.get("instruction", "N/A"),
                step.get("distance", "N/A"),
                step.get("time", "N/A")
            )
        
        if len(final_route["steps"]) > 5:
            steps_table.add_row("...", "...", "...", "...")
        
        console.print(steps_table)
    
    # Display recommendations
    if "recommendations" in final_route:
        recs = Tree("[bold pink]Recommendations[/bold pink]")
        for rec in final_route["recommendations"]:
            recs.add(rec)
        console.print(recs)
    
    console.print(f"\n[bold green]Full HTML visualization has been created![/bold green]")

def main():
    """Main function to visualize the route data."""
    # Check command line arguments
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Try to find the most recent route file
        route_files = [f for f in os.listdir() if f.startswith("route_") and f.endswith(".json")]
        if not route_files:
            console.print("[bold red]No route files found. Please specify a file path.[/bold red]")
            return
        
        # Sort by modification time (most recent first)
        route_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        json_file = route_files[0]
        console.print(f"[yellow]Using most recent file: {json_file}[/yellow]")
    
    # Load the JSON data
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        
        # Create the HTML visualization
        output_path = create_html_visualization(data)
        
        # Show terminal visualization
        display_terminal_visualization(data)
        
        # Open the HTML file in the default browser
        console.print(f"[green]Opening visualization in browser: {output_path}[/green]")
        webbrowser.open(f"file://{os.path.abspath(output_path)}")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")

if __name__ == "__main__":
    main() 