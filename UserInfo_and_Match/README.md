# User Information and Matching System

This directory contains the core user profile management and travel companion matching functionality for the WanderMatch application.

## Overview

The User Information and Matching system is responsible for:
1. Collecting and storing user survey responses
2. Processing user travel preferences and demographics
3. Implementing the matching algorithm to pair compatible travel companions
4. Managing user profiles and match history
5. Providing data interfaces for other application components

## Directory Structure

```
UserInfo_and_Match/
├── matching_algorithm/        # Travel companion matching system
│   ├── match_engine.py        # Core matching logic
│   ├── compatibility.py       # Compatibility scoring functions
│   ├── filters.py             # Pre-filtering of potential matches
│   └── weightings.json        # Configuration for attribute importance
├── user_profiles/             # User profile management
│   ├── profile_manager.py     # Profile creation and update functions
│   ├── validators.py          # Input validation for user data
│   └── anonymizer.py          # Privacy protection utilities
├── survey_processing/         # Survey data handling
│   ├── processor.py           # Survey response processing
│   ├── normalization.py       # Data normalization functions
│   └── analytics.py           # Survey response analytics
├── database/                  # Database interfaces
│   ├── schemas/               # Database schema definitions
│   │   ├── users.sql          # User table schema
│   │   ├── preferences.sql    # User preferences schema
│   │   ├── matches.sql        # Match records schema
│   │   └── feedback.sql       # Match feedback schema
│   ├── migrations/            # Database migration scripts
│   └── db_connector.py        # Database connection handling
├── api/                       # Internal API endpoints
│   ├── user_endpoints.py      # User profile endpoints
│   ├── match_endpoints.py     # Match-related endpoints
│   └── survey_endpoints.py    # Survey submission endpoints
├── survey_results/            # Storage for survey responses
│   └── [user_submissions]     # Individual user survey files
├── tests/                     # Test suite
│   ├── test_matching.py       # Tests for matching algorithm
│   ├── test_profiles.py       # Tests for profile management
│   └── mock_data.py           # Test data generation
└── config.json                # Configuration settings
```

## Key Components

### Matching Algorithm
- Implements a multi-factor compatibility scoring system
- Uses weighted attributes based on importance to travel compatibility
- Applies both hard filters (deal-breakers) and soft preferences
- Incorporates mutual compatibility in both directions

### User Profiles
- Stores comprehensive user information securely
- Manages privacy settings and data visibility
- Handles profile updates and version history
- Implements input validation and data quality checks

### Survey Processing
- Processes raw survey submissions into structured data
- Applies normalization and standardization to responses
- Extracts key travel preferences and personality indicators
- Generates analytics on user demographics and preferences

## How It Works

1. **Data Collection**: Users complete a travel preferences survey
2. **Profile Creation**: Survey data is processed into a structured user profile
3. **Match Analysis**: The matching algorithm evaluates compatibility between users
4. **Match Generation**: Compatible users are paired based on overall compatibility score
5. **Feedback Loop**: Match success feedback is used to refine the algorithm

## Survey Data Collection

The system supports multiple ways to collect and store survey data:

1. **Online Survey Interface**: Users can complete a web-based survey provided by the `get_user_info` module
2. **Direct API Submission**: Applications can submit data directly to the survey API endpoints
3. **CSV Import**: Pre-collected survey data can be imported through CSV files

### CSV File Storage

The `survey_results/` directory is the central repository for all user survey data. Files are stored in this format:
- Filename pattern: `user_answer_TIMESTAMP.csv` (e.g., `user_answer_20230415_123456.csv`)
- CSV structure includes all survey fields with standardized headers
- All files are stored exclusively on the server side through the survey API

The system regularly checks this directory for new files and processes them automatically.

## Integration with get_user_info Module

This module works closely with the `get_user_info` module:

1. `get_user_info` provides the survey interface and initial data collection
2. Survey responses are saved in the `UserInfo_and_Match/survey_results/` directory
3. This module processes the raw survey data and creates structured user profiles
4. The matching algorithm then uses these profiles to identify compatible travelers

This separation of concerns allows:
- Independent development of the user interface and matching algorithm
- Flexible data collection methods
- Optimization of each component for its specific purpose

## Integration Points

This module provides data to:
- `get_itinerary` module (for personalized itinerary creation)
- `blog_generation` module (for personalized content)
- Web and mobile interfaces (for profile display and match presentation)

And receives data from:
- Survey form submissions
- User feedback on matches
- Profile updates from web/mobile interfaces

## Match Factors

The matching algorithm considers multiple dimensions:
1. **Travel Style**: Pace, planning level, activity types
2. **Preferences**: Accommodation, food, budget, transportation
3. **Personality**: Extraversion, openness, conscientiousness
4. **Demographics**: Age range, language, background
5. **Destination Interests**: Geographic and cultural preferences

## Configuration

System settings in `config.json` include:
- Matching algorithm parameters and thresholds
- Feature weighting configurations
- Database connection settings
- Privacy and data retention policies

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Required packages:
  - pandas
  - scikit-learn
  - psycopg2
  - numpy
  - fastapi

## Data Privacy

The system implements several privacy protections:
- Personal identifiers are separated from matching data
- Users control visibility of profile information
- Match data is encrypted in transit and at rest
- Data retention policies automatically expire old data
- Users can request complete data deletion

## Performance Considerations

- Match calculations are performed asynchronously
- Pre-computed compatibility scores improve response time
- Database indexes optimize common query patterns
- Caching is used for frequently accessed profiles

## Troubleshooting

### Common Issues

#### Poor Match Quality
If matches seem incompatible:
1. Check that users have completed all survey sections
2. Verify the weighting configuration in `weightings.json`
3. Review the match threshold settings in `config.json`

#### Missing User Data
If user profiles appear incomplete:
1. Check the survey submission logs
2. Verify data processing in `survey_processing`
3. Ensure database connections are functioning

#### CSV File Issues
If survey data files are missing or corrupted:
1. Check that the survey system is properly configured
2. Verify that `survey_results/` directory exists and has proper permissions
3. Check server logs for any errors during the form submission process
4. Ensure the Flask server is running correctly with `python ../get_user_info/start_server.py`

#### Slow Match Processing
If match generation is taking too long:
1. Check database performance and indexes
2. Verify the match batch size configuration
3. Consider adjusting the algorithm complexity settings

## Future Enhancements

- Machine learning-based matching refinement
- Real-time chat and communication between matches
- Group matching for multi-person travel parties
- Integration with social networks for enhanced profiles
- Reputation and trust scoring system 