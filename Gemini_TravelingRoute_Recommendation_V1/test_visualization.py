#!/usr/bin/env python
"""
Test file for visualizing routes with real paths
"""
import json
import os
from datetime import datetime

try:
    # Try to import our visualization modules
    import visualize_route
    import enhanced_visualization
    from route_validator import validate_route
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Error importing modules: {e}")
    MODULES_AVAILABLE = False

def create_test_route_data():
    """Create a test route data structure for visualization testing"""
    # Origin and destination
    origin = "London"
    destination = "Cambridge"
    mode = "driving"
    
    # Create a basic route data structure
    route_data = {
        "timestamp": datetime.now().isoformat(),
        "query": {
            "origin": origin,
            "destination": destination
        },
        "selected_mode": mode,
        "plan": {
            "weather": {
                "description": "Partly cloudy in Cambridge",
                "temperature": "15°C (59°F)",
                "conditions": "Partly cloudy",
                "recommendation": "Good day for traveling, bring a light jacket"
            },
            "walkability": {
                "score": "85/100",
                "description": "Cambridge is very walkable with many pedestrian-friendly areas",
                "pros": ["Many pedestrian zones", "Good sidewalks", "Beautiful scenery"],
                "disadvantages": ["Some areas with heavy traffic", "Limited accessibility in some historic areas"]
            },
            "transportation_options": [
                {
                    "mode": "driving",
                    "estimated_time": "1.5 - 2 hours",
                    "distance": "~95 km (60 miles)",
                    "cost": "£15-20 for fuel + potential parking fees",
                    "weather_impact": "Good driving conditions",
                    "pros": ["Fastest option", "Flexibility"],
                    "disadvantages": ["Traffic possible", "Parking can be difficult in Cambridge"]
                },
                {
                    "mode": "walking",
                    "estimated_time": "Not practical (~30 hours)",
                    "distance": "~95 km (60 miles)",
                    "cost": "Free",
                    "weather_impact": "Good walking weather, but very long distance",
                    "pros": ["Scenic views", "Exercise"],
                    "disadvantages": ["Not practical for this distance", "Would require multiple days"]
                }
            ]
        }
    }
    
    # Try to validate the route using our validator
    try:
        validation_result = validate_route(origin, destination, mode)
        print(f"Route validation complete. Service status: {validation_result.get('service_status', 'unknown')}")
        
        # Create final route data
        final_route = {
            "route_summary": {
                "mode": mode,
                "origin": origin,
                "destination": destination,
                "total_time": "1.5 - 2 hours",
                "total_distance": "~95 km (60 miles)",
                "weather_advisory": "Good conditions for travel",
                "feasibility_assessment": "This route is fully feasible via public roads"
            },
            "steps": [
                {"number": 1, "instruction": "Start in central London", "distance": "0 km", "time": "0 min", "path_type": "city roads"},
                {"number": 2, "instruction": "Take M11 motorway north", "distance": "80 km", "time": "60 min", "path_type": "highway"},
                {"number": 3, "instruction": "Exit onto A1303", "distance": "10 km", "time": "15 min", "path_type": "regional road"},
                {"number": 4, "instruction": "Follow signs to Cambridge city center", "distance": "5 km", "time": "15 min", "path_type": "city roads"},
                {"number": 5, "instruction": "Arrive in Cambridge", "distance": "0 km", "time": "0 min", "path_type": "city roads"}
            ],
            "recommendations": [
                "Consider using Park & Ride facilities in Cambridge to avoid parking issues",
                "Traffic can be heavy during rush hours (8-9am, 5-6:30pm)"
            ],
            "safety_concerns": [
                "Watch for cyclists in Cambridge city center",
                "Limited visibility if foggy in rural areas"
            ],
            "validation": {
                "is_validated": True,
                "issues": [],
                "alternatives": []
            }
        }
        
        # Add the validation result to the route data
        if "validated_route" in validation_result:
            # Save the geometry from the validation
            route_data["final_route"] = final_route
            route_data["final_route"]["validation"] = {
                "is_validated": validation_result["is_valid"],
                "issues": validation_result["issues"],
                "alternatives": validation_result["alternatives"],
                "validated_route": validation_result["validated_route"]
            }
        else:
            # No validation data available, just use the basic route
            route_data["final_route"] = final_route
        
    except Exception as e:
        print(f"Error during route validation: {e}")
        # Add basic final route without validation
        route_data["final_route"] = {
            "route_summary": {
                "mode": mode,
                "origin": origin,
                "destination": destination,
                "total_time": "1.5 - 2 hours",
                "total_distance": "~95 km (60 miles)",
                "weather_advisory": "Good conditions for travel"
            },
            "steps": [
                {"number": 1, "instruction": "Start in central London", "distance": "0 km", "time": "0 min"},
                {"number": 2, "instruction": "Take M11 motorway north", "distance": "80 km", "time": "60 min"},
                {"number": 3, "instruction": "Exit onto A1303", "distance": "10 km", "time": "15 min"},
                {"number": 4, "instruction": "Follow signs to Cambridge city center", "distance": "5 km", "time": "15 min"},
                {"number": 5, "instruction": "Arrive in Cambridge", "distance": "0 km", "time": "0 min"}
            ]
        }
    
    return route_data

def run_test():
    """Run visualization test"""
    if not MODULES_AVAILABLE:
        print("Required modules not available. Cannot run test.")
        return
    
    print("Creating test route data...")
    route_data = create_test_route_data()
    
    # Save the test data to a file
    test_file = "test_route_data.json"
    with open(test_file, "w") as f:
        json.dump(route_data, f, indent=2)
    print(f"Test route data saved to {test_file}")
    
    # Test basic visualization
    print("\nTesting basic visualization...")
    basic_html = visualize_route.create_html_visualization(route_data, "test_basic_visualization.html")
    print(f"Basic visualization created: {basic_html}")
    
    # Test enhanced visualization
    print("\nTesting enhanced visualization...")
    enhanced_visualization.create_enhanced_visualization(route_data)
    print("Enhanced visualization created")
    
    # Open the visualizations in the browser
    try:
        import webbrowser
        webbrowser.open(os.path.abspath("test_basic_visualization.html"))
        webbrowser.open(os.path.abspath(f"route_{route_data['query']['origin'].replace(' ', '_')}_to_{route_data['query']['destination'].replace(' ', '_')}_map.html"))
    except Exception as e:
        print(f"Could not open visualizations in browser: {e}")

if __name__ == "__main__":
    run_test() 