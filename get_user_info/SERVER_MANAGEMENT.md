# Server Management

This document explains how to properly manage the WanderMatch survey server to ensure consistent operation.

## Background

The project contains two server implementations:

1. **Main Server (`server.py`)** - The primary server that should be used. This server:
   - Saves survey results to `UserInfo_and_Match/survey_results/`
   - Handles form submissions and data validation
   - Provides error handling and reporting

2. **Legacy Server (`backend/app.py`)** - An older implementation that should not be used. This server:
   - Saves survey results to `get_user_info/backend/`
   - Uses an outdated data structure
   - Has limited error handling capabilities

Having both servers running simultaneously can cause issues with file paths and inconsistent behavior.

## Solution: Server Manager Script

The `start_server.py` script ensures that:
- Only one server is running at a time
- Specifically, the main `server.py` implementation is used

## Prerequisites

The script requires the `psutil` library:

```
pip install psutil
```

## Usage

### Starting the Server

1. Run the server manager script:

```
cd get_user_info
python start_server.py
```

2. The script will:
   - Check for any running Flask servers (including both `server.py` and `backend/app.py`)
   - Stop all running servers to avoid conflicts
   - Start the main `server.py` implementation
   - Keep running to allow for easy termination with Ctrl+C

### Stopping the Server

You can stop the server in two ways:

1. Run the script again - it will stop any running servers before starting a new one
2. Use your operating system's task manager to find and terminate the Python process running `server.py`

## Troubleshooting

### Port Already in Use

If you see an error about port 5000 being in use:

1. Run the server manager script, which will attempt to stop any processes using that port
2. If the issue persists, try changing the port in `server.py` (around line 173) to a different value like 5001

### Server Not Responding

If the server is not responding to requests:

1. Stop all servers using the script
2. Check for error messages in the console
3. Ensure that the `UserInfo_and_Match/survey_results/` directory exists and is writable
4. Restart the server with the script

### File Path Issues

If files are being saved to the wrong location:

1. Ensure you're using the main `server.py` server (run through the server manager script)
2. Check the .env file for any custom `PROJECT_PATH` settings
3. Verify that the `UserInfo_and_Match/survey_results/` directory exists and has proper permissions
4. Run the `test_survey_paths.py` script to test the file paths

## Testing the Server

After starting the server with the manager script, you can test it with:

```
python test_survey_paths.py
```

This will verify that:
1. Files are saved to the correct location
2. The embed_info.py module can find the saved files 