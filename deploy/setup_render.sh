#!/bin/bash
# setup_render.sh - Setup script for Render deployment

set -e  # Exit on error

echo "Setting up WanderMatch for Render deployment..."

# Create required directories
mkdir -p UserInfo_and_Match/survey_results
mkdir -p wandermatch_output/maps
mkdir -p wandermatch_output/blogs

# Ensure directories are writable
chmod -R 777 UserInfo_and_Match
chmod -R 777 wandermatch_output

# Test directory permissions
echo "Testing directory permissions..."
test_file="UserInfo_and_Match/survey_results/test_write.txt"
echo "Write test" > "$test_file"
rm "$test_file"
echo "Directory permissions look good!"

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd deploy/frontend
npm install

echo "Setup complete!" 