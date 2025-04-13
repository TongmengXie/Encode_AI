#!/usr/bin/env python
"""
Route Generator using a hybrid approach:
- Portia-like planning and execution structure
- Gemini for the actual processing (free API)
"""
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Import our route validator
try:
    from route_validator import validate_route, add_validation_to_env
    VALIDATOR_AVAILABLE = True
    # Add API key to .env if not present
    add_validation_to_env()
except ImportError:
    print("Route validator not available. Routes will not be validated against real maps.")
    VALIDATOR_AVAILABLE = False

class RouteGenerator:
    """Class to manage route generation and user clarification."""
    
    def __init__(self, model_name='gemini-1.5-pro'):
        """Initialize with a specific Gemini model."""
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
    
    def generate_route_plan(self, origin, destination):
        """Generate a travel route plan using Gemini."""
        print(f"\nGenerating route plan from {origin} to {destination}...")
        
        planning_prompt = f"""
        Plan a trip from {origin} to {destination}. 
        
        Create a detailed multi-step plan with the following sections:
        
        1. Weather Analysis: Check and describe the current weather conditions in {destination}
        2. Walkability Assessment: Evaluate how walkable {destination} is
        3. Transportation Options: Calculate and compare travel times for different methods:
           - Driving (use only public roads and highways)
           - Walking (use only pedestrian paths and walkways)
           - Public Transit (use only existing public transportation routes)
           - Biking (use only bike-friendly roads and dedicated bike paths)
        
        IMPORTANT: Ensure that all routes follow REAL physical paths and roads. 
        Do not suggest routes that would be physically impossible or unsafe.
        For example:
        - Bike routes should only use roads suitable for cycling
        - Walking routes should only use pedestrian paths
        - Driving routes should only use public roads
        - All routes should avoid restricted areas and private property

        Your response should be in JSON format with the following structure:
        {{
            "weather": {{
                "description": "Current weather in {destination}",
                "temperature": "Temperature in Celsius and Fahrenheit",
                "conditions": "Weather conditions (sunny, rainy, etc.)",
                "recommendation": "Weather-based recommendation"
            }},
            "walkability": {{
                "score": "Estimated walkability score (0-100)",
                "description": "Description of walkability factors",
                "pros": ["list", "of", "pros"],
                "cons": ["list", "of", "cons"]
            }},
            "transportation_options": [
                {{
                    "mode": "driving",
                    "estimated_time": "Estimated travel time",
                    "distance": "Estimated distance",
                    "cost": "Estimated cost",
                    "weather_impact": "How weather affects this mode",
                    "pros": ["list", "of", "pros"],
                    "cons": ["list", "of", "cons"],
                    "feasibility": "Assessment of route feasibility with this mode"
                }},
                // Repeat for walking, public transit, and biking
            ]
        }}
        
        Return ONLY the JSON with no additional text.
        """
        
        try:
            response = self.model.generate_content(
                planning_prompt,
                generation_config={
                    "max_output_tokens": 1500,
                    "temperature": 0.2,
                }
            )
            
            # Extract JSON from the response
            plan_text = response.text.strip()
            if plan_text.startswith("```json"):
                plan_text = plan_text.split("```json")[1]
            if "```" in plan_text:
                plan_text = plan_text.split("```")[0]
                
            plan = json.loads(plan_text.strip())
            
            # Print the plan
            print("\nGenerated Route Plan:")
            print(json.dumps(plan, indent=2))
            
            return plan
        except Exception as e:
            print(f"Error generating plan: {e}")
            # Return a simplified error plan
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_user_choice(self, transportation_options):
        """Present transportation options to the user and get their choice."""
        print("\n---- TRANSPORTATION OPTIONS ----")
        
        for option in transportation_options:
            mode = option["mode"]
            print(f"\n{mode.upper()}:")
            print(f"  Time: {option['estimated_time']}")
            print(f"  Distance: {option['distance']}")
            print(f"  Cost: {option['cost']}")
            print(f"  Weather Impact: {option['weather_impact']}")
            print("  Pros:")
            for pro in option["pros"]:
                print(f"    - {pro}")
            print("  Cons:")
            for con in option["cons"]:
                print(f"    - {con}")
        
        valid_choices = [opt["mode"].lower() for opt in transportation_options]
        
        while True:
            choice = input(f"\nPlease select your preferred transportation mode ({', '.join(valid_choices)}): ").lower()
            if choice in valid_choices:
                return choice
            else:
                print(f"Invalid choice. Please select one of: {', '.join(valid_choices)}")
    
    def generate_final_route(self, plan, selected_mode, origin, destination):
        """Generate a final route based on the selected transportation mode."""
        print(f"\nGenerating detailed route for {selected_mode.upper()} from {origin} to {destination}...")
        
        # Find the selected transportation option
        selected_option = None
        for option in plan["transportation_options"]:
            if option["mode"].lower() == selected_mode.lower():
                selected_option = option
                break
        
        if not selected_option:
            print(f"Error: Could not find transportation mode '{selected_mode}' in the plan.")
            return None
            
        # Check if route is feasible
        if "feasibility" in selected_option and "not feasible" in selected_option["feasibility"].lower():
            print(f"Warning: This {selected_mode} route may not be feasible: {selected_option['feasibility']}")
            proceed = input("Do you want to proceed anyway? (y/n): ").lower()
            if proceed != 'y':
                print("Route generation cancelled. Please select a different transportation mode.")
                return None
        
        # Validate route with the route validator if available
        validation_result = {"is_valid": True, "issues": [], "alternatives": []}
        if VALIDATOR_AVAILABLE:
            print(f"Validating route using mapping service...")
            validation_result = validate_route(origin, destination, selected_mode)
            
            # If validation shows issues, warn the user
            if not validation_result["is_valid"]:
                print("\nWARNING: Route validation detected issues:")
                for issue in validation_result["issues"]:
                    print(f"- {issue}")
                
                if validation_result["alternatives"]:
                    print("\nSuggested alternatives:")
                    for alt in validation_result["alternatives"]:
                        print(f"- {alt}")
                
                proceed = input("\nDo you want to proceed with generating this route anyway? (y/n): ").lower()
                if proceed != 'y':
                    print("Route generation cancelled.")
                    return None
        
        # Generate detailed route
        route_prompt = f"""
        Generate a detailed route for traveling from {origin} to {destination} via {selected_mode}.
        
        Transportation details:
        - Mode: {selected_mode}
        - Estimated time: {selected_option['estimated_time']}
        - Distance: {selected_option['distance']}
        - Weather conditions: {plan['weather']['description']}
        
        IMPORTANT: The route MUST follow REAL physical paths and roads. 
        Ensure all directions are based on actual geography and infrastructure:
        - For driving: Use only public roads accessible by car
        - For walking: Use only pedestrian-accessible paths and walkways
        - For biking: Use only bike-friendly roads and dedicated bike paths
        - For public transit: Use only actual transit lines and stations that exist

        Provide a step-by-step route with:
        1. Starting point details (specific location)
        2. Major waypoints or turns (with road/path names)
        3. Key landmarks along the way (to help with navigation)
        4. Arrival details (specific location)
        5. Recommended stops or points of interest
        6. Safety tips considering the current weather
        7. Validation notes about route feasibility
        
        Your response should be in JSON format with the following structure:
        {{
            "route_summary": {{
                "mode": "{selected_mode}",
                "origin": "{origin}",
                "destination": "{destination}",
                "total_time": "Estimated total time",
                "total_distance": "Total distance",
                "weather_advisory": "Any weather-related advisory",
                "feasibility_assessment": "Assessment of whether this route is physically possible"
            }},
            "steps": [
                {{
                    "number": 1,
                    "instruction": "Step instruction with specific road/path names",
                    "distance": "Distance for this step",
                    "time": "Time for this step",
                    "path_type": "Type of path (road, highway, bike lane, footpath, etc.)",
                    "notes": "Any additional notes"
                }},
                // Additional steps...
            ],
            "recommendations": [
                "Recommendation 1",
                "Recommendation 2",
                // Additional recommendations...
            ],
            "safety_concerns": [
                "Safety concern 1",
                "Safety concern 2"
            ],
            "validation": {{
                "is_validated": {str(validation_result["is_valid"]).lower()},
                "issues": {json.dumps(validation_result["issues"])},
                "alternatives": {json.dumps(validation_result["alternatives"])}
            }}
        }}
        
        Return ONLY the JSON with no additional text.
        """
        
        try:
            response = self.model.generate_content(
                route_prompt,
                generation_config={
                    "max_output_tokens": 1500,
                    "temperature": 0.2,
                }
            )
            
            # Extract JSON from the response
            route_text = response.text.strip()
            if route_text.startswith("```json"):
                route_text = route_text.split("```json")[1]
            if "```" in route_text:
                route_text = route_text.split("```")[0]
                
            route = json.loads(route_text.strip())
            return route
        except Exception as e:
            print(f"Error generating route: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def save_results(self, plan, selected_mode, final_route, origin, destination):
        """Save the complete results to a file."""
        # Validate route before saving
        validation_warnings = []
        
        # Check if route validation data exists
        if "validation" in final_route:
            # If the route is not validated, add warnings
            if not final_route["validation"].get("is_validated", True):
                validation_warnings = final_route["validation"].get("issues", [])
                print("\n[WARNING] This route has validation issues:")
                for warning in validation_warnings:
                    print(f"- {warning}")
                
                # If alternatives exist, suggest them
                alternatives = final_route["validation"].get("alternatives", [])
                if alternatives:
                    print("\nSuggested alternatives:")
                    for alt in alternatives:
                        print(f"- {alt}")
                
                # Ask if user wants to save anyway
                proceed = input("\nDo you want to save this route anyway? (y/n): ").lower()
                if proceed != 'y':
                    print("Save cancelled.")
                    return None
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "query": {
                "origin": origin,
                "destination": destination
            },
            "plan": plan,
            "selected_mode": selected_mode,
            "final_route": final_route,
            "validation_warnings": validation_warnings
        }
        
        filename = f"route_{origin.replace(' ', '_')}_to_{destination.replace(' ', '_')}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filename}")
        return filename

