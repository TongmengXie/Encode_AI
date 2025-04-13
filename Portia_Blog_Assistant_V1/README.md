# AI-Powered Travel Blog Generator

A Python application that generates personalized travel blogs with AI-generated images using Portia, OpenAI's GPT models, and Google's Gemini.

## Overview

This application creates custom travel blogs based on user input, complete with AI-generated images that match the blog content. The system uses state-of-the-art language models to generate engaging travel narratives and image generation capabilities to create visual content.

## Features

- **Personalized Travel Blogs**: Generate custom travel content based on user information
- **AI-Generated Images**: Create images that complement the blog content
- **Multi-Model Support**: Uses either OpenAI or Google's Gemini based on availability
- **Graceful Fallbacks**: Maintains functionality even when APIs are unavailable
- **Interactive UI**: Simple command-line interface for entering travel details
- **HTML Export**: Creates beautiful, shareable HTML blog pages
- **Smart API Selection**: Automatically uses the working API service

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd travel-blog-generator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up API keys (see "API Keys Setup" section below)

## API Keys Setup

The application can work with either OpenAI's API or Google's Gemini API. Set up one or both:

### Option 1: Environment Variables

Add the following to your environment variables:
```
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### Option 2: .env File

Create a `.env` file in the project root with:
```
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
```

## Usage

Run the application:
```
python main.py
```

Follow the prompts to:
1. Choose whether to enter your own travel details or use the default example
2. If entering details, provide information about the traveler and destination
3. The application will generate a blog and images using available AI services
4. An HTML file will be created and automatically opened in your browser

## Example Input Fields

- **Name**: Traveler's name
- **Age Range**: Approximate age group (e.g., "25~34")
- **Gender**: Gender identity
- **Nationality**: Country of origin
- **Destination**: Travel destination
- **Interests**: What the traveler enjoys (e.g., "historical sites, food")
- **Future Travel Wish**: Where they'd like to go next
- **Special Requirements**: Any special needs (optional)
- **Budget**: Approximate travel budget (optional)
- **Currency Preference**: Preferred currency (optional)
- **Travel Preference**: Travel style (e.g., "luxury", "backpacking") (optional)
- **Issues**: Any concerns about the trip (optional)

## Output

The application generates:
1. A console display of the blog content
2. An HTML file in the `blog_output` directory
3. Generated images in the `generated_media` directory

## Architecture

The application uses the Portia framework to orchestrate AI tools:
- **BlogGenerationTool**: Generates blog content with title, introduction, paragraphs, and conclusion
- **MediaSuggestionTool**: Suggests images that would complement the blog
- **MediaGenerator**: Creates actual images based on the suggestions

## Dependencies

- **portia**: Framework for LLM application development
- **google-generativeai**: Google's Gemini API client
- **openai**: OpenAI API client
- **python-dotenv**: For loading environment variables
- **pillow**: For image processing
- **requests**: For HTTP requests

## Troubleshooting

**API Key Issues**: If you encounter authentication errors, check that your API keys are valid and correctly set up.

**Image Generation Failure**: If image generation fails, the application will automatically use placeholder images.

**Model Unavailability**: If one model service is unavailable, the system automatically tries the other, or falls back to template-based generation.

## License

[MIT License](LICENSE)

## Acknowledgements

- OpenAI for GPT and DALL-E APIs
- Google for Gemini API
- [Portia](https://github.com/portia-project/portia) framework 