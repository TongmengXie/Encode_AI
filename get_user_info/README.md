# WanderMatch - User Information Module

This directory contains the components needed to collect, process, and match user information for the WanderMatch travel partner application. The module handles both collecting new user data via an online survey and matching users with potential travel partners through embedding similarity.

## Code Structure
```
get_user_info/
├── run_info.py              # Main script to launch survey interface
├── embed_info.py            # Embedding calculations and partner matching
├── server.py                # Flask server for survey API endpoints
├── user_pool.csv            # Database of potential travel partners
├── user_pool_embeddings.pkl # Cached embeddings for faster matching
├── user_pool_hash.txt       # Hash to validate cache freshness
├── migrate_user_pool.py     # Helper for migrating user pool data
├── frontend/                # Survey UI components
│   ├── index.html           # Main survey form with travel preferences
│   ├── thank_you.html       # Submission confirmation page
│   ├── scripts.js           # Form handling and submission logic
│   └── styles.css           # Styling for survey interface
├── backend/                 # User answers and recommendation API
│   ├── app.py               # API for recommendations and matching
│   ├── requirements.txt     # Backend dependencies
│   └── user_answer_*.csv    # User survey responses (timestamped)
├── results/                 # Matching results (created during execution)
│   ├── similarity_matrix_*.csv  # Similarity scores between users
│   └── top_matches_*.csv    # Top matched partners based on similarity
└── cache/                   # Additional caching directory
```

## Key Components

### Core Files
- `run_info.py` - Main script to launch the survey interface and collect user responses
- `embed_info.py` - Handles embedding calculations and partner matching using OpenAI embeddings
- `server.py` - Flask server that handles the survey API endpoints
- `user_pool.csv` - Database of potential travel partners for matching
- `migrate_user_pool.py` - Helper script to migrate user pool data if needed

### Directories
- `frontend/` - Contains the survey UI (HTML, CSS, JS)
- `backend/` - Stores user answers and hosts recommendation API
- `results/` - Stores matching results (created when running matching)

## How It Works

### User Data Collection
1. `run_info.py` starts both the frontend and backend servers
2. The frontend displays a survey form with travel preferences
3. User fills out and submits the form
4. The backend saves the responses as a CSV file in `backend/`

### Travel Partner Matching
1. `embed_info.py` loads the user data and the potential partners from `user_pool.csv`
2. It creates embeddings for each user's answers using OpenAI's embedding API
3. Similarity scores are calculated between the user and potential partners
4. The top matches are saved to `results/` and returned to the main application

## Usage

### Running the Survey
1. Start the server using the server management script:
   ```
   cd get_user_info
   python start_server.py
   ```
   
   > **Note**: This is the recommended way to start the server as it ensures only one server is running. 
   > See SERVER_MANAGEMENT.md for more details.
   
   Alternatively, you can still start the server directly:
   ```
   python server.py
   ```
   