def main():
    """Main function to demonstrate route generation."""
    # Create the route generator
    generator = RouteGenerator()
    
    # Get origin and destination from user
    print("=== ROUTE GENERATOR WITH GEMINI ===")
    origin = input("Enter origin location: ")
    destination = input("Enter destination location: ")
    
    if not origin or not destination:
        # Default values for demonstration
        origin = "San Francisco, CA"
        destination = "Palo Alto, CA"
        print(f"\nUsing default locations: {origin} to {destination}")
    
    # Generate route plan
    plan = generator.generate_route_plan(origin, destination)
    
    if "error" in plan:
        print(f"\nError: {plan['error']}")
        return
    
    # Get user's transportation choice
    selected_mode = generator.get_user_choice(plan["transportation_options"])
    print(f"\nYou selected: {selected_mode.upper()}")
    
    # Generate final route based on selection
    final_route = generator.generate_final_route(plan, selected_mode, origin, destination)
    
    if final_route:
        print("\n====== DETAILED ROUTE ======")
        print(json.dumps(final_route, indent=2))
        
        # Save results
        filename = generator.save_results(plan, selected_mode, final_route, origin, destination)
        print(f"\nRoute generation complete! Results saved to {filename}")
    else:
        print("\nRoute generation failed. Please try again.")

if __name__ == "__main__":
    main() 