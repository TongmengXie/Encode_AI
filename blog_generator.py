#!/usr/bin/env python
"""
Blog generation module for WanderMatch.
Contains functions for generating travel blogs and converting them to HTML.
"""
import os
import sys
import time
import json
import re
import markdown
from datetime import datetime
from typing import Dict, Any, List
from ui_utils import print_header, print_info, print_success, print_warning, print_error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_blog_post(user_info, partner_info, route_info):
    """
    Generate a blog post for the travel route.
    
    Args:
        user_info: Dictionary containing user information
        partner_info: Dictionary containing partner information (or None if solo)
        route_info: Dictionary containing route details
        
    Returns:
        Dictionary containing blog generation results
    """
    print_header("Creating Your Travel Blog", emoji="✍️")
    
    # Ensure output directories exist
    output_dir = os.path.join(WORKSPACE_DIR, "wandermatch_output")
    blogs_dir = os.path.join(output_dir, "blogs")
    os.makedirs(blogs_dir, exist_ok=True)
    
    # Try different blog generation methods
    blog_content = None
    html_content = None
    
    # Check for API keys
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    # Attempt to generate blog with LLM
    if openai_api_key or gemini_api_key:
        try:
            print_info("Generating personalized travel blog with AI...")
            blog_content = generate_blog_with_llm(
                user_info, 
                partner_info, 
                route_info,
                openai_api_key=openai_api_key,
                gemini_api_key=gemini_api_key
            )
            if blog_content:
                print_success("Successfully generated AI blog post!")
        except Exception as e:
            print_warning(f"Error generating AI blog: {str(e)}")
    
    # If LLM generation failed, use template-based generation
    if not blog_content:
        print_info("Using template-based blog generation...")
        blog_content = generate_blog_with_template(user_info, partner_info, route_info)
        if blog_content:
            print_success("Successfully generated blog from template!")
    
    # Convert blog content to HTML
    if blog_content:
        html_content = convert_to_html(blog_content, user_info, partner_info, route_info)
    else:
        print_error("Failed to generate blog content.")
        return {"success": False, "error": "Failed to generate blog content"}
    
    # Generate timestamps for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save markdown file
    md_filename = f"travel_blog_{timestamp}.md"
    md_path = os.path.join(blogs_dir, md_filename)
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(blog_content)
    
    # Save HTML file
    html_filename = f"travel_blog_{timestamp}.html"
    html_path = os.path.join(blogs_dir, html_filename)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print_success(f"Blog post saved to: {md_path}")
    print_success(f"HTML version saved to: {html_path}")
    
    # Try to open HTML file in browser
    try:
        import webbrowser
        webbrowser.open('file://' + os.path.abspath(html_path))
        print_success("Blog opened in your browser!")
    except Exception as e:
        print_warning(f"Could not open browser: {str(e)}")
    
    return {
        "success": True,
        "md_content": blog_content,
        "html_content": html_content,
        "md_path": md_path,
        "html_path": html_path
    }

def generate_blog_with_llm(user_info, partner_info, route_info, openai_api_key=None, gemini_api_key=None):
    """
    Generate a blog post using AI language models.
    
    Args:
        user_info: Dictionary with user information
        partner_info: Dictionary with partner information (or None)
        route_info: Dictionary with route details
        openai_api_key: OpenAI API key
        gemini_api_key: Gemini API key
        
    Returns:
        String containing markdown blog content
    """
    # Try Gemini first if API key is available
    if gemini_api_key:
        try:
            blog_content = generate_blog_with_gemini(user_info, partner_info, route_info, gemini_api_key)
            if blog_content:
                return blog_content
        except Exception as e:
            print_warning(f"Gemini blog generation failed: {str(e)}")
    
    # Fall back to OpenAI if Gemini fails or isn't available
    if openai_api_key:
        try:
            blog_content = generate_blog_with_openai(user_info, partner_info, route_info, openai_api_key)
            if blog_content:
                return blog_content
        except Exception as e:
            print_warning(f"OpenAI blog generation failed: {str(e)}")
    
    # If both fail, return None
    return None

