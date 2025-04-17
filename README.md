# WanderMatch

WanderMatch is an application that helps users find compatible travel companions, generate personalized itineraries, and create travel blogs based on user preferences.

## Features

- **User Profile Creation**: Collect travel preferences and personal information through an interactive survey
- **Partner Matching**: Match users with compatible travel companions using AI-powered similarity analysis
- **Transport Comparison**: Compare different transportation options (flight, train, bus, car) with detailed information on duration, cost, carbon footprint, comfort level, and pros/cons
- **Interactive Maps**: Visualize travel routes with interactive Folium maps showing attractions and travel paths
- **Blog Generation**: Automatically create travel blogs using AI (Gemini or OpenAI) with personalized content based on user profile and travel details
- **Itinerary Planning**: Generate customized travel plans with attractions, route points, and timelines

## Installation

> **Note**: This application requires Python 3.12.9. Please ensure you have this version installed before proceeding.

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/WanderMatch.git
   cd WanderMatch
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up API keys in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_API_KEY=your_google_maps_api_key (optional)
   ```

4. Ensure required directories exist:
   ```
   mkdir -p UserInfo_and_Match/survey_results
   mkdir -p get_user_info/backend
   mkdir -p wandermatch_output/maps
   mkdir -p wandermatch_output/blogs
   ```

## Usage

1. Start the application:
   ```
   python wandermatch.py
   ```

2. Complete the online survey:
   - Navigate to http://localhost:5000 in your browser
   - Fill out your travel preferences and personal information
   - Submit the form to create your profile

3. Select a travel companion or choose to travel solo

4. Enter your origin and destination cities

5. Compare transportation options:
   - View an interactive HTML comparison of different transport modes
   - See details about duration, cost, carbon footprint, and comfort
   - Select your preferred option

6. Review your generated travel route:
   - An interactive map will open in your browser
   - View the route, attractions, and key information
   
7. Explore your personalized travel blog:
   - Read a detailed travel narrative generated by AI
   - The blog adapts to your chosen destination, transport, and travel partner

## Project Structure

```
WanderMatch/
├── wandermatch.py            # Main application entry point
├── get_user_info/            # User survey and information collection
├── UserInfo_and_Match/       # Profile management and matching algorithm
├── map_utils.py              # Map generation with Folium
├── transport.py              # Transportation options comparison
├── route_generator.py        # Travel route planning
├── blog_generator.py         # AI-powered travel blog creation
├── ui_utils.py               # Terminal UI utilities
├── requirements.txt          # Project dependencies
└── wandermatch_output/       # Generated maps, blogs, and visualizations
```

## Transportation Features

The transportation system provides:
- AI-generated transport options using Gemini and OpenAI
- Fallback to default options when APIs are unavailable
- Detailed comparison of transport modes (flight, train, bus, car)
- Interactive HTML visualization with responsive cards
- Color-coded carbon footprint indicators
- Text-based terminal interface with standardized formatting

## Map Visualization

The map generation system offers:
- Interactive Folium maps of travel routes
- Markers for origin, destination, and attractions
- Popup information for key locations
- Clustering of nearby attractions
- Color-coded route lines based on transport mode
- Support for multiple geocoding services

## Blog Generation

The blog creation system features:
- AI-powered blog generation using Gemini or OpenAI
- Templated blog generation as a fallback
- Personalization based on user profile and travel details
- Markdown formatting with structured sections
- Conversion to HTML with styled presentation
- Automatic browser opening to display blogs

## Requirements

- Python 3.12.9 (required)
- OpenAI API key
- Gemini API key
- Google Maps API key (optional, for enhanced geocoding)
- Required packages listed in requirements.txt

## Terminal Output

The application uses straightforward terminal-based output with clear text formatting:
- All console messages use standard print functions with text-based indicators
- Status messages are prefixed with indicators like [INFO], [SUCCESS], [WARNING], etc.
- Tabular data is formatted with basic text alignment
- The system works consistently across all terminal types without special formatting requirements

## Fallback Mechanisms

The application implements robust fallback mechanisms:
- Server-side storage with proper error handling and reporting
- Multiple encoding attempts for CSV files to prevent Unicode errors
- Directory path validation with alternative paths if standard paths are unavailable
- Cascading API services (Gemini → OpenAI → templates)
- Default transport options when API services are unavailable
- Multiple geocoding service options if the primary service fails

## Updates

### Recent Changes
- **Python Version Requirement**: Updated to require Python 3.12.9
- **Terminal Output Simplification**: Removed rich package dependency for better compatibility across different terminals
- **CSV Storage**: Improved server-side storage of survey responses with enhanced error handling
- **Configuration**: Added pyproject.toml for modern Python packaging

## Troubleshooting

- **Server connectivity issues**: Ensure the survey server is running with `python get_user_info/start_server.py`
- **Missing CSV files**: Check server logs and verify directory permissions for survey_results
- **Unicode errors**: Check encoding settings in both server and database connections
- **API connection issues**: Verify API keys and internet connectivity
- **Match quality issues**: Ensure survey completion and check matching algorithm settings
- **Map display problems**: Ensure Folium is properly installed and browser access is available
- **Transport API failures**: The system will automatically use default transport options

## License

This project is licensed under the MIT License - see the LICENSE file for details.