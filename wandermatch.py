#!/usr/bin/env python
"""
WanderMatch: Travel Matchmaking & Route Recommendation Platform

This script integrates all components of WanderMatch:
1. User Profile Creation & Partner Matching
2. Travel Route Generation
3. Blog Post Creation

To run: python wandermatch.py
"""
import os
import sys
from dotenv import load_dotenv

# Import local utility modules
from ui_utils import (
    clear_screen, print_header, print_info, print_success, 
    print_error, print_warning, input_prompt
)

# Import functional modules
from user_management import get_user_info, select_travel_partner
from transport import select_transport_mode
from route_generator import generate_travel_route
from blog_generator import generate_blog_post

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Constants
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check required environment variables
def check_environment():
    """Check for required environment variables."""
    required_keys = [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY"
    ]

    optional_keys = [
        "ORS_API_KEY",
        "GOOGLE_API_KEY"
    ]

    missing_required = [key for key in required_keys if not os.environ.get(key)]
    missing_optional = [key for key in optional_keys if not os.environ.get(key)]
    
    if missing_required:
        print_error(f"Missing required environment variables: {', '.join(missing_required)}")
        print_info("Please add these to your .env file at: " + os.path.join(WORKSPACE_DIR, '.env'))
        return False
    elif missing_optional:
        print_warning(f"Missing optional environment variables: {', '.join(missing_optional)}")
        print_info("Some features may be limited. Add these to your .env file for full functionality.")
        return True
    else:
        print_success("All environment variables loaded successfully.")
        return True

def main():
    """Main function to run the WanderMatch application"""
    clear_screen()
    print_header("WanderMatch", emoji="[TRAVEL]", color="green")
    
    # Check environment variables
    if not check_environment():
        proceed = input_prompt("Continue with limited functionality? (y/n)", default="y")
        if proceed.lower() != "y":
            print_info("Exiting application. Please set up the required environment variables.")
            sys.exit(0)
    
    print_info(" ")
    
    # Get user info
    user_info = get_user_info()
    
    # # Display potential travel partners and let user choose
    # partner_info = select_travel_partner(user_info)
    
    # # Select origin and destination
    # origin_city = input_prompt("Enter your origin city: ")
    # destination_city = input_prompt("Enter your destination city: ")
    
    # # Store these in user_info for later use
    # user_info['origin_city'] = origin_city
    # user_info['destination_city'] = destination_city
    
    # # Select transport mode
    # transport_option = select_transport_mode(origin_city, destination_city)
    
    # # Generate travel route
    # route_info = generate_travel_route(user_info, partner_info, transport_option)
    
    # # Generate blog post
    # blog_result = generate_blog_post(user_info, partner_info, route_info)
    
    # # Create output directories
    # output_dir = os.path.join(WORKSPACE_DIR, "wandermatch_output")
    # blogs_dir = os.path.join(output_dir, "blogs")
    # maps_dir = os.path.join(output_dir, "maps")
    # for directory in [output_dir, blogs_dir, maps_dir]:
    #     os.makedirs(directory, exist_ok=True)
    
    # # Display summary
    # print_header("Your WanderMatch Journey is Ready!", emoji="[SPARKLE]", color="green")
    # print_success(f"Origin: {origin_city}")
    # print_success(f"Destination: {destination_city}")
    # if partner_info:
    #     print_success(f"Travel Partner: {partner_info.get('name', 'Travel Companion')}")
    # else:
    #     print_success("Travel Mode: Solo")
    # print_success(f"Transportation: {transport_option.get('mode', 'Custom')}")
    # print_success(f"Blog saved to: {blog_result.get('html_path', 'wandermatch_output/blogs/')}")
    
    print_info("\nThank you for using WanderMatch! Safe travels!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\nOperation cancelled by user. Exiting...")
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc() 