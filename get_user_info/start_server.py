#!/usr/bin/env python
"""
Server Launcher Script

This script ensures that only one server is running at a time,
and specifically launches the main server.py implementation.
"""
import os
import sys
import time
import signal
import subprocess
import platform
import psutil

# Get the current script directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Import utility functions if available
try:
    from embed_info import print_header, print_info, print_success, print_error, print_warning
except ImportError:
    # Fallback simple implementations
    def print_header(text, emoji="✨", color="blue"):
        print(f"\n{emoji} {text} {emoji}")
        print("=" * (len(text) + 10))
        
    def print_info(text, emoji="ℹ️"):
        print(f"{emoji} {text}")
        
    def print_success(text, emoji="✅"):
        print(f"{emoji} {text}")
        
    def print_error(text, emoji="❌"):
        print(f"{emoji} {text}")
        
    def print_warning(text, emoji="⚠️"):
        print(f"{emoji} {text}")

def is_port_in_use(port=5000):
    """Check if the specified port is in use."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            connections = psutil.Process(proc.info['pid']).connections()
            for conn in connections:
                if conn.laddr.port == port:
                    return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False, None

def find_flask_servers():
    """Find running Flask servers."""
    flask_servers = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = proc.info['cmdline']
            if cmd and len(cmd) > 1:
                cmd_str = ' '.join(cmd)
                # Look for Python processes running app.py or server.py
                if (('python' in cmd[0].lower() or 'python3' in cmd[0].lower()) and 
                    ('app.py' in cmd_str or 'server.py' in cmd_str) and
                    'flask' in cmd_str.lower()):
                    server_type = 'Unknown'
                    if 'app.py' in cmd_str:
                        server_type = 'backend/app.py'
                    elif 'server.py' in cmd_str:
                        server_type = 'server.py'
                    
                    flask_servers.append({
                        'pid': proc.info['pid'],
                        'type': server_type,
                        'cmd': cmd_str
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return flask_servers

def stop_server(pid):
    """Stop a server by PID."""
    try:
        if platform.system() == 'Windows':
            # Windows requires a different approach
            subprocess.run(['taskkill', '/F', '/PID', str(pid)])
            return True
        else:
            # Unix-like systems can use signals
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)  # Give it a moment to terminate
            # If it's still running, force kill
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
            return True
    except Exception as e:
        print_error(f"Error stopping server (PID {pid}): {str(e)}")
        return False

def start_server():
    """Start the main server.py implementation."""
    server_path = os.path.join(SCRIPT_DIR, 'server.py')
    
    if not os.path.exists(server_path):
        print_error(f"Server file not found at: {server_path}")
        return False
    
    try:
        # Start server as a subprocess
        print_info(f"Starting server from: {server_path}")
        # Use Popen to avoid blocking
        process = subprocess.Popen([sys.executable, server_path])
        time.sleep(2)  # Give the server a moment to start
        
        # Check if the server started successfully
        port_in_use, new_pid = is_port_in_use(5000)
        if port_in_use:
            print_success(f"Server started successfully on port 5000 (PID: {new_pid})")
            return True
        else:
            print_error("Server failed to start on port 5000")
            return False
    except Exception as e:
        print_error(f"Error starting server: {str(e)}")
        return False

def main():
    print_header("FLASK SERVER MANAGER", emoji="🚀")
    
    # Check if any Flask server is already running
    print_info("Checking for running Flask servers...")
    flask_servers = find_flask_servers()
    
    # Check if the port is in use regardless
    port_in_use, pid = is_port_in_use(5000)
    if port_in_use and pid:
        if pid not in [server['pid'] for server in flask_servers]:
            flask_servers.append({
                'pid': pid,
                'type': 'Unknown (port 5000)',
                'cmd': 'Unknown'
            })
    
    if flask_servers:
        print_warning(f"Found {len(flask_servers)} running Flask server(s):")
        for i, server in enumerate(flask_servers):
            print_info(f"  {i+1}. PID: {server['pid']} - Type: {server['type']}")
            if server['cmd'] != 'Unknown':
                print_info(f"     Command: {server['cmd']}")
                
        print_info("Stopping all running servers...")
        for server in flask_servers:
            if stop_server(server['pid']):
                print_success(f"Stopped server (PID: {server['pid']})")
            else:
                print_error(f"Failed to stop server (PID: {server['pid']})")
    else:
        print_info("No running Flask servers found.")
    
    # Start the server.py implementation
    print_header("STARTING SERVER", emoji="🔄")
    if start_server():
        print_success("Server started successfully.")
        print_info("The correct server (server.py) is now running.")
        print_info("You can access the API at: http://localhost:5000")
        print_info("Press Ctrl+C to stop the script (the server will keep running)")
    else:
        print_error("Failed to start the server.")
        
    try:
        # Keep the script running so it can be easily stopped with Ctrl+C
        print_info("Press Ctrl+C to exit...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_info("\nExiting script (server will continue running in the background)")
        print_info("To stop the server, run this script again or manually kill the process")

if __name__ == "__main__":
    main() 