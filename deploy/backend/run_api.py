#!/usr/bin/env python
"""
Script to start the WanderMatch API server.
This script activates the environment and runs the Flask API server.
"""
import os
import sys
import subprocess

def main():
    """
    Start the Flask API server
    """
    # Determine if we're in production or development
    is_production = os.environ.get('ENVIRONMENT') == 'production'
    
    print(f"Starting WanderMatch API server in {'production' if is_production else 'development'} mode...")
    
    # Set environment variables
    os.environ['FLASK_APP'] = 'app.py'
    
    # Only enable debug mode in development
    if not is_production:
        os.environ['FLASK_DEBUG'] = 'True'
    
    # Use the PORT environment variable from Render in production
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if is_production else '127.0.0.1'
    
    # Log startup information
    print(f"Server will listen on {host}:{port}")
    print(f"API base URL will be: http{'s' if is_production else ''}://{host}:{port}")
    
    # Run the Flask app
    try:
        from app import app
        app.run(host=host, port=port, debug=not is_production)
    except Exception as e:
        print(f"Error starting Flask app: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 