2. Open the frontend application in your browser (usually http://localhost:5000)
3. Fill out the survey form and submit

### Running the Matching Only
```bash
python embed_info.py
```
This will:
- Use the most recent user answers from `backend/`
- Calculate embeddings and match scores
- Save results to the `results/` directory
- Display the top matches in the console

## API Endpoints

The backend server provides these endpoints:
- `GET /api/destinations` - Returns suggested destinations 
- `POST /api/submit` - Saves user form data
- `POST /api/recommend` - Returns recommended travel partners based on submitted answers

## CSV File Storage

The application now exclusively uses server-side storage for CSV files. When a user submits the survey:

1. The form data is sent to the server
2. The server validates and processes the data
3. A CSV file is created and saved directly in the `UserInfo_and_Match/survey_results` directory

### Troubleshooting CSV File Storage

If you're having issues with CSV files not being properly saved:

1. Check server logs for error messages during form submission
2. Verify the `UserInfo_and_Match/survey_results` directory exists and has proper write permissions
3. Ensure the Flask server is running correctly using the server management script
   ```
   python start_server.py
   ```
4. Check network connectivity between the client and server during form submission

## Performance Optimizations

- The module caches embeddings to avoid recalculating them for the same user pool
- It supports multiple encoding formats when reading CSV files to prevent Unicode errors
- A fallback mechanism is implemented if API services are unavailable

## Requirements

- Python 3.8+
- OpenAI API key (set in `.env` file in parent directory)
- Required packages:
  - `pandas`
  - `numpy`
  - `openai`
  - `flask`
  - `flask-cors`
  - `rich` (optional, for prettier console output)

## File Paths

The application uses the following directory paths:

- Backend directory: `get_user_info/backend/`
- Survey results directory: `UserInfo_and_Match/survey_results/`

## Troubleshooting

### Survey System Issues
- If the survey doesn't load, check that ports 5000 and 8000 are available
- Unicode errors when reading files can be resolved by using the correct encoding (the system tries multiple encoding formats)
- If embedding calculation fails, check your OpenAI API key and internet connection

### Network Connectivity Issues
If there are problems connecting to the server:
1. Check that the server is running and accessible (verify with a simple GET request to http://localhost:5000)
2. Ensure there are no firewall or network restrictions blocking the connection
3. Restart the server with the server management script
   ```
   python start_server.py
   ```
4. If persistent issues occur, check the server logs for error messages

### Encoding Issues
If you encounter issues with Unicode characters in console output:
- This is a known issue on Windows systems with certain terminal encodings
- The application has fallback mechanisms to handle these cases
- You can still use the application normally despite encoding warnings

## Testing

Several test scripts are provided to verify system functionality:

- `test_encoding.py`: Tests Unicode handling in CSV files
- `test_server_flag.py`: Tests the save_on_server flag functionality
- `fix_paths.py`: Verifies path settings and creates test files
- `sync_csv.py`: Synchronizes CSV files between directories
- `final_test.py`: Comprehensive test of form submission and file saving

# WanderMatch Survey System

This system collects and processes survey information from users and helps match them with potential travel companions.

## Setup

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:
   ```
   pip install flask flask-cors pandas python-dotenv openai
   ```
3. Make sure the directory structure is set up correctly:
   ```
   /your_project_root/
     ├── get_user_info/
     │   ├── server.py
     │   ├── backend/
     │   └── frontend/
     └── UserInfo_and_Match/
         └── survey_results/
   ```

## Usage

1. Start the server:
   ```
   cd get_user_info
   python server.py
   ```
2. Open the frontend application in your browser (usually http://localhost:5000)
3. Fill out the survey form and submit

## CSV File Storage

The application supports two methods of CSV storage:

1. **Client-side generation**: The form data is converted to CSV in the browser and downloaded to your Downloads folder.
2. **Server-side storage**: The form data is sent to the server and saved in the `UserInfo_and_Match/survey_results` directory.

### Troubleshooting CSV File Storage

If you're having issues with CSV files not being properly saved:

1. **Check client-side generated CSV**: Look in your Downloads folder for a file named `user_answer_TIMESTAMP.csv`.
2. **Manually copy CSV**: Copy this file to the `UserInfo_and_Match/survey_results` directory.
3. **Run the synchronization script**: This will copy CSV files between directories.
   ```
   python sync_csv.py
   ```

## Testing

Several test scripts are provided to verify system functionality:

- `test_encoding.py`: Tests Unicode handling in CSV files
- `test_server_flag.py`: Tests the save_on_server flag functionality
- `fix_paths.py`: Verifies path settings and creates test files
- `sync_csv.py`: Synchronizes CSV files between directories
- `final_test.py`: Comprehensive test of form submission and file saving

## File Paths

The application uses the following directory paths:

- Backend directory: `get_user_info/backend/`
- Survey results directory: `UserInfo_and_Match/survey_results/`

## Troubleshooting

If you encounter issues with Unicode characters in console output:
- This is a known issue on Windows systems with certain terminal encodings
- The application has fallback mechanisms to handle these cases
- You can still use the application normally despite encoding warnings

If CSV files are not appearing in the expected directory:
1. Run `sync_csv.py` to locate and copy files between directories
2. Check both the backend and survey_results directories
3. Manually copy any CSV files from your Downloads folder to the survey_results directory 