import os
import time
import json
import traceback

class LLMService:
    """
    Service class to handle interactions with various LLM providers
    with fallback mechanisms and error handling.
    """
    
    def answer_question(self, question, context=None):
        """
        Try multiple LLM providers in sequence for answering the question.
        
        Args:
            question (str): The user's question
            context (dict): Optional context with route and partner info
            
        Returns:
            dict: Response with answer and provider information
        """
        # Log the question and context
        print(f"Answering question: {question}")
        if context:
            print(f"With context: {json.dumps(context, indent=2)}")
        
        # Try OpenAI first
        try:
            # Check if API key is available
            if "OPENAI_API_KEY" not in os.environ:
                print("OpenAI API key not found in environment variables")
                raise ValueError("OpenAI API key not found")
                
            result = self.answer_with_openai(question, context)
            return {
                "success": True,
                "answer": result,
                "provider": "OpenAI GPT-3.5"
            }
        except Exception as e:
            print(f"OpenAI error: {str(e)}")
            print(traceback.format_exc())
            
            # Try Gemini next
            try:
                # Check if API key is available
                if "GEMINI_API_KEY" not in os.environ:
                    print("Gemini API key not found in environment variables")
                    raise ValueError("Gemini API key not found")
                    
                result = self.answer_with_gemini(question, context)
                return {
                    "success": True,
                    "answer": result,
                    "provider": "Google Gemini 1.5"
                }
            except Exception as e:
                print(f"Gemini error: {str(e)}")
                print(traceback.format_exc())
                
                # If all fails, use fallback approach
                return {
                    "success": True,
                    "answer": "Failed to call LLMs, this is a fallback approach. Please try again later or check if API keys are properly configured.",
                    "provider": "fallback"
                }
    
    def answer_with_openai(self, question, context=None):
        """
        Generate an answer using OpenAI's GPT-3.5 model
        
        Args:
            question (str): The question to answer
            context (dict): Optional context with route and partner info
            
        Returns:
            str: The generated answer
        """
        try:
            from openai import OpenAI
            
            # Initialize OpenAI client
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Prepare system message based on available context
            system_message = "You are a helpful travel assistant that provides concise and accurate information about travel destinations, routes, and tips."
            
            # Prepare user message with context
            user_message = question
            
            # Add context if available
            context_info = []
            if context:
                if "route" in context and context["route"]:
                    route = context["route"]
                    context_info.append(f"Route Information: {route.get('origin', 'Unknown')} to {route.get('destination', 'Unknown')} via {route.get('mode', 'Unknown')}")
                    
                if "partner" in context and context["partner"]:
                    partner = context["partner"]
                    context_info.append(f"Travel Partner: {partner.get('name', 'Unknown')} from {partner.get('nationality', 'Unknown')}")
            
            if context_info:
                user_message = f"{question}\n\nContext:\n" + "\n".join(context_info)
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract and return answer
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in OpenAI answer generation: {str(e)}")
            raise
    
    def answer_with_gemini(self, question, context=None):
        """
        Generate an answer using Google's Gemini model
        
        Args:
            question (str): The question to answer
            context (dict): Optional context with route and partner info
            
        Returns:
            str: The generated answer
        """
        try:
            import google.generativeai as genai
            
            # Configure the API
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            
            # Prepare the prompt with context
            prompt = question
            
            # Add context if available
            context_info = []
            if context:
                if "route" in context and context["route"]:
                    route = context["route"]
                    context_info.append(f"Route Information: {route.get('origin', 'Unknown')} to {route.get('destination', 'Unknown')} via {route.get('mode', 'Unknown')}")
                    
                if "partner" in context and context["partner"]:
                    partner = context["partner"]
                    context_info.append(f"Travel Partner: {partner.get('name', 'Unknown')} from {partner.get('nationality', 'Unknown')}")
            
            if context_info:
                prompt = f"{question}\n\nContext:\n" + "\n".join(context_info)
            
            # Set up the model
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config={
                    "temperature": 0.7,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 500,
                }
            )
            
            # Generate content
            response = model.generate_content(prompt)
            
            # Extract and return answer
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in Gemini answer generation: {str(e)}")
            raise 