def generate_blog_with_gemini(user_info, partner_info, route_info, api_key):
    """
    Generate a blog post using Google's Gemini API.
    
    Args:
        user_info: Dictionary with user information
        partner_info: Dictionary with partner information (or None)
        route_info: Dictionary with route details
        api_key: Gemini API key
        
    Returns:
        String containing markdown blog content
    """
    try:
        import google.generativeai as genai
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Set up the model
        generation_config = {
            "temperature": 0.8,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 8192,
        }
        
        # Extract information for the prompt
        user_name = user_info.get("name", "Traveler")
        partner_name = partner_info.get("name", "my travel companion") if partner_info else None
        origin = user_info.get("origin_city", "our starting point")
        destination = user_info.get("destination_city", "our destination")
        transport_mode = route_info.get("transport_mode", "various transportation")
        
        # Format attractions
        attractions = route_info.get("attractions", [])
        attraction_text = ""
        if attractions:
            attraction_text = "Main attractions visited:\n"
            for attraction in attractions:
                if isinstance(attraction, dict):
                    name = attraction.get("name", "")
                    if name:
                        attraction_text += f"- {name}\n"
        
        # Create prompt based on solo or partner travel
        if partner_info:
            travel_context = f"I, {user_name}, traveled with {partner_name} from {origin} to {destination}."
        else:
            travel_context = f"I, {user_name}, traveled solo from {origin} to {destination}."
        
        # Construct the full prompt
        prompt = f"""
        Write a detailed travel blog post in markdown format about this trip:
        
        {travel_context}
        We traveled by {transport_mode}.
        
        {attraction_text}
        
        The blog should:
        1. Have an engaging title with a markdown heading
        2. Include 5-7 sections with appropriate subheadings
        3. Tell a story about the journey, include vivid descriptions
        4. Mention specific locations, foods, and experiences
        5. Include some cultural or historical insights about the destination
        6. End with a personal reflection or advice for future travelers
        
        Write in first person, in a conversational and personal style. 
        Format the blog properly in markdown with headers, paragraphs, and occasional emphasis.
        DO NOT include fake dates, prices, or URLs.
        """
        
        # Generate content with Gemini
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        response = model.generate_content(prompt)
        
        # Return the blog content
        return response.text
    
    except Exception as e:
        print_error(f"Error generating blog with Gemini: {str(e)}")
        return None

def generate_blog_with_openai(user_info, partner_info, route_info, api_key):
    """
    Generate a blog post using OpenAI API.
    
    Args:
        user_info: Dictionary with user information
        partner_info: Dictionary with partner information (or None)
        route_info: Dictionary with route details
        api_key: OpenAI API key
        
    Returns:
        String containing markdown blog content
    """
    try:
        from openai import OpenAI
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Extract information for the prompt
        user_name = user_info.get("name", "Traveler")
        partner_name = partner_info.get("name", "my travel companion") if partner_info else None
        origin = user_info.get("origin_city", "our starting point")
        destination = user_info.get("destination_city", "our destination")
        transport_mode = route_info.get("transport_mode", "various transportation")
        
        # Format attractions
        attractions = route_info.get("attractions", [])
        attraction_text = ""
        if attractions:
            attraction_text = "Main attractions visited:\n"
            for attraction in attractions:
                if isinstance(attraction, dict):
                    name = attraction.get("name", "")
                    if name:
                        attraction_text += f"- {name}\n"
        
        # Create prompt based on solo or partner travel
        if partner_info:
            travel_context = f"I, {user_name}, traveled with {partner_name} from {origin} to {destination}."
        else:
            travel_context = f"I, {user_name}, traveled solo from {origin} to {destination}."
        
        # Construct the full prompt
        prompt = f"""
        Write a detailed travel blog post in markdown format about this trip:
        
        {travel_context}
        We traveled by {transport_mode}.
        
        {attraction_text}
        
        The blog should:
        1. Have an engaging title with a markdown heading
        2. Include 5-7 sections with appropriate subheadings
        3. Tell a story about the journey, include vivid descriptions
        4. Mention specific locations, foods, and experiences
        5. Include some cultural or historical insights about the destination
        6. End with a personal reflection or advice for future travelers
        
        Write in first person, in a conversational and personal style. 
        Format the blog properly in markdown with headers, paragraphs, and occasional emphasis.
        DO NOT include fake dates, prices, or URLs.
        """
        
        # Generate content with OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a talented travel writer creating engaging blog posts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        # Return the blog content
        return response.choices[0].message.content
    
    except Exception as e:
        print_error(f"Error generating blog with OpenAI: {str(e)}")
        return None

