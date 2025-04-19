# WanderMatch React Deployment

This is a React-based deployment of the WanderMatch application.

## Prerequisites

1. Python 3.12+ with the following packages:
   - Flask
   - Flask-CORS
   - pandas
   - requests

2. Node.js 14+ (npm is not required as we use npx)

## Project Structure

```
deploy/
├── backend/            # Flask API backend
│   ├── app.py          # Main Flask application
│   ├── run_api.py      # Helper script to start the API
│   └── test_api.py     # Test script for API endpoints
├── frontend/           # React frontend
│   ├── public/         # Static assets
│   ├── src/            # React source code
│   │   ├── assets/     # Image assets
│   │   ├── components/ # React components
│   │   └── types/      # TypeScript type definitions
│   ├── .env            # Environment variables
│   └── package.json    # Frontend dependencies
├── package.json        # Root package.json for scripts
├── run_deployment.py   # Main deployment script
└── verify_setup.py     # Verification script
```

## Quick Start

### Step 1: Verify Setup

Run the verification script to check if all required dependencies and files are present:

```bash
cd deploy
python verify_setup.py
```

Install any missing dependencies as indicated by the verification script.

### Step 2: Run the Deployment

Simply run the deployment script:

```bash
python run_deployment.py
```

This will:
1. Check your environment
2. Install necessary frontend dependencies
3. Start the backend Flask API
4. Start the React frontend development server
5. Open your browser to the application

## Manual Setup (if needed)

### 1. Install Backend Dependencies

```bash
conda activate myenv
pip install flask flask-cors pandas requests
```

### 2. Start the Backend Manually

```bash
cd deploy/backend
python app.py
```

### 3. Start the Frontend Manually

```bash
cd deploy/frontend
npx npm install  # Install dependencies
npx npm start    # Start the development server
```

## Troubleshooting

### Common Issues

1. **Node.js not found**
   - Install Node.js from https://nodejs.org/
   - Make sure it's in your PATH
   - Verify with `node --version`

2. **Python package missing**
   - Install missing packages with pip:
   - `pip install flask flask-cors pandas requests`

3. **Survey data not saving**
   - Check the console output for the path where data is being saved
   - Ensure the directory exists and is writable
   - The backend tries to save to the original location at `../../UserInfo_and_Match/survey_results`

4. **Frontend dependency errors**
   - If you see TypeScript errors about missing modules:
   - Delete the `node_modules` folder in the frontend directory
   - Run `npx npm install` again

## Using the Application

1. Open your browser to `http://localhost:3000`
2. You'll see the landing page with a "Launch Survey" button
3. Click the button to access the survey form
4. Fill out your travel preferences
5. Submit the form to save your data
6. After submission, you'll be returned to the landing page with a "Calculate Travel Match" button

## API Endpoints

- `GET /api/health` - Health check endpoint
- `POST /api/survey` - Save survey responses 