#!/usr/bin/env python
"""
Travel Route Planner - Gemini Powered
A streamlined travel planning application using Google's Gemini API
for route generation and visualization.
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Import our modules
try:
    from RouteGenerator_Hybrid import RouteGenerator
    import visualize_route
    import enhanced_visualization
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required files are in the current directory")
    sys.exit(1)

# Initialize rich console for better terminal output
console = Console()

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    console.print("[bold red]GEMINI_API_KEY not found in environment variables[/bold red]")
    console.print("Please make sure you have a .env file with GEMINI_API_KEY value.")
    sys.exit(1)

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import dotenv
        import requests
        import folium
        import rich
        console.print("[green]All core dependencies are installed and available.[/green]")
        
        # Check for Google Generative AI
        try:
            import google.generativeai
            console.print("[green]Google Generative AI library is available for route generation.[/green]")
        except ImportError:
            console.print("[bold red]Google Generative AI library is not installed. This is required.[/bold red]")
            console.print("Please install it with: pip install google-generativeai")
            return False
            
        return True
    except ImportError as e:
        console.print(f"[bold red]Missing core dependency: {e}[/bold red]")
        console.print("Please install all required packages:")
        console.print("pip install -r requirements.txt")
        return False

def validate_location(location):
    """Validate and normalize location input using Gemini."""
    try:
        # Initialize a model for validation
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        I need to validate this location: "{location}"
        
        First, determine if this is a valid geographic location (city, place, address, landmark, etc.).
        If it's valid, provide the properly formatted name.
        If it's misspelled, suggest the correct spelling.
        
        Respond in JSON format only:
        {{
            "is_valid": true/false,
            "normalized_name": "Properly formatted location name",
            "confidence": 0-100,
            "suggestions": ["Possible alternative 1", "Possible alternative 2"]
        }}
        
        Return ONLY the JSON with no additional text.
        """
        
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 500,
                "temperature": 0.1,
            }
        )
        
        # Extract JSON from the response
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text.split("```json")[1]
        if "```" in result_text:
            result_text = result_text.split("```")[0]
            
        result = json.loads(result_text.strip())
        
        return result
    except Exception as e:
        console.print(f"[yellow]Location validation error: {str(e)}[/yellow]")
        # Return default structure if validation fails
        return {
            "is_valid": True,  # Assume valid if we can't check
            "normalized_name": location,
            "confidence": 0,
            "suggestions": []
        }

