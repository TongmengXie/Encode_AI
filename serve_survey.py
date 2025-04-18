#!/usr/bin/env python
"""
Simple HTTP Server to serve the WanderMatch Survey pages.
This allows testing the workflow without needing to deploy to a web server.
"""
import http.server
import socketserver
import webbrowser
import os
import threading
import time
import subprocess
import sys
import signal
import json

# Configure servers
FRONTEND_PORT = 8000
BACKEND_PORT = 5000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Global variable to track the backend process
backend_process = None

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        # Override to provide cleaner console output
        print(f"[FRONTEND] {self.client_address[0]} - {format % args}")
    
    def end_headers(self):
        """Add cache control headers before ending the headers."""
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_POST(self):
        """Handle POST requests - specifically for shutdown command."""
        if self.path == '/shutdown':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'message': 'Server shutting down...'}).encode())
            
            # Start a thread that will shut down the server after a short delay
            threading.Thread(target=shutdown_servers, daemon=True).start()
            return
        
        # For any other POST requests, return 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found')

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)  # Increased delay to ensure backend is up
    timestamp = int(time.time())  # Add timestamp for cache busting
    url = f"http://localhost:{FRONTEND_PORT}/survey_launcher.html?cb={timestamp}"
    print(f"Opening browser to {url}")
    webbrowser.open(url)

def start_backend_server():
    """Start the Flask backend server"""
    global backend_process
    
    # Path to the backend app.py file
    backend_path = os.path.join(DIRECTORY, "deploy", "backend", "app.py")
    
    # Check if backend exists
    if not os.path.exists(backend_path):
        print(f"Warning: Backend file not found at {backend_path}")
        print("The survey submission and embedding calculation will not work.")
        return
    
    print(f"Starting Flask backend server on port {BACKEND_PORT}...")
    
    # Set environment variables for Flask
    env = os.environ.copy()
    env["FLASK_APP"] = backend_path
    env["PORT"] = str(BACKEND_PORT)
    env["FLASK_DEBUG"] = "True"
    
    # Start the Flask server as a subprocess
    try:
        backend_process = subprocess.Popen(
            [sys.executable, backend_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Start a thread to monitor and log the backend output
        threading.Thread(target=monitor_backend_output, daemon=True).start()
        
        print(f"Backend server started with PID: {backend_process.pid}")
    except Exception as e:
        print(f"Error starting backend server: {str(e)}")

def monitor_backend_output():
    """Monitor and log backend server output"""
    global backend_process
    
    if not backend_process:
        return
        
    while True:
        line = backend_process.stdout.readline()
        if not line and backend_process.poll() is not None:
            break
        if line:
            print(f"[BACKEND] {line.strip()}")

def cleanup():
    """Clean up resources before exiting"""
    global backend_process
    
    if backend_process:
        print("Stopping backend server...")
        # Try to terminate gracefully first
        if sys.platform == 'win32':
            # On Windows
            backend_process.terminate()
        else:
            # On Unix-like systems
            os.kill(backend_process.pid, signal.SIGTERM)
            
        # Give it some time to terminate gracefully
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Backend server did not terminate gracefully, forcing...")
            backend_process.kill()
            
        print("Backend server stopped.")

def shutdown_servers():
    """Shut down all servers after a short delay."""
    time.sleep(0.5)  # Short delay to allow the response to be sent
    
    # First shut down backend if it's running
    cleanup()
    
    # Then shut down the HTTP server
    print("Shutting down frontend server...")
    httpd.shutdown()

if __name__ == "__main__":
    # Change to the directory containing the script
    os.chdir(DIRECTORY)
    
    # Start the backend server first
    start_backend_server()
    
    # Create the frontend server
    handler = MyHandler
    httpd = socketserver.TCPServer(("", FRONTEND_PORT), handler)
    
    print(f"Serving frontend at http://localhost:{FRONTEND_PORT}")
    print(f"To open the survey launcher, visit: http://localhost:{FRONTEND_PORT}/survey_launcher.html")
    print("Press Ctrl+C to stop all servers")
    
    # Open browser automatically
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        # Start the frontend server
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    finally:
        httpd.server_close()
        cleanup() 