def generate_blog_with_template(user_info, partner_info, route_info):
    """
    Generate a blog post using a template-based approach.
    
    Args:
        user_info: Dictionary with user information
        partner_info: Dictionary with partner information (or None)
        route_info: Dictionary with route details
        
    Returns:
        String containing markdown blog content
    """
    try:
        # Extract information for the template
        user_name = user_info.get("name", "Traveler")
        partner_name = partner_info.get("name", "my travel companion") if partner_info else None
        origin = user_info.get("origin_city", "our origin")
        destination = user_info.get("destination_city", "our destination")
        transport_mode = route_info.get("transport_mode", "various transportation")
        
        # Format attractions as bullet points
        attractions = route_info.get("attractions", [])
        attraction_bullets = ""
        if attractions:
            for attraction in attractions:
                if isinstance(attraction, dict):
                    name = attraction.get("name", "")
                    description = attraction.get("description", "")
                    if name:
                        attraction_bullets += f"* **{name}** - {description}\n"
        
        # Get current date for the blog
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Create blog title based on destinations
        blog_title = f"# Journey from {origin} to {destination}: An Unforgettable Adventure"
        
        # Introduction section
        if partner_info:
            intro = f"""
## Introduction

On {current_date}, {user_name} and {partner_name} embarked on an exciting journey from {origin} to {destination}. 
We decided to travel by {transport_mode}, which offered us a unique perspective on the landscapes and cultures we encountered along the way.
This blog captures our experiences, the places we visited, and the memories we created together.
"""
        else:
            intro = f"""
## Introduction

On {current_date}, I ({user_name}) embarked on a solo adventure from {origin} to {destination}.
I chose to travel by {transport_mode}, which gave me the freedom to explore at my own pace and immerse myself in the local culture.
This blog is a recollection of my journey, the places I discovered, and the insights I gained along the way.
"""
        
        # The journey section
        journey = f"""
## The Journey Begins

The journey from {origin} to {destination} was an adventure in itself. As we left the familiar streets of {origin} behind, 
a sense of excitement filled the air. The {transport_mode} journey offered spectacular views and comfortable travel.

## Arriving in {destination}

Upon arriving in {destination}, we were immediately struck by its unique character and atmosphere. 
The local architecture, the sounds, and the smells all contributed to our first impressions of this remarkable place.
"""
        
        # Attractions section
        attractions_section = f"""
## Must-Visit Attractions

During our stay in {destination}, we explored several notable attractions that showcase the city's rich history and culture:

{attraction_bullets or "* **Local Markets** - Vibrant gathering places with local products and crafts\n* **Historical Sites** - Ancient architecture that tells the story of the region\n* **Natural Wonders** - Breathtaking landscapes that capture the beauty of the area"}
"""
        
        # Food and culture section
        food_culture = f"""
## Local Cuisine and Culture

One of the highlights of our trip was experiencing the local cuisine. From street food vendors to upscale restaurants, 
{destination} offers a rich tapestry of flavors that reflect its cultural heritage.

The locals were welcoming and eager to share their traditions with visitors. We had the opportunity to participate 
in some cultural activities that gave us a deeper understanding of the local way of life.
"""
        
        # Conclusion section
        conclusion = f"""
## Reflections and Advice

This journey from {origin} to {destination} was more than just a trip; it was an opportunity to broaden our horizons 
and gain new perspectives. For anyone planning to visit {destination}, I recommend taking the time to explore 
beyond the tourist attractions and engage with the local community.

Remember to respect local customs, try the local cuisine, and be open to unexpected adventures – they often 
become the most memorable parts of the journey.

Until the next adventure!

_{user_name}_
"""
        
        # Combine all sections to create the complete blog
        blog_content = f"{blog_title}\n\n{intro}\n{journey}\n{attractions_section}\n{food_culture}\n{conclusion}"
        
        return blog_content
    
    except Exception as e:
        print_error(f"Error generating blog from template: {str(e)}")
        return "# My Travel Journey\n\nAn error occurred while generating the blog content."

