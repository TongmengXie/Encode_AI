import random
import os
import requests
import io
import getpass
import json
import base64
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Literal, Type
from PIL import Image
from openai import OpenAI
import tkinter as tk
from tkinter import ttk
from io import BytesIO
import time
import webbrowser
import datetime
from dotenv import load_dotenv

from portia import (
    DefaultToolRegistry,
    InMemoryToolRegistry,
    Portia,
    Config,
    Tool,
    ToolRunContext,
    LLMModel,
    LLMProvider
)
from portia.cli import CLIExecutionHooks
from pydantic import BaseModel, Field
from portia.llm_wrapper import LLMWrapper
from portia.config import LLM_TOOL_MODEL_KEY

# Try to import Google's Gemini packages
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI package not found. To use Gemini, run: pip install google-generativeai")

# Set your API keys
# First try to get them from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# If not in environment, ask the user (only in interactive mode)
if __name__ == "__main__":
    if not OPENAI_API_KEY and not GEMINI_API_KEY:
        print("No API keys found in environment variables.")
        api_choice = input("Which API would you like to use? (1 for OpenAI, 2 for Gemini): ")
        
        if api_choice == "1":
            OPENAI_API_KEY = getpass.getpass("Enter your OpenAI API key (input will be hidden): ")
        elif api_choice == "2" and GEMINI_AVAILABLE:
            GEMINI_API_KEY = getpass.getpass("Enter your Gemini API key (input will be hidden): ")
            if GEMINI_API_KEY:
                genai.configure(api_key=GEMINI_API_KEY)
        else:
            print("Using template-based generation without API calls.")

# Configure Gemini if available and have API key
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@dataclass
class UserData:
    name: str
    age_range: str
    gender: str
    nationality: str
    destination: str
    interests: str
    future_travel_wish: str
    special_requirements: Optional[str] = None
    budget: Optional[str] = None
    currency_preference: Optional[str] = None
    travel_preference: Optional[str] = None
    issues: Optional[str] = None

@dataclass
class MediaSuggestion:
    description: str
    prompt: str
    type: str  # "image", "video", or "audio"
    url: Optional[str] = None  # Local file path or URL
    content: Optional[bytes] = None  # Binary content
    generator: Optional[str] = None  # Which API generated this media ("openai", "gemini", "stock")

@dataclass
class BlogContent:
    title: str
    introduction: str
    paragraphs: List[str]
    conclusion: str
    media_suggestions: List[MediaSuggestion]
    generator: str = "template"  # Which API generated the content ("openai", "gemini", "template")

