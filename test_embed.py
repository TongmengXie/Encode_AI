import os
import sys
from dotenv import load_dotenv
import traceback

# Add directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
get_user_info_dir = os.path.join(current_dir, "get_user_info")
if get_user_info_dir not in sys.path:
    sys.path.insert(0, get_user_info_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Load environment variables
load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

print("=== OpenAI API Key Test ===")
if openai_api_key:
    print("OpenAI API key found in environment variables")
    print(f"Key starts with: {openai_api_key[:5]}...")
    print(f"Key length: {len(openai_api_key)}")
else:
    print("ERROR: OpenAI API key not found in environment variables")

try:
    print("\n=== Testing OpenAI API ===")
    from openai import OpenAI
    client = OpenAI(api_key=openai_api_key)
    
    # Test simple embedding
    print("Testing embedding generation...")
    test_text = "This is a test for embedding generation"
    
    response = client.embeddings.create(
        input=test_text,
        model="text-embedding-ada-002"
    )
    
    if response and response.data:
        print(f"✅ Embedding created successfully! Vector dimension: {len(response.data[0].embedding)}")
    else:
        print("❌ Failed to create embedding")
        
except Exception as e:
    print(f"❌ Error testing OpenAI API: {str(e)}")
    print(traceback.format_exc())

try:
    print("\n=== Testing embed_info module ===")
    import get_user_info.embed_info as embed_info_module
    
    # Test loading user pool
    print("Testing load_user_pool function...")
    user_pool = embed_info_module.load_user_pool()
    if user_pool is not None:
        print(f"✅ User pool loaded successfully with {len(user_pool)} entries")
    else:
        print("❌ Failed to load user pool")
    
    # Test getting latest user answer
    print("\nTesting get_latest_user_answer function...")
    filepath, user_df, user_ts = embed_info_module.get_latest_user_answer()
    if filepath:
        print(f"✅ Latest user answer loaded from: {filepath}")
    else:
        print("❌ Failed to load latest user answer")
        
except Exception as e:
    print(f"❌ Error testing embed_info module: {str(e)}")
    print(traceback.format_exc()) 