def convert_to_html(blog_content, user_info, partner_info, route_info):
    """
    Convert markdown blog content to styled HTML.
    
    Args:
        blog_content: Markdown content as string
        user_info: Dictionary with user information
        partner_info: Dictionary with partner information (or None)
        route_info: Dictionary with route details
        
    Returns:
        String containing HTML content
    """
    try:
        # Extract information for the HTML template
        user_name = user_info.get("name", "Traveler")
        origin = user_info.get("origin_city", "Origin")
        destination = user_info.get("destination_city", "Destination")
        
        # Convert markdown to HTML
        html_body = markdown.markdown(blog_content)
        
        # HTML template with styling
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Blog: {origin} to {destination}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #2c3e50;
            color: white;
            border-radius: 5px;
        }}
        h1 {{
            color: #fff;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #2c3e50;
            margin-top: 30px;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #3498db;
        }}
        p {{
            margin-bottom: 20px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .author {{
            font-style: italic;
            text-align: right;
            margin-top: 40px;
            color: #7f8c8d;
        }}
        .metadata {{
            text-align: center;
            margin-top: 10px;
            font-size: 0.9em;
            color: #bdc3c7;
        }}
        blockquote {{
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #f2f2f2;
            border-left: 4px solid #e74c3c;
            font-style: italic;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul, ol {{
            margin-bottom: 20px;
        }}
        li {{
            margin-bottom: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Travel Blog</h1>
        <div class="metadata">From {origin} to {destination} • By {user_name}</div>
    </header>
    
    <main>
        {html_body}
    </main>
    
    <div class="footer">
        <p>Generated by WanderMatch • {datetime.now().strftime("%Y-%m-%d")}</p>
    </div>
</body>
</html>
"""
        
        return html_template
    
    except Exception as e:
        print_error(f"Error converting blog to HTML: {str(e)}")
        return f"<html><body><h1>Travel Blog</h1><p>Error generating HTML content: {str(e)}</p></body></html>"

def render_budget_breakdown(route_info):
    """
    Generate an HTML table showing budget breakdown.
    
    Args:
        route_info: Dictionary with route details
        
    Returns:
        String containing HTML table content
    """
    try:
        # Extract budget breakdown from route info
        budget = route_info.get("budget", {})
        if not budget or not isinstance(budget, dict):
            return "<p>Budget information not available.</p>"
        
        # Start HTML table
        html = """
        <div class="budget-section">
            <h3>Budget Breakdown</h3>
            <table class="budget-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Calculate total budget
        total = sum(budget.values())
        
        # Add rows for each budget category
        for category, amount in budget.items():
            percentage = (amount / total) * 100 if total > 0 else 0
            html += f"""
                <tr>
                    <td>{category}</td>
                    <td>${amount:.2f}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """
        
        # Close the table
        html += f"""
                </tbody>
                <tfoot>
                    <tr>
                        <td><strong>Total</strong></td>
                        <td><strong>${total:.2f}</strong></td>
                        <td>100%</td>
                    </tr>
                </tfoot>
            </table>
        </div>
        """
        
        return html
    
    except Exception as e:
        print_error(f"Error rendering budget breakdown: {str(e)}")
        return "<p>Error generating budget information.</p>"