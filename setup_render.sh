#!/bin/bash
# setup_render.sh - Setup script for Render deployment

# Don't exit on error when running on Windows
if [[ "$OSTYPE" != "msys"* ]] && [[ "$OSTYPE" != "win"* ]] && [[ "$OSTYPE" != "cygwin"* ]]; then
  set -e  # Exit on error - only for Linux/Mac
fi

echo "Setting up WanderMatch for Render deployment..."
echo "Detected OS: $OSTYPE"

# Create required directories
mkdir -p UserInfo_and_Match/survey_results
mkdir -p wandermatch_output/maps
mkdir -p wandermatch_output/blogs

# Ensure directories are writable (skip chmod on Windows)
if [[ "$OSTYPE" != "msys"* ]] && [[ "$OSTYPE" != "win"* ]] && [[ "$OSTYPE" != "cygwin"* ]]; then
  echo "Setting directory permissions (Linux/Mac)..."
  chmod -R 777 UserInfo_and_Match
  chmod -R 777 wandermatch_output
else
  echo "Skipping chmod (not needed on Windows)"
  # On Windows, permissions are managed differently
  # No equivalent command needed
fi

# Test directory permissions
echo "Testing directory permissions..."
test_file="UserInfo_and_Match/survey_results/test_write.txt"
echo "Write test" > "$test_file"
if [ -f "$test_file" ]; then
  echo "Successfully created test file"
  rm "$test_file"
  echo "Successfully removed test file"
  echo "Directory permissions look good!"
else
  echo "WARNING: Could not create test file. Check permissions manually."
fi

# Copy survey HTML files to the frontend public directory
echo "Copying HTML files to frontend directory..."
mkdir -p deploy/frontend/public
cp test_survey_form.html deploy/frontend/public/ 2>/dev/null || echo "Warning: test_survey_form.html not found"
cp survey_launcher.html deploy/frontend/public/ 2>/dev/null || echo "Warning: survey_launcher.html not found"

echo "Setup complete!"
echo "Note: This script will work correctly on Render regardless of your local OS." 