def run_route_generation():
    """Run the route generation workflow with Gemini."""
    console.print(Panel("[bold]Route Generator[/bold]", subtitle="Powered by Gemini"))
    
    try:
        # Create the route generator
        generator = RouteGenerator()
        
        # Get origin and destination from user with validation
        origin_input = Prompt.ask("Enter origin location", default="London")
        
        # Validate origin
        origin_validation = validate_location(origin_input)
        if not origin_validation["is_valid"]:
            console.print(f"[yellow]'{origin_input}' doesn't seem to be a valid location.[/yellow]")
            if origin_validation["suggestions"]:
                suggestion = origin_validation["suggestions"][0]
                console.print(f"Did you mean: [green]{suggestion}[/green]?")
                if Prompt.ask("Use this suggestion?", choices=["y", "n"], default="y") == "y":
                    origin = suggestion
                else:
                    origin = origin_input
            else:
                origin = origin_input
        else:
            # Use normalized name if confidence is high enough
            if origin_validation["confidence"] > 70:
                if origin_validation["normalized_name"] != origin_input:
                    console.print(f"[yellow]Using normalized name: [green]{origin_validation['normalized_name']}[/green][/yellow]")
                origin = origin_validation["normalized_name"]
            else:
                origin = origin_input
        
        # Get and validate destination
        destination_input = Prompt.ask("Enter destination location", default="Bath")
        
        # Validate destination
        destination_validation = validate_location(destination_input)
        if not destination_validation["is_valid"]:
            console.print(f"[yellow]'{destination_input}' doesn't seem to be a valid location.[/yellow]")
            if destination_validation["suggestions"]:
                suggestion = destination_validation["suggestions"][0]
                console.print(f"Did you mean: [green]{suggestion}[/green]?")
                if Prompt.ask("Use this suggestion?", choices=["y", "n"], default="y") == "y":
                    destination = suggestion
                else:
                    destination = destination_input
            else:
                destination = destination_input
        else:
            # Use normalized name if confidence is high enough
            if destination_validation["confidence"] > 70:
                if destination_validation["normalized_name"] != destination_input:
                    console.print(f"[yellow]Using normalized name: [green]{destination_validation['normalized_name']}[/green][/yellow]")
                destination = destination_validation["normalized_name"]
            else:
                destination = destination_input
        
        # Show final locations
        console.print(f"\n[bold]Planning route from [green]{origin}[/green] to [green]{destination}[/green][/bold]")
        
        # Generate route plan
        console.print(f"\n[bold]Generating route plan...[/bold]")
        try:
            plan = generator.generate_route_plan(origin, destination)
            
            if "error" in plan:
                console.print(f"\n[bold red]Error: {plan.get('error', 'Unknown error')}[/bold red]")
                if Prompt.ask("\nDo you want to try again with different locations?", choices=["y", "n"], default="y") == "y":
                    return run_route_generation()
                return None
                
        except Exception as e:
            console.print(f"\n[bold red]Error generating route plan: {str(e)}[/bold red]")
            return None
        
        # Verify the plan contains transportation options
        if "transportation_options" not in plan or not plan["transportation_options"]:
            console.print("\n[bold red]Error: No transportation options found in the plan[/bold red]")
            return None
        
        # Get user's transportation choice
        try:
            selected_mode = generator.get_user_choice(plan["transportation_options"])
            console.print(f"\n[bold green]Selected: {selected_mode.upper()}[/bold green]")
        except Exception as e:
            console.print(f"\n[bold red]Error selecting transportation mode: {str(e)}[/bold red]")
            return None
        
        # Generate final route based on selection
        console.print("\n[bold]Generating detailed route...[/bold]")
        try:
            final_route = generator.generate_final_route(plan, selected_mode, origin, destination)
            
            if not final_route:
                console.print("\n[bold red]Failed to generate route details. Please try again.[/bold red]")
                return None
            
            # Check route validation
            if "validation" in final_route:
                if not final_route["validation"].get("is_validated", True):
                    console.print("\n[bold yellow]⚠️ Route Validation Warning ⚠️[/bold yellow]")
                    console.print("[yellow]This route may have issues with physical feasibility:[/yellow]")
                    for issue in final_route["validation"].get("issues", []):
                        console.print(f"[yellow]• {issue}[/yellow]")
                    
                    # Show alternatives if available
                    if final_route["validation"].get("alternatives", []):
                        console.print("\n[bold cyan]Suggested alternatives:[/bold cyan]")
                        for alt in final_route["validation"].get("alternatives", []):
                            console.print(f"[cyan]• {alt}[/cyan]")
                    
                    # Ask user if they want to continue or try a different mode
                    if Prompt.ask("\nDo you want to continue with this route or try a different mode?", 
                                choices=["continue", "different"], default="continue") == "different":
                        console.print("\n[yellow]Let's try a different transportation mode.[/yellow]")
                        return run_route_generation()
                else:
                    console.print("\n[bold green]✓ Route validated - This route follows real physical paths[/bold green]")
            
            # Display feasibility assessment if available
            if "route_summary" in final_route and "feasibility_assessment" in final_route["route_summary"]:
                assessment = final_route["route_summary"]["feasibility_assessment"]
                if "not" in assessment.lower() or "impossible" in assessment.lower() or "difficult" in assessment.lower():
                    console.print(f"\n[bold yellow]Feasibility Assessment: {assessment}[/bold yellow]")
                else:
                    console.print(f"\n[bold green]Feasibility Assessment: {assessment}[/bold green]")
                
            console.print("\n[bold cyan]====== DETAILED ROUTE ======[/bold cyan]")
            
            # Display route summary
            if "route_summary" in final_route:
                summary = final_route["route_summary"]
                console.print(Panel.fit(
                    f"[bold]From [green]{summary.get('origin', origin)}[/green] to [green]{summary.get('destination', destination)}[/green][/bold]\n"
                    f"Mode: [cyan]{summary.get('mode', selected_mode.upper())}[/cyan]\n"
                    f"Distance: {summary.get('total_distance', 'Unknown')}\n"
                    f"Time: {summary.get('total_time', 'Unknown')}\n"
                    f"Weather: {summary.get('weather_advisory', plan['weather'].get('description', 'Unknown'))}",
                    title="Route Summary"
                ))
            
            # Display safety concerns if available
            if "safety_concerns" in final_route and final_route["safety_concerns"]:
                console.print("\n[bold yellow]Safety Concerns:[/bold yellow]")
                for concern in final_route["safety_concerns"]:
                    console.print(f"[yellow]• {concern}[/yellow]")
            
            # Display route steps
            if "steps" in final_route and final_route["steps"]:
                console.print("\n[bold]Step by Step Directions:[/bold]")
                for step in final_route["steps"]:
                    step_num = step.get("number", "")
                    instruction = step.get("instruction", "")
                    distance = step.get("distance", "")
                    time = step.get("time", "")
                    path_type = step.get("path_type", "")
                    
                    # Format the path type with appropriate color based on type
                    path_type_colored = ""
                    if path_type:
                        color = "white"
                        if "highway" in path_type.lower():
                            color = "blue"
                        elif "road" in path_type.lower():
                            color = "green"
                        elif "bike" in path_type.lower():
                            color = "cyan"
                        elif "footpath" in path_type.lower() or "pedestrian" in path_type.lower():
                            color = "yellow"
                        path_type_colored = f" [[{color}]{path_type}[/{color}]]"
                    
                    console.print(f"[bold]{step_num}.[/bold] {instruction}{path_type_colored}")
                    if distance and time:
                        console.print(f"   [dim]({distance}, approx. {time})[/dim]")
                    elif distance:
                        console.print(f"   [dim]({distance})[/dim]")
            
            # Display full JSON for debugging if needed
            if os.getenv("DEBUG_MODE") == "True":
                console.print("\n[dim]Raw route data:[/dim]")
                console.print(json.dumps(final_route, indent=2))
            
            # Save results
            try:
                filename = generator.save_results(plan, selected_mode, final_route, origin, destination)
                console.print(f"\n[green]Route generation complete! Results saved to {filename}[/green]")
                
                # Ask if the user wants to visualize the route
                if Prompt.ask("\nDo you want to visualize this route?", choices=["y", "n"], default="y") == "y":
                    visualize_route_data(filename)
                
                return filename
            except Exception as e:
                console.print(f"\n[bold red]Error saving route results: {str(e)}[/bold red]")
                return None
                
        except Exception as e:
            console.print(f"\n[bold red]Error generating detailed route: {str(e)}[/bold red]")
            return None
            
    except Exception as e:
        console.print(f"\n[bold red]Error in route generation: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()
        return None

def visualize_route_data(json_file=None):
    """Visualize route data using visualization features."""
    console.print(Panel("[bold]Route Visualization[/bold]", subtitle="Maps & Animation"))
    
    if not json_file:
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
        if not os.path.exists(json_file):
            console.print(f"[bold red]Error: File '{json_file}' does not exist[/bold red]")
            return
            
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                console.print(f"[bold red]Error: Invalid JSON in file '{json_file}'[/bold red]")
                console.print(f"JSON error: {str(e)}")
                return
        
        # Verify required keys exist in the data
        required_keys = ["query"]
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            console.print(f"[bold red]Error: Missing required data in '{json_file}'[/bold red]")
            console.print(f"Missing keys: {', '.join(missing_keys)}")
            return
        
        # Show visualization options
        console.print("\n[bold]Visualization Options:[/bold]")
        console.print("[1] Basic Visualization (Terminal + Text Summary, No Map)")
        console.print("[2] Enhanced Visualization (Interactive Map with Route Animation)")
        console.print("[3] Both Visualizations")
        
        choice = Prompt.ask("\nSelect visualization type", choices=["1", "2", "3"], default="2")
        
        if choice in ["1", "3"]:
            # Create the basic HTML visualization
            console.print("\n[bold]Creating basic visualization...[/bold]")
            output_path = visualize_route.create_html_visualization(data)
            
            # Show terminal visualization
            visualize_route.display_terminal_visualization(data)
            
            # Open the HTML file in the default browser if only basic visualization was chosen
            if choice == "1":
                console.print(f"\n[green]Opening basic visualization in browser: {output_path}[/green]")
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(output_path)}")
        
        if choice in ["2", "3"]:
            # Create enhanced visualization with map and animation
            console.print("\n[bold]Creating enhanced visualization with interactive map...[/bold]")
            enhanced_visualization.create_enhanced_visualization(data)
        
    except Exception as e:
        console.print(f"[bold red]Error visualizing route: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()

def configure_api_settings():
    """Configure Gemini API settings."""
    console.print(Panel("[bold]API Configuration[/bold]", subtitle="Gemini API"))
    
    console.print("\n[bold]Current API Configuration:[/bold]")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    if gemini_key:
        console.print(f"[green]Gemini API Key: {gemini_key[:6]}...{gemini_key[-4:]}[/green]")
    else:
        console.print("[red]Gemini API Key: Not configured[/red]")
    
    # Update Gemini API Key
    current = gemini_key if gemini_key else ""
    new_key = Prompt.ask("Enter new Gemini API Key (press Enter to keep current)", default=current, password=True)
    
    if new_key and new_key != current:
        # Update the .env file
        update_env_file("GEMINI_API_KEY", new_key)
        console.print("[green]Gemini API Key updated successfully[/green]")
        
        # Update the current environment variable
        os.environ["GEMINI_API_KEY"] = new_key
        
        # Reconfigure Gemini API
        genai.configure(api_key=new_key)
        console.print("[green]Gemini API reconfigured with new key[/green]")

def update_env_file(key, value):
    """Update a key-value pair in the .env file."""
    env_path = os.path.join(os.getcwd(), '.env')
    
    # Read existing content
    if os.path.exists(env_path):
        with open(env_path, 'r') as file:
            lines = file.readlines()
    else:
        lines = []
    
    # Check if key exists and update it
    key_exists = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f'{key}="{value}"\n'
            key_exists = True
            break
    
    # If key doesn't exist, add it
    if not key_exists:
        lines.append(f'{key}="{value}"\n')
    
    # Write back to file
    with open(env_path, 'w') as file:
        file.writelines(lines)

def display_main_menu():
    """Display the main menu options and handle user input."""
    # Check API availability
    gemini_available = os.getenv("GEMINI_API_KEY") is not None
    
    console.print(Panel.fit(
        "[bold green]Travel Route Planner[/bold green]\n"
        "Gemini-powered route planning and visualization\n"
        f"[{'green' if gemini_available else 'red'}]Gemini API: {'Available' if gemini_available else 'Not configured'}[/{'green' if gemini_available else 'red'}]",
        title="Main Menu"
    ))
    
    console.print("\n[bold]Available options:[/bold]")
    console.print("[1] Generate Travel Route")
    console.print("[2] Visualize Existing Route")
    console.print("[3] Check Dependencies")
    console.print("[4] Configure API Settings")
    console.print("[0] Exit")
    
    # Get user input with flexible handling
    valid_choices = ["0", "1", "2", "3", "4"]
    choice_mapping = {
        "0": "0", "exit": "0", "quit": "0", "q": "0",
        "1": "1", "route": "1", "generate": "1", "g": "1", "plan": "1",
        "2": "2", "visualize": "2", "vis": "2", "view": "2", "v": "2",
        "3": "3", "check": "3", "dependencies": "3", "dep": "3", "d": "3",
        "4": "4", "config": "4", "settings": "4", "api": "4", "setup": "4"
    }
    
    while True:
        user_input = input("\nEnter your choice: ").strip().lower()
        
        # Direct match to valid choices
        if user_input in valid_choices:
            return user_input
            
        # Try to map to valid choice
        if user_input in choice_mapping:
            mapped_choice = choice_mapping[user_input]
            console.print(f"[yellow]Interpreting '{user_input}' as option [{mapped_choice}][/yellow]")
            return mapped_choice
            
        # Check for similarity to valid options
        import difflib
        close_matches = difflib.get_close_matches(user_input, choice_mapping.keys(), n=3, cutoff=0.6)
        
        if close_matches:
            suggested_option = choice_mapping[close_matches[0]]
            console.print(f"[yellow]Did you mean '{close_matches[0]}' (option [{suggested_option}])?[/yellow]")
            confirmation = input("Press Enter to confirm, or type your choice again: ").strip().lower()
            
            if not confirmation or confirmation == "y" or confirmation == "yes":
                console.print(f"[yellow]Using option [{suggested_option}][/yellow]")
                return suggested_option
        else:
            console.print(f"[bold red]Invalid choice: '{user_input}'[/bold red]")
            console.print(f"Please select from: {', '.join(valid_choices)}")
            console.print("Or use keywords: route, visualize, check, config, exit")

def main():
    """Main function to run the application."""
    while True:
        # Display menu and get user choice
        choice = display_main_menu()
        
        if choice == "0":
            console.print("[yellow]Exiting application. Goodbye![/yellow]")
            break
        
        elif choice == "1":
            # Generate travel route with Gemini
            run_route_generation()
            
        elif choice == "2":
            # Visualize existing route
            visualize_route_data()
            
        elif choice == "3":
            # Check dependencies
            check_dependencies()
        
        elif choice == "4":
            # Configure API settings
            configure_api_settings()
        
        # Pause before showing the menu again
        console.print("\n[italic]Press Enter to return to the main menu...[/italic]")
        input()
        console.clear()

if __name__ == "__main__":
    # Check dependencies on startup
    check_dependencies()
    main() 