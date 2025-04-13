# Travel Route Planner - Gemini Powered

A streamlined travel planning application using Google's Gemini API for intelligent route generation and interactive visualization.

## Features

- **Intelligent Route Planning**: Generate optimal routes between any two locations
- **Multiple Transportation Modes**: Support for driving, public transit, walking, and cycling
- **Interactive Visualization**: View routes on interactive maps with animations
- **Location Validation**: Smart validation and correction of location inputs
- **Weather Integration**: Get weather conditions along your route
- **Safety Considerations**: Receive safety advisories for your journey
- **Feasibility Assessment**: Evaluate if routes are physically possible

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/travel-route-planner.git
   cd travel-route-planner
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   - Create a `.env` file in the project root
   - Add your Gemini API key: `GEMINI_API_KEY="your_api_key_here"`

## Usage

Run the application:
```
python main.py
```

### Main Menu Options:
1. **Generate Travel Route**: Plan a new route between two locations
2. **Visualize Existing Route**: View a previously generated route
3. **Check Dependencies**: Verify all required packages are installed
4. **Configure API Settings**: Update your API keys
0. **Exit**: Quit the application

## Required Dependencies

- google-generativeai
- rich
- dotenv
- requests
- folium

## Project Structure

- `main.py`: Main application with user interface
- `RouteGenerator_Hybrid.py`: Core route generation engine
- `visualize_route.py`: Basic route visualization
- `enhanced_visualization.py`: Interactive map visualization
- Generated routes are saved as JSON files (`route_*.json`)

## Obtaining a Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/)
2. Create or sign in to your Google account
3. Get an API key from the API section
4. Add the key to your `.env` file

## License

[MIT License](LICENSE)

## Acknowledgments

- This project uses Google's Gemini API for route generation
- Map visualizations powered by Folium
- Terminal UI created with Rich 