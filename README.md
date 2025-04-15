# WanderMatch: Travel Partner Matching & Route Planning

WanderMatch is an AI-powered travel platform that helps users find compatible travel companions, generate personalized travel routes, and create shareable blog posts about their journeys.

## Features

1. **User Profile Creation** - Create a traveler profile with your preferences and travel interests
2. **Partner Matching** - Find ideal travel companions using semantic embeddings with cached user pools
3. **Route Generation** - Get personalized travel routes based on your preferences and destination
4. **Blog Generation** - Generate shareable travel blog posts with highlights of your journey
5. **Interactive HTML Maps** - Visualize your travel routes with interactive maps
6. **Transport Comparison** - Compare different transport options with detailed pros and cons

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wandermatch.git
cd wandermatch
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following API keys:
```
OPENAI_API_KEY=your_openai_api_key        # Required for embeddings and route generation
GEMINI_API_KEY=your_gemini_api_key        # Required for content generation
PORTIA_API_KEY=your_portia_api_key        # Required for blog post generation
ORS_API_KEY=your_ors_api_key              # Required for mapping services
GOOGLE_API_KEY=your_google_api_key        # Required for places API
```

4. Create required directories for outputs:
```bash
mkdir -p get_user_info/results wandermatch_output/maps wandermatch_output/blogs
```

## Usage

### Running the Application

To run the complete WanderMatch platform:

```bash
python wandermatch.py
```

This will:
1. Guide you through creating your travel profile (via web survey or terminal input)
2. Find your ideal travel partner using cached embeddings for efficiency
3. Generate a personalized travel route based on your preferences
4. Create a travel blog post markdown file that you can share
5. Visualize transport options with an interactive HTML display

### Online Survey

The application launches a web server to collect user information through a friendly online form:

1. A Flask server starts on port 5000 to handle form submissions
2. A simple HTTP server starts on port 8000 to serve the survey form
3. Your browser opens to display the form (or you can navigate to http://localhost:8000)
4. After completing the form, you'll see a thank you page
5. Return to the terminal and press Enter to continue

### Travel Partner Selection Process

The partner matching system works through:

1. **Embedding Generation**: User answers are converted to vector embeddings using OpenAI's API
2. **Similarity Calculation**: Cosine similarity measures compatibility between user vectors
3. **Weighted Matching**: Different profile attributes are weighted by importance
4. **Partner Recommendation**: Top matches are displayed with compatibility scores
5. **Manual Selection**: Users can choose a partner or travel solo

### Transport Options

The transport comparison system:

1. Attempts to generate options using Gemini or OpenAI
2. Falls back to predefined routes if API generation fails
3. Creates an interactive HTML visualization of options
4. Displays a comparison table in the terminal
5. Allows selection of preferred transport mode

### Cached Embeddings

To improve performance, WanderMatch caches user pool embeddings. The system:

1. Checks for existing cached embeddings in the `user_pool_embeddings.pkl` file
2. Validates cache with a hash of the current user pool (`user_pool_hash.txt`)
3. Only recalculates embeddings when the user pool changes
4. Stores embeddings in the `/get_user_info/` directory

### Output Files

The application generates several output files:

1. **User Answers**: Stored in `/get_user_info/backend/` with timestamp-based filenames
2. **Similarity Matrices**: Generated in `/get_user_info/results/` with timestamp
3. **Top Matches**: Partner matching results saved in `/get_user_info/results/`
4. **Route Maps**: Interactive maps saved in `/wandermatch_output/maps/`
5. **Blog Posts**: Generated blogs saved in `/wandermatch_output/blogs/`
6. **Transport Options**: Interactive HTML comparison in `/wandermatch_output/`

## Project Structure

```
wandermatch/
├── wandermatch.py           # Main application file
├── utils.py                 # Utility functions for formatting and file handling
├── get_user_info/           # User profile collection module
│   ├── embed_info.py        # OpenAI embedding and semantic matching logic
│   ├── user_pool.csv        # Database of potential travel partners
│   ├── user_pool_embeddings.pkl # Cached embeddings for faster matching
│   ├── user_pool_hash.txt   # Hash to validate cache freshness
│   ├── server.py            # Flask server for online survey and recommendations
│   ├── run_info.py          # Frontend launcher and server manager
│   ├── results/             # Directory for similarity and matching results
│   ├── frontend/            # Web interface files
│   │   ├── index.html       # Survey form with responsive design
│   │   ├── thank_you.html   # Submission confirmation page
│   │   ├── scripts.js       # Frontend functionality and validation
│   │   └── styles.css       # CSS styling for user interface
│   └── backend/             # Survey response storage
│       ├── app.py           # API for recommendations and vector matching
│       └── user_answer_*.csv # User responses with timestamp
├── wandermatch_output/      # Generated output files
│   ├── maps/                # Interactive travel route maps
│   ├── blogs/               # Generated travel blog posts in HTML and markdown
│   └── transport_options.html # Transport comparison visualization
├── .env                     # Environment variables and API keys
├── requirements.txt         # Python package dependencies
└── README.md                # This file
```

## Requirements

- Python 3.8+
- OpenAI API Key (for embeddings and content generation)
- Gemini API Key (for route generation)
- Portia API Key (for blog generation)
- ORS API Key (for mapping)
- Google API Key (for places and maps)
- Internet connection

## Fallback Mechanisms

WanderMatch includes robust fallback mechanisms:
1. If API-based partner matching fails, it falls back to using the local user pool
2. If all recommendation systems fail, it provides default travel partners
3. For transport options, predefined routes are available when API calls fail
4. Route generation can work with minimal location data if detailed preferences are unavailable
5. Multiple encoding strategies are tried when handling CSV files

## Troubleshooting

### Encoding Issues
If you encounter encoding errors, particularly on Windows systems:
- The application now handles multiple encodings (UTF-8, ISO-8859-1, CP1252)
- CSV files are explicitly saved with UTF-8 encoding
- Any problematic characters during file operations are gracefully handled with replacements
- Subprocess calls use `errors='replace'` to prevent crashes on unusual characters

### JSON Parsing Errors
If route generation fails due to malformed JSON:
- The application includes enhanced JSON repair logic
- Multiple parsing attempts are made with progressive fixes
- The system will fall back to default route generation if all parsing attempts fail

### API Connectivity
If API requests fail:
- Check your internet connection
- Verify API keys in your `.env` file
- Ensure no firewalls are blocking API requests
- The application will automatically use fallback mechanisms for core functionality

### Common Error Messages
- **"No user answer files found"**: Run the survey first using `python -c "from get_user_info import run_info; run_info.main()"`
- **"Embeddings cache not found"**: This is normal on first run, embeddings will be calculated
- **"Error parsing JSON response"**: The AI service returned malformed data, the app will use fallbacks

## Running Individual Components

You can run specific components separately:

```bash
# Run just the user survey and matching
python -c "from get_user_info import run_info; run_info.main()"

# Generate embeddings for user pool
python -c "from get_user_info import embed_info; embed_info.main()"

# Test transport mode generation
python -c "import wandermatch; wandermatch.select_transport_mode('London', 'Paris')"

# Generate a route between two cities
python -c "import wandermatch; user_info={'name':'Test User'}; wandermatch.generate_travel_route(user_info, None, {'mode':'Train'})"
```

## License

MIT License