class MediaGenerator:
    """Handles media generation using OpenAI's DALL-E, Google Gemini, and other services"""
    def __init__(self, openai_client=None, use_gemini=False):
        self.openai_client = openai_client
        self.use_gemini = use_gemini and GEMINI_AVAILABLE and GEMINI_API_KEY
        self.output_dir = "generated_media"
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Try to detect available image generator
        self.openai_working = False
        self.gemini_working = False
        
        # Test OpenAI image generation capability
        if self.openai_client:
            try:
                print("Testing OpenAI image generation capability...")
                # Just verify we can create an OpenAI client without making actual API call
                OpenAI(api_key=OPENAI_API_KEY)
                self.openai_working = True
            except Exception as e:
                print(f"OpenAI image generation unavailable: {e}")
        
        # Test Gemini image generation capability if available
        if self.use_gemini:
            try:
                print("Testing Gemini for future image generation capability...")
                # Just verify we can use the Gemini API without making actual API call
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_working = True
            except Exception as e:
                print(f"Gemini image generation unavailable: {e}")
        
        print(f"Media generator initialized. OpenAI: {'Available' if self.openai_working else 'Unavailable'}, " +
              f"Gemini: {'Available' if self.gemini_working else 'Unavailable'}")
    
    def generate_image(self, prompt: str, description: str) -> MediaSuggestion:
        """Generate an image using available APIs or fallback to placeholders"""
        # Modify the prompt to ensure no humans in the images
        prompt = self._modify_prompt_for_views(prompt)
        
        # Try each API based on availability, with fallbacks
        if self.openai_working:
            try:
                print(f"Generating image with OpenAI: {description}")
                return self._generate_image_openai(prompt, description)
            except Exception as e:
                print(f"OpenAI image generation failed: {e}")
                self.openai_working = False  # Mark as not working for future requests
                # If OpenAI fails and Gemini is available, try that next
        
        if self.gemini_working and GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                print(f"Generating image with Gemini: {description}")
                return self._generate_image_gemini(prompt, description)
            except Exception as e:
                print(f"Gemini image generation failed: {e}")
                self.gemini_working = False  # Mark as not working for future requests
        
        # If all attempts fail, use a placeholder
        print(f"All image generation methods failed, using placeholder: {description}")
        return self._generate_placeholder_image(prompt, description)
    
    def _modify_prompt_for_views(self, prompt: str) -> str:
        """Modify the prompt to ensure images are views/landscapes without humans"""
        # Add specifications for no humans and focusing on views
        if "no humans" not in prompt.lower() and "without people" not in prompt.lower():
            prompt += ", scenic view, no humans, no people, landscape photography, natural beauty"
        return prompt
    
    def _generate_image_openai(self, prompt: str, description: str) -> MediaSuggestion:
        """Generate an image using OpenAI's DALL-E"""
        try:
            # Generate a safe filename from the description
            safe_name = "".join(c if c.isalnum() else "_" for c in description)
            safe_name = safe_name[:50]  # Limit length
            filename = f"openai_{safe_name}_{int(time.time())}.png"
            file_path = os.path.join(self.output_dir, filename)
            
            # Call DALL-E API
            response = self.openai_client.images.generate(
                model="dall-e-2",  # or "dall-e-3" for higher quality but more expensive
                prompt=prompt,
                size="1024x1024",  # Larger size for better landscape details
                n=1,
                response_format="b64_json"
            )
            
            # Save the generated image
            image_data = base64.b64decode(response.data[0].b64_json)
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            print(f"Image generated with OpenAI and saved to {file_path}")
            
            return MediaSuggestion(
                description=description,
                prompt=prompt,
                type="image",
                url=file_path,
                content=image_data,
                generator="openai"
            )
            
        except Exception as e:
            print(f"Error generating image with OpenAI: {e}")
            raise e  # Re-raise to allow fallback to other methods
    
    def _generate_image_gemini(self, prompt: str, description: str) -> MediaSuggestion:
        """Generate an image using Google's Gemini"""
        try:
            # Generate a safe filename from the description
            safe_name = "".join(c if c.isalnum() else "_" for c in description)
            safe_name = safe_name[:50]  # Limit length
            filename = f"gemini_{safe_name}_{int(time.time())}.png"
            file_path = os.path.join(self.output_dir, filename)
            
            # Configure Gemini for image generation
            generation_config = {
                "temperature": 0.9,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 2048,
            }
            
            # Set up the Gemini model for image generation
            # Note: Gemini-1.5 Pro and Gemini-1.5 Flash are the current models that support image generation
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro", 
                generation_config=generation_config
            )
            
            # For actual image generation, we need to use Gemini's imagen capabilities
            # This requires the "imagen" API in Gemini, which exists but may have specific requirements
            try:
                # Try using the imagen API directly if available
                # This implementation might need to be adjusted based on the latest Gemini API
                response = model.generate_content({
                    "prompt": prompt,
                    "modality": "imagen",  # This signals we want to generate an image
                    "size": "1024x1024"
                })
                
                # Check if we got an image back
                if hasattr(response, 'imagen') and response.imagen:
                    # Save the image
                    image_data = response.imagen.content
                    with open(file_path, "wb") as f:
                        f.write(image_data)
                    
                    print(f"Image generated with Gemini and saved to {file_path}")
                    
                    return MediaSuggestion(
                        description=description,
                        prompt=prompt,
                        type="image",
                        url=file_path,
                        content=image_data,
                        generator="gemini"
                    )
                else:
                    # Fall back to the alternate method if direct image generation doesn't work
                    raise ValueError("Gemini did not return an image")
                    
            except Exception as inner_e:
                print(f"Direct Gemini image generation failed, trying alternate method: {inner_e}")
                
                # Alternate method: Use Vertex AI Imagen if available
                # This is a more specialized Google Cloud service that works with Gemini
                try:
                    from google.cloud import aiplatform
                    from vertexai.preview.generative_models import GenerativeModel as VertexGenerativeModel
                    
                    # Initialize Vertex AI with project details
                    aiplatform.init(project="your-project-id")
                    
                    # Create the model
                    imagen_model = VertexGenerativeModel("imagen-1.0")
                    
                    # Generate the image
                    response = imagen_model.generate_images(
                        prompt=prompt,
                        number_of_images=1,
                        safety_settings={
                            "harm_category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_NONE",
                        }
                    )
                    
                    # Process the response
                    if response.images and len(response.images) > 0:
                        # Download the generated image
                        image_data = requests.get(response.images[0].url).content
                        
                        with open(file_path, "wb") as f:
                            f.write(image_data)
                        
                        print(f"Image generated with Vertex AI Imagen and saved to {file_path}")
                        
                        return MediaSuggestion(
                            description=description,
                            prompt=prompt,
                            type="image",
                            url=file_path,
                            content=image_data,
                            generator="vertex_imagen"
                        )
                    else:
                        raise ValueError("No images returned from Vertex AI")
                        
                except (ImportError, Exception) as vertex_e:
                    print(f"Vertex AI image generation failed: {vertex_e}")
                    # Fall back to placeholder
            
            # If we get here, we need to use a placeholder
            print("Using placeholder image as Gemini/Vertex image generation failed")
            
            # Generate a placeholder image with the description text
            # This creates an image with the text from the description
            placeholder_url = f"https://placehold.co/800x600/3498db/ffffff/png?text={safe_name.replace('_', '+')}"
            response = requests.get(placeholder_url)
            image_data = response.content
            
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            print(f"Placeholder image saved to {file_path}")
            
            return MediaSuggestion(
                description=description,
                prompt=prompt,
                type="image",
                url=file_path,
                content=image_data,
                generator="placeholder"
            )
            
        except Exception as e:
            print(f"All image generation methods with Gemini failed: {e}")
            # Last resort - return a placeholder without saving
            return MediaSuggestion(
                description=description,
                prompt=prompt,
                type="image",
                url=f"https://placehold.co/800x600/ff0000/ffffff/png?text=Generation+Failed",
                generator="error"
            )
            
    def generate_video_with_gemini(self, prompt: str, description: str) -> MediaSuggestion:
        """
        Attempt to generate a video using Gemini's capabilities
        
        Note: As of now, Gemini doesn't have direct video generation capabilities,
        but this function is prepared for when that feature becomes available.
        Currently, it falls back to stock videos.
        """
        print("Video generation with Gemini is not yet available. Using stock video.")
        # Get a relevant stock video for now
        return self.get_stock_video(description)
        
    def generate_audio_with_gemini(self, prompt: str, description: str) -> MediaSuggestion:
        """
        Attempt to generate audio using Gemini's capabilities
        
        Note: As of now, Gemini doesn't have direct audio generation capabilities,
        but this function is prepared for when that feature becomes available.
        Currently, it falls back to stock audio.
        """
        print("Audio generation with Gemini is not yet available. Using stock audio.")
        # Get a relevant stock audio for now
        return self.get_stock_audio(description)
    
    def get_stock_video(self, description: str) -> MediaSuggestion:
        """Return a placeholder stock video"""
        # For demo purposes, we'll return one of a few stock videos
        # In a real implementation, this could connect to a stock video API
        stock_videos = {
            "cherry blossom": "https://www.pexels.com/download/video/5562440/?fps=25.0&h=1080&w=1920",
            "japan": "https://www.pexels.com/download/video/3910229/?fps=29.97&h=1080&w=1920",
            "travel": "https://www.pexels.com/download/video/5509565/?fps=25.0&h=720&w=1280",
            "walking": "https://www.pexels.com/download/video/4594052/?fps=25.0&h=720&w=1280",
            "default": "https://www.pexels.com/download/video/1409899/?fps=25.0&h=720&w=1280"
        }
        
        # Find the most relevant stock video
        url = None
        for key, video_url in stock_videos.items():
            if key.lower() in description.lower():
                url = video_url
                break
        
        if url is None:
            url = stock_videos["default"]
            
        return MediaSuggestion(
            description=description,
            prompt="",
            type="video",
            url=url,
            generator="stock"
        )
    
    def get_stock_audio(self, description: str) -> MediaSuggestion:
        """Return a placeholder stock audio"""
        # For demo purposes, we'll return one of a few stock audio files
        stock_audio = {
            "japan": "https://cdn.pixabay.com/download/audio/2021/11/25/audio_756b2eba0d.mp3",
            "travel": "https://cdn.pixabay.com/download/audio/2023/06/19/audio_4c35b2a3ed.mp3",
            "nature": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_4db20cba62.mp3",
            "default": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_28993b77af.mp3"
        }
        
        # Find the most relevant stock audio
        url = None
        for key, audio_url in stock_audio.items():
            if key.lower() in description.lower():
                url = audio_url
                break
        
        if url is None:
            url = stock_audio["default"]
            
        return MediaSuggestion(
            description=description,
            prompt="",
            type="audio",
            url=url,
            generator="stock"
        )

    def _generate_placeholder_image(self, prompt: str, description: str) -> MediaSuggestion:
        """Generate a placeholder image when no API is available"""
        try:
            # Create a simplified placeholder with a direct URL - no file saving needed
            safe_name = "".join(c if c.isalnum() else "_" for c in description)
            safe_name = safe_name.replace("_", "+")[:20]  # Shorter text for readability
            
            # Direct URL to a placeholder image - this will definitely work in HTML
            placeholder_url = f"https://placehold.co/600x400/0275d8/ffffff/png?text={safe_name}"
            
            print(f"Created placeholder image URL: {placeholder_url}")
            
            return MediaSuggestion(
                description=description,
                prompt=prompt,
                type="image",
                url=placeholder_url,  # Direct URL - no file saving
                generator="placeholder"
            )
        except Exception as e:
            print(f"Error creating placeholder: {e}")
            # Absolute fallback - hardcoded URL
            return MediaSuggestion(
                description=description,
                prompt=prompt,
                type="image",
                url="https://placehold.co/600x400/dc3545/ffffff/png?text=Image+Unavailable",
                generator="error"
            )

class BlogGenerator:
    def __init__(self, openai_api_key=None, use_gemini=False):
        self.openai_client = None
        self.use_gemini = use_gemini and GEMINI_AVAILABLE and GEMINI_API_KEY
        
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
            
        self.media_gen = MediaGenerator(self.openai_client, self.use_gemini)
    
    def generate_blog(self, user: UserData) -> BlogContent:
        """Generate blog content using available APIs or fallback to templates"""
        # Try Gemini first if available
        if self.use_gemini:
            try:
                return self._generate_with_gemini(user)
            except Exception as e:
                print(f"Error generating with Gemini: {e}")
                # Fall back to OpenAI
                if self.openai_client:
                    return self.generate_with_openai(user)
                # If no OpenAI, use templates
                return self._generate_with_templates(user)
        
        # Try OpenAI if available
        elif self.openai_client:
            return self.generate_with_openai(user)
        
        # Fall back to template generation
        else:
            return self._generate_with_templates(user)
    
    def generate_with_openai(self, user: UserData) -> BlogContent:
        """Generate blog content using OpenAI if API key is provided, otherwise use template method"""
        if self.openai_client:
            return self._generate_with_ai(user)
        else:
            return self._generate_with_templates(user)
    
    def _generate_with_gemini(self, user: UserData) -> BlogContent:
        """Generate blog content using Google's Gemini API"""
        # Prepare prompt for Gemini
        prompt = f"""
        Create a travel blog post for the following traveler:
        Name: {user.name}
        Age Range: {user.age_range}
        Gender: {user.gender}
        Nationality: {user.nationality}
        Destination: {user.destination}
        Interests: {user.interests}
        Future Travel Wish: {user.future_travel_wish}
        Special Requirements: {user.special_requirements}
        Budget: {user.budget}
        Currency Preference: {user.currency_preference}
        Travel Preference: {user.travel_preference}
        Issues: {user.issues}
        
        Generate a blog post with:
        1. An engaging title
        2. An introduction that mentions their nationality, interests, and destination
        3. 3-5 paragraphs about their journey
        4. A conclusion that mentions their future travel wish
        
        Format your response as JSON with the following structure:
        {{
            "title": "Blog Title",
            "introduction": "Introduction paragraph",
            "paragraphs": ["Paragraph 1", "Paragraph 2", "Paragraph 3"],
            "conclusion": "Conclusion paragraph"
        }}
        """
        
        try:
            # Configure Gemini model
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
            }
            
            # Initialize the model
            model = genai.GenerativeModel("gemini-pro", generation_config=generation_config)
            
            # Generate content
            response = model.generate_content(prompt)
            content = response.text
            
            # Extract the JSON from the response
            # Find the JSON block in the response (in case there's extra text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                blog_data = json.loads(json_content)
            else:
                raise ValueError("Could not find valid JSON in the response")
            
            # Generate media suggestions with Gemini
            media_suggestions = self._generate_media_suggestions_gemini(user, blog_data)
            
            # Actually generate the media based on the suggestions
            processed_media = []
            for media in media_suggestions:
                if media.type == "image":
                    print(f"Processing image with Gemini: {media.description}")
                    img_result = self.media_gen._generate_image_gemini(media.prompt, media.description)
                    processed_media.append(img_result)
                elif media.type == "video":
                    print(f"Processing video with Gemini: {media.description}")
                    processed_media.append(self.media_gen.generate_video_with_gemini(media.prompt, media.description))
                elif media.type == "audio":
                    print(f"Processing audio with Gemini: {media.description}")
                    processed_media.append(self.media_gen.generate_audio_with_gemini(media.prompt, media.description))
                else:
                    processed_media.append(media)
            
            return BlogContent(
                title=blog_data["title"],
                introduction=blog_data["introduction"],
                paragraphs=blog_data["paragraphs"],
                conclusion=blog_data["conclusion"],
                media_suggestions=processed_media,
                generator="gemini"
            )
            
        except Exception as e:
            print(f"Error generating content with Gemini: {e}")
            # Fall back to template generation
            return self._generate_with_templates(user)
    
    def _generate_media_suggestions_gemini(self, user: UserData, blog_data) -> List[MediaSuggestion]:
        """Generate media suggestions using Gemini"""
        prompt = f"""
        Based on this blog post about a trip to {user.destination} with interest in {user.interests},
        suggest only 2 specific images that would complement the blog. No video or audio suggestions needed.
        
        IMPORTANT: ALL IMAGES MUST BE SCENIC VIEWS, LANDSCAPES, OR ARCHITECTURE WITHOUT ANY HUMANS OR PEOPLE IN THEM.
        
        Blog title: {blog_data["title"]}
        
        Format your response as JSON with the following structure:
        {{
            "media": [
                {{
                    "type": "image",
                    "description": "Description for humans",
                    "prompt": "Detailed prompt for image generation - must explicitly specify no humans or people, focusing on landscapes and scenic views"
                }},
                {{
                    "type": "image",
                    "description": "Description for humans",
                    "prompt": "Detailed prompt for image generation - must explicitly specify no humans or people, focusing on landscapes and scenic views"
                }}
            ]
        }}
        """
        
        try:
            # Configure and generate with Gemini
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            content = response.text
            
            # Extract the JSON from the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                media_data = json.loads(json_content)
            else:
                raise ValueError("Could not find valid JSON in the response")
            
            # Convert to MediaSuggestion objects
            media_suggestions = []
            for item in media_data.get("media", []):
                media_suggestions.append(
                    MediaSuggestion(
                        description=item["description"],
                        prompt=item["prompt"],
                        type=item["type"],
                        url=None,
                        generator="gemini"
                    )
                )
                
            return media_suggestions
            
        except Exception as e:
            print(f"Error generating media suggestions with Gemini: {e}")
            return self._generate_media_suggestions_template(user)
            
    def _generate_with_ai(self, user: UserData) -> BlogContent:
        """Generate blog content using OpenAI API"""
        # Prepare prompt for the AI
        prompt = f"""
        Create a travel blog post for the following traveler:
        Name: {user.name}
        Age Range: {user.age_range}
        Gender: {user.gender}
        Nationality: {user.nationality}
        Destination: {user.destination}
        Interests: {user.interests}
        Future Travel Wish: {user.future_travel_wish}
        Special Requirements: {user.special_requirements}
        Budget: {user.budget}
        Currency Preference: {user.currency_preference}
        Travel Preference: {user.travel_preference}
        Issues: {user.issues}
        
        Generate a blog post with:
        1. An engaging title
        2. An introduction that mentions their nationality, interests, and destination
        3. 3-5 paragraphs about their journey
        4. A conclusion that mentions their future travel wish
        
        Format your response as JSON with the following structure:
        {{
            "title": "Blog Title",
            "introduction": "Introduction paragraph",
            "paragraphs": ["Paragraph 1", "Paragraph 2", "Paragraph 3"],
            "conclusion": "Conclusion paragraph"
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # More widely available model
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a travel blog writer that creates personalized content."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response
            content = response.choices[0].message.content
            blog_data = json.loads(content)
            
            # Generate media suggestions
            media_suggestions = self._generate_media_suggestions_ai(user, blog_data)
            
            # Actually generate the images based on the suggestions
            processed_media = []
            for media in media_suggestions:
                if media.type == "image":
                    # Generate the actual image
                    processed_media.append(self.media_gen.generate_image(media.prompt, media.description))
                elif media.type == "video":
                    # Get a stock video for now
                    processed_media.append(self.media_gen.get_stock_video(media.description))
                elif media.type == "audio":
                    # Get a stock audio for now
                    processed_media.append(self.media_gen.get_stock_audio(media.description))
                else:
                    processed_media.append(media)
            
            return BlogContent(
                title=blog_data["title"],
                introduction=blog_data["introduction"],
                paragraphs=blog_data["paragraphs"],
                conclusion=blog_data["conclusion"],
                media_suggestions=processed_media,
                generator="openai"
            )
            
        except Exception as e:
            print(f"Error generating content with OpenAI: {e}")
            # Fall back to template generation
            return self._generate_with_templates(user)
    
    def _generate_media_suggestions_ai(self, user: UserData, blog_data) -> List[MediaSuggestion]:
        """Generate media suggestions using OpenAI"""
        if not self.openai_client:
            return self._generate_media_suggestions_template(user)
            
        try:
            prompt = f"""
            Based on this blog post about a trip to {user.destination} with interest in {user.interests},
            suggest only 2 specific images that would complement the blog. No video or audio suggestions needed.
            
            IMPORTANT: ALL IMAGES MUST BE SCENIC VIEWS, LANDSCAPES, OR ARCHITECTURE WITHOUT ANY HUMANS OR PEOPLE IN THEM.
            
            Blog title: {blog_data["title"]}
            
            Format your response as JSON with the following structure:
            {{
                "media": [
                    {{
                        "type": "image",
                        "description": "Description for humans",
                        "prompt": "Detailed prompt for image generation - must explicitly specify no humans or people, focusing on landscapes and scenic views"
                    }},
                    {{
                        "type": "image",
                        "description": "Description for humans",
                        "prompt": "Detailed prompt for image generation - must explicitly specify no humans or people, focusing on landscapes and scenic views"
                    }}
                ]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a visual content creator for travel blogs."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response
            content = response.choices[0].message.content
            media_data = json.loads(content)
            
            # Convert to MediaSuggestion objects
            media_suggestions = []
            for item in media_data.get("media", []):
                media_suggestions.append(
                    MediaSuggestion(
                        description=item["description"],
                        prompt=item["prompt"],
                        type=item["type"],
                        url=None,
                        generator="openai"
                    )
                )
                
            return media_suggestions
            
        except Exception as e:
            print(f"Error generating media suggestions with OpenAI: {e}")
            return self._generate_media_suggestions_template(user)
    
    def _generate_with_templates(self, user: UserData) -> BlogContent:
        """Generate blog content using templates (fallback method)"""
        title = self._generate_blog_title(user)
        intro = self._generate_introduction(user)
        paras = self._generate_paragraphs(user)
        conclusion = self._generate_conclusion(user)
        media_suggestions = self._generate_media_suggestions_template(user)
        
        # Process media suggestions to generate actual content
        processed_media = []
        for media in media_suggestions:
            if media.type == "image":
                # Generate the actual image with whatever is available
                processed_media.append(self.media_gen.generate_image(media.prompt, media.description))
            elif media.type == "video":
                # Get a stock video
                processed_media.append(self.media_gen.get_stock_video(media.description))
            elif media.type == "audio":
                # Get a stock audio
                processed_media.append(self.media_gen.get_stock_audio(media.description))
            else:
                processed_media.append(media)
        
        return BlogContent(
            title=title,
            introduction=intro,
            paragraphs=paras,
            conclusion=conclusion,
            media_suggestions=processed_media if processed_media else media_suggestions,
            generator="template"
        )
    
    def _generate_blog_title(self, user: UserData) -> str:
        templates = [
            f"The Enchanting Beauty of {user.destination}",
            f"Discovering the Magic of {user.destination}",
            f"A Journey Through {user.destination}: Finding Beauty Everywhere",
            f"The Breathtaking Sights of {user.destination}",
        ]
        return random.choice(templates)

    def _generate_introduction(self, user: UserData) -> str:
        return f"Embarking on a journey to {user.destination} brings a sense of wonder and excitement. With its rich culture and stunning landscapes, this destination offers an unforgettable experience for anyone with a passion for {user.interests}. The perfect blend of tradition and natural beauty creates an atmosphere that captivates the soul from the very first moment."

    def _generate_paragraphs(self, user: UserData) -> List[str]:
        paragraphs = [
            f"Arriving in {user.destination} feels like stepping into another world. The air carries whispers of ancient stories, while the landscape unfolds with breathtaking beauty at every turn. The first glimpse of this magnificent place creates memories that linger long after the journey ends.",
            
            f"Exploring the local areas reveals hidden treasures and unexpected delights. Friendly locals share stories and recommendations that make the experience even more special. The authentic charm of {user.destination} shines through in these everyday interactions.",
            
            f"The experience of {user.interests} here is truly unparalleled. Nature presents itself in the most magnificent ways, painting pictures more beautiful than any artist could capture. Each moment spent admiring these sights feels like a precious gift.",
            
            f"The local cuisine tells its own story of {user.destination}'s rich cultural heritage. Each dish represents generations of tradition, creating flavors that dance on the palate and warm the heart. Sharing a meal here connects visitors to the soul of this special place."
        ]
        
        return paragraphs

    def _generate_conclusion(self, user: UserData) -> str:
        return f"As the journey through {user.destination} comes to a close, the heart fills with gratitude for these beautiful experiences. The memories created here will provide endless inspiration and joy in the days to come. Perhaps someday, the road will lead to {user.future_travel_wish} - another adventure waiting to unfold with its own unique magic."

    def _generate_media_suggestions_template(self, user: UserData) -> List[MediaSuggestion]:
        """Generate media suggestions using templates"""
        image_suggestions = [
            MediaSuggestion(
                description=f"Scenic view of {user.destination} landscape",
                prompt=f"Scenic landscape photograph of {user.destination}, natural beauty, dramatic lighting, no people, no humans, wide angle, high resolution",
                type="image"
            ),
            MediaSuggestion(
                description=f"{user.interests} in {user.destination} with natural scenery",
                prompt=f"Beautiful photograph of {user.interests} in {user.destination}, natural scenery, no people, landscape view, golden hour lighting",
                type="image"
            ),
        ]
        
        # Return only two image suggestions
        return image_suggestions


class HtmlGenerator:
    """Generates HTML output for the blog content"""
    def __init__(self, blog: BlogContent, user: UserData):
        self.blog = blog
        self.user = user
        self.output_dir = "blog_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_html(self) -> str:
        """Generate HTML for the blog"""
        # Create a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "travel_blog"  # Generic name for privacy
        filename = f"{safe_name}_{self.user.destination.replace(' ', '_')}_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        # Start building HTML with additional CSS for media sources
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.blog.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
        }}
        header {{
            background-color: #3498db;
            color: white;
            padding: 40px 20px;
            text-align: center;
            background-image: linear-gradient(to right, #3498db, #2c3e50);
        }}
        h1 {{
            margin: 0;
            font-size: 2.5rem;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .destination-info {{
            text-align: center;
            margin-top: 20px;
            color: rgba(255,255,255,0.9);
            font-size: 1.2rem;
        }}
        .intro {{
            font-size: 1.2rem;
            margin-bottom: 30px;
            border-left: 4px solid #3498db;
            padding-left: 20px;
            font-style: italic;
        }}
        .media-item {{
            margin: 30px 0;
            text-align: center;
        }}
        .media-item img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }}
        .media-caption {{
            margin-top: 10px;
            font-style: italic;
            color: #666;
        }}
        .media-source {{
            font-size: 0.8rem;
            color: #999;
            margin-top: 5px;
        }}
        .conclusion {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-top: 30px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }}
        .blog-info {{
            background-color: #f0f8ff;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 20px 0;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{self.blog.title}</h1>
        <div class="destination-info">
            <span>Destination: {self.user.destination}</span>
        </div>
    </header>
    
    <div class="container">
        <div class="intro">
            {self.blog.introduction}
        </div>
        
        <!-- Blog info -->
        <div class="blog-info">
            Content generated using: <strong>{self.blog.generator}</strong>
        </div>
"""

        # Add first paragraph
        html += f"""
        <p>{self.blog.paragraphs[0]}</p>
"""

        # Add first image if available
        if len(self.blog.media_suggestions) > 0:
            media = self.blog.media_suggestions[0]
            if media.type == "image" and media.url:
                # Convert to absolute file URL if it's a local path
                img_url = media.url
                if not img_url.startswith(('http://', 'https://')):
                    # Convert to absolute file URL
                    absolute_path = os.path.abspath(img_url)
                    img_url = f"file:///{absolute_path.replace(os.sep, '/')}"
                
                html += f"""
        <!-- First landscape image -->
        <div class="media-item">
            <img src="{img_url}" alt="{media.description}" style="max-width:100%; height:auto;">
            <div class="media-caption">{media.description}</div>
            <div class="media-source">Source: {media.generator or 'placeholder'}</div>
        </div>
"""
            else:
                # Use a placeholder if the image isn't available
                html += f"""
        <!-- Placeholder for first image -->
        <div class="media-item">
            <img src="https://placehold.co/800x500/0275d8/ffffff/png?text={self.user.destination.replace(' ', '+')}" 
                alt="Placeholder for {self.user.destination}" style="max-width:100%; height:auto;">
            <div class="media-caption">View of {self.user.destination}</div>
            <div class="media-source">Source: placeholder</div>
        </div>
"""
        
        # Add remaining paragraphs
        for i in range(1, len(self.blog.paragraphs)):
            html += f"""
        <p>{self.blog.paragraphs[i]}</p>
"""
            # Add second image after the second paragraph
            if i == 1 and len(self.blog.media_suggestions) > 1:
                media = self.blog.media_suggestions[1]
                if media.type == "image" and media.url:
                    # Convert to absolute file URL if it's a local path
                    img_url = media.url
                    if not img_url.startswith(('http://', 'https://')):
                        # Convert to absolute file URL
                        absolute_path = os.path.abspath(img_url)
                        img_url = f"file:///{absolute_path.replace(os.sep, '/')}"
                    
                    html += f"""
        <!-- Second landscape image -->
        <div class="media-item">
            <img src="{img_url}" alt="{media.description}" style="max-width:100%; height:auto;">
            <div class="media-caption">{media.description}</div>
            <div class="media-source">Source: {media.generator or 'placeholder'}</div>
        </div>
"""
                else:
                    # Use a placeholder if the image isn't available
                    html += f"""
        <!-- Placeholder for second image -->
        <div class="media-item">
            <img src="https://placehold.co/800x500/0275d8/ffffff/png?text={self.user.interests.replace(' ', '+')}" 
                alt="Placeholder for {self.user.interests}" style="max-width:100%; height:auto;">
            <div class="media-caption">View of {self.user.interests}</div>
            <div class="media-source">Source: placeholder</div>
        </div>
"""
        
        # Add conclusion
        html += f"""
        <!-- Conclusion section -->
        <div class="conclusion">
            <h3>Final Thoughts</h3>
            <p>{self.blog.conclusion}</p>
        </div>
        
        <div class="footer">
            <p>Generated on {datetime.datetime.now().strftime("%B %d, %Y")} | Travel Blog Assistant</p>
            <p>Discover the beauty of {self.user.destination} through our lens</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Write HTML to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
            
        print(f"HTML blog generated and saved to: {filepath}")
        return filepath

def display_blog_console(blog: BlogContent):
    """Display blog content in console for non-GUI environments"""
    print("\n" + "=" * 80)
    print(f"TITLE: {blog.title}")
    print("=" * 80 + "\n")
    
    print(f"{blog.introduction}\n")
    
    for i, para in enumerate(blog.paragraphs, 1):
        print(f"{para}\n")
        
        # Suggest media after each odd-numbered paragraph
        if i % 2 == 1 and i//2 < len(blog.media_suggestions):
            media = blog.media_suggestions[i//2]
            media_type = "IMAGE" if media.type == "image" else "VIDEO" if media.type == "video" else "AUDIO"
            print(f"[{media_type} SUGGESTION: {media.description}]\n")
    
    print(f"{blog.conclusion}\n")
    
    print("-" * 80)
    print("MEDIA SUGGESTIONS:")
    for i, media in enumerate(blog.media_suggestions, 1):
        media_type = "IMAGE" if media.type == "image" else "VIDEO" if media.type == "video" else "AUDIO"
        print(f"  {i}. [{media_type}] {media.description}")
        if media.url:
            print(f"     URL: {media.url}")
        print(f"     Prompt: {media.prompt}")
    print("-" * 80 + "\n")


class BlogGenerationInput(BaseModel):
    """Input for the BlogGenerationTool."""
    name: str = Field(..., description="User's name")
    age_range: str = Field(..., description="User's age range")
    gender: str = Field(..., description="User's gender")
    nationality: str = Field(..., description="User's nationality")
    destination: str = Field(..., description="Travel destination")
    interests: str = Field(..., description="User's travel interests")
    future_travel_wish: str = Field(..., description="User's future travel wish")
    special_requirements: Optional[str] = Field(None, description="Any special requirements")
    budget: Optional[str] = Field(None, description="User's budget")
    currency_preference: Optional[str] = Field(None, description="Currency preference")
    travel_preference: Optional[str] = Field(None, description="Travel preference")
    issues: Optional[str] = Field(None, description="Any issues to consider")


class BlogGenerationTool(Tool[str]):
    """
    A tool to generate personalized travel blog content.
    
    Given user details and travel preferences, this tool generates a structured
    travel blog with title, introduction, paragraphs, and conclusion.
    """

    id: str = "blog_generation"
    name: str = "Travel Blog Generation Tool"
    description: str = "Generates personalized travel blog content based on user details and preferences."
    args_schema: Type[BaseModel] = BlogGenerationInput
    output_schema: tuple[str, str] = (
        "json",
        "A JSON object with blog content including title, introduction, paragraphs, and conclusion"
    )

    def run(
        self,
        context: ToolRunContext,
        name: str,
        age_range: str,
        gender: str,
        nationality: str,
        destination: str,
        interests: str,
        future_travel_wish: str,
        special_requirements: Optional[str] = None,
        budget: Optional[str] = None,
        currency_preference: Optional[str] = None,
        travel_preference: Optional[str] = None,
        issues: Optional[str] = None,
    ) -> str:
        llm = LLMWrapper.for_usage(LLM_TOOL_MODEL_KEY, context.config).to_langchain()
        
        system_prompt = """You are a travel blog writer that creates personalized content.
Create a travel blog post for the user with the details provided.

Generate a blog post with:
1. An engaging title
2. An introduction that mentions their nationality, interests, and destination
3. 3-5 paragraphs about their journey
4. A conclusion that mentions their future travel wish

Format your response as JSON with the following structure:
{
    "title": "Blog Title",
    "introduction": "Introduction paragraph",
    "paragraphs": ["Paragraph 1", "Paragraph 2", "Paragraph 3"],
    "conclusion": "Conclusion paragraph"
}
"""

        # Create user message with all details
        user_message = f"""
        Name: {name}
        Age Range: {age_range}
        Gender: {gender}
        Nationality: {nationality}
        Destination: {destination}
        Interests: {interests}
        Future Travel Wish: {future_travel_wish}
        """
        
        if special_requirements:
            user_message += f"Special Requirements: {special_requirements}\n"
        if budget:
            user_message += f"Budget: {budget}\n"
        if currency_preference:
            user_message += f"Currency Preference: {currency_preference}\n"
        if travel_preference:
            user_message += f"Travel Preference: {travel_preference}\n"
        if issues:
            user_message += f"Issues: {issues}\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        response = llm.invoke(messages)
        try:
            # Try to parse the response as JSON
            json_response = json.loads(response.content)
            return json.dumps(json_response, indent=2)
        except json.JSONDecodeError:
            # If response is not valid JSON, return an error message
            return json.dumps({
                "error": "Could not parse blog content",
                "raw_response": response.content
            }, indent=2)


class MediaSuggestionInput(BaseModel):
    """Input for the MediaSuggestionTool."""
    destination: str = Field(..., description="Travel destination")
    interests: str = Field(..., description="User's travel interests")
    blog_title: str = Field(..., description="The title of the blog post")
    blog_content: str = Field(..., description="The main content of the blog post")


class MediaSuggestionTool(Tool[str]):
    """
    A tool to suggest media content for travel blogs.
    
    Based on blog content, this tool suggests appropriate image prompts
    that would complement the travel blog.
    """

    id: str = "media_suggestion"
    name: str = "Media Suggestion Tool"
    description: str = "Suggests media content (images) to accompany a travel blog."
    args_schema: Type[BaseModel] = MediaSuggestionInput
    output_schema: tuple[str, str] = (
        "json",
        "A JSON object with media suggestions including descriptions and image generation prompts"
    )

    def run(
        self,
        context: ToolRunContext,
        destination: str,
        interests: str,
        blog_title: str,
        blog_content: str,
    ) -> str:
        llm = LLMWrapper.for_usage(LLM_TOOL_MODEL_KEY, context.config).to_langchain()
        
        system_prompt = """You are a visual content creator for travel blogs.
Based on the blog post about the trip, suggest specific images that would complement the blog.

IMPORTANT: ALL IMAGES MUST BE SCENIC VIEWS, LANDSCAPES, OR ARCHITECTURE WITHOUT ANY HUMANS OR PEOPLE IN THEM.

Format your response as JSON with the following structure:
{
    "media": [
        {
            "type": "image",
            "description": "Description for humans",
            "prompt": "Detailed prompt for image generation - must explicitly specify no humans or people, focusing on landscapes and scenic views"
        },
        {
            "type": "image",
            "description": "Description for humans",
            "prompt": "Detailed prompt for image generation - must explicitly specify no humans or people, focusing on landscapes and scenic views"
        }
    ]
}

Suggest exactly 2 images that best complement the blog content.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Blog title: {blog_title}\nBlog content:\n{blog_content}\nDestination: {destination}\nInterests: {interests}"}
        ]
        
        response = llm.invoke(messages)
        try:
            # Try to parse the response as JSON
            json_response = json.loads(response.content)
            return json.dumps(json_response, indent=2)
        except json.JSONDecodeError:
            # If response is not valid JSON, return an error message
            return json.dumps({
                "error": "Could not parse media suggestions",
                "raw_response": response.content
            }, indent=2)


def init_portia_config():
    """Initialize Portia configuration with available AI model."""
    # Try loading keys from environment
    load_dotenv()
    global OPENAI_API_KEY
    global GEMINI_API_KEY
    
    if not OPENAI_API_KEY:
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    
    if not GEMINI_API_KEY and GEMINI_AVAILABLE:
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
    
    # First try to see which API has working access
    openai_working = False
    gemini_working = False
    
    # Check OpenAI access
    if OPENAI_API_KEY:
        try:
            # Test OpenAI with a minimal request
            client = OpenAI(api_key=OPENAI_API_KEY)
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            openai_working = True
            print("OpenAI API access confirmed.")
        except Exception as e:
            print(f"OpenAI API test failed: {e}")
    
    # Check Gemini access
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            # Test Gemini with a minimal request
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            model.generate_content("Hello")
            gemini_working = True
            print("Gemini API access confirmed.")
        except Exception as e:
            print(f"Gemini API test failed: {e}")
    
    # Choose the working API
    if gemini_working:
        # Prefer Gemini if it's working
        print("Using Gemini for blog generation.")
        config = Config.from_default(
            llm_provider=LLMProvider.GOOGLE_GENERATIVE_AI,
            llm_model_name=LLMModel.GEMINI_2_0_FLASH,
            google_api_key=GEMINI_API_KEY,
            default_log_level="INFO"
        )
    elif openai_working:
        # Fall back to OpenAI if Gemini isn't working
        print("Using OpenAI for blog generation.")
        config = Config.from_default(
            llm_provider=LLMProvider.OPENAI,
            llm_model_name=LLMModel.GPT_3_5_TURBO,
            openai_api_key=OPENAI_API_KEY,
            default_log_level="INFO"
        )
    else:
        print("No working API keys found for either Gemini or OpenAI.")
        print("Please check your API keys and network connection.")
        exit(1)
    
    return config


def create_blog_from_portia_results(blog_json, media_json):
    """Convert Portia tool results to BlogContent object."""
    try:
        blog_data = json.loads(blog_json) if isinstance(blog_json, str) else blog_json
        media_data = json.loads(media_json) if isinstance(media_json, str) else media_json
        
        # Create media suggestions from the media data
        media_suggestions = []
        if "media" in media_data:
            for item in media_data["media"]:
                media_suggestions.append(
                    MediaSuggestion(
                        description=item["description"],
                        prompt=item["prompt"],
                        type=item["type"],
                        url=None,
                        generator="portia"
                    )
                )
        
        # Create the blog content object
        blog_content = BlogContent(
            title=blog_data.get("title", "Travel Blog"),
            introduction=blog_data.get("introduction", ""),
            paragraphs=blog_data.get("paragraphs", []),
            conclusion=blog_data.get("conclusion", ""),
            media_suggestions=media_suggestions,
            generator="portia"
        )
        
        return blog_content
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error creating blog from Portia results: {e}")
        # Create a fallback blog
        return BlogContent(
            title="Travel Blog",
            introduction="Welcome to my travel blog.",
            paragraphs=["This blog was generated with some difficulties."],
            conclusion="Thank you for reading!",
            media_suggestions=[],
            generator="fallback"
        )


def main():
    # Load environment variables
    load_dotenv()
    
    # Example user from the provided data
    amina = UserData(
        name="Amina Yusuf",
        age_range="35~44",
        gender="Female",
        nationality="Nigerian",
        destination="Kyoto, Japan",
        interests="Cherry blossom",
        future_travel_wish="Walk the Camino de Santiago in Spain",
        special_requirements="24/7 hospital access",
        budget="$1500",
        currency_preference="Local currency",
        travel_preference="Travel only",
        issues="No issues"
    )
    
    try:
        # Initialize Portia with available AI model
        config = init_portia_config()
        
        # Set up tools registry
        tools = DefaultToolRegistry(config=config) + InMemoryToolRegistry.from_local_tools([
            BlogGenerationTool(), MediaSuggestionTool()
        ])
        
        # Create Portia instance
        portia = Portia(config=config, tools=tools, execution_hooks=CLIExecutionHooks())
        
        print("Generating blog content with Portia...")
        
        # Create plan for generating blog content and media suggestions
        plan = portia.plan(f"""
        Generate a personalized travel blog for a user with the following details:
        Name: {amina.name}
        Age Range: {amina.age_range}
        Gender: {amina.gender}
        Nationality: {amina.nationality}
        Destination: {amina.destination}
        Interests: {amina.interests}
        Future Travel Wish: {amina.future_travel_wish}
        Special Requirements: {amina.special_requirements or "None"}
        Budget: {amina.budget or "Not specified"}
        Currency Preference: {amina.currency_preference or "Not specified"}
        Travel Preference: {amina.travel_preference or "Not specified"}
        Issues: {amina.issues or "None"}

        First, generate the blog content with appropriate title, introduction, paragraphs, and conclusion.
        Then, suggest media (images) that would complement the blog.
        """)
        
        # Execute the plan
        result = portia.run_plan(plan)
        print("Blog generation complete!")
        
        # Extract blog data and media suggestions from the result
        blog_result = None
        media_result = None
        
        for step in result.steps:
            if step.tool_id == "blog_generation":
                blog_result = step.output
            elif step.tool_id == "media_suggestion":
                media_result = step.output
        
        if blog_result:
            # Convert Portia results to BlogContent
            blog = create_blog_from_portia_results(blog_result, media_result or {"media": []})
            
            # Process the media suggestions to generate actual media content
            # Test both APIs to see which one works
            use_gemini = GEMINI_AVAILABLE and GEMINI_API_KEY is not None
            
            media_gen = MediaGenerator(
                openai_client=OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None, 
                use_gemini=use_gemini
            )
            
            # Generate the actual media from the suggestions
            processed_media = []
            for media in blog.media_suggestions:
                if media.type == "image":
                    processed_media.append(media_gen.generate_image(media.prompt, media.description))
                else:
                    processed_media.append(media)
            
            blog.media_suggestions = processed_media
            
            # Display blog content in console
            display_blog_console(blog)
            
            # Generate HTML blog and open in browser
            print("Generating HTML blog...")
            html_gen = HtmlGenerator(blog, amina)
            blog_path = html_gen.generate_html()
            
            # Open the generated blog in the default web browser
            try:
                print(f"Opening blog in web browser: {blog_path}")
                webbrowser.open('file://' + os.path.abspath(blog_path))
            except Exception as e:
                print(f"Could not open browser: {e}")
                print(f"Please open the file manually: {blog_path}")
        else:
            raise Exception("Failed to generate blog content with Portia.")
            
    except Exception as e:
        print(f"Error using Portia for blog generation: {e}")
        print("Falling back to template-based generation...")
        
        # Fall back to the original template-based method
        # First test which API is available
        openai_working = False
        gemini_working = False
        
        if OPENAI_API_KEY:
            try:
                OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                openai_working = True
            except Exception:
                pass
        
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                genai.GenerativeModel('gemini-pro').generate_content("Hello")
                gemini_working = True
            except Exception:
                pass
        
        # Use whichever API is working
        use_gemini = gemini_working
        generator = BlogGenerator(
            openai_api_key=OPENAI_API_KEY if openai_working else None, 
            use_gemini=use_gemini
        )
        
        if openai_working or gemini_working:
            try:
                print(f"Using {'Gemini' if use_gemini else 'OpenAI'} for fallback blog generation")
                blog = generator.generate_blog(amina)
            except Exception as e2:
                print(f"API-based generation failed: {e2}")
                print("Using template-based generation as last resort")
                blog = generator._generate_with_templates(amina)
        else:
            print("No working APIs found. Using template-based generation")
            blog = generator._generate_with_templates(amina)
        
        display_blog_console(blog)
        
        # Generate HTML blog and open in browser
        print("Generating HTML blog...")
        html_gen = HtmlGenerator(blog, amina)
        blog_path = html_gen.generate_html()
        
        # Open the generated blog in the default web browser
        try:
            print(f"Opening blog in web browser: {blog_path}")
            webbrowser.open('file://' + os.path.abspath(blog_path))
        except Exception as e:
            print(f"Could not open browser: {e}")
            print(f"Please open the file manually: {blog_path}")
    
    print("\nThis demo shows how personalized travel blog content can be generated with Portia and interactive media.")
    print("In a full implementation, you could:")
    print("  - Create a web app for users to input their travel details")
    print("  - Use DALL-E or Gemini to generate personalized images")
    print("  - Connect to video APIs for custom video generation")
    print("  - Allow sharing to social media platforms")
    print("  - Create printable PDF versions of the blog")


if __name__ == "__main__":
    main()
