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

try:
    print("=== Running Partner Matching Test ===")
    import get_user_info.embed_info as embed_info_module
    
    # Create output directory for partner matches
    partner_matches_dir = os.path.join(current_dir, "UserInfo_and_Match", "partner_matches")
    os.makedirs(partner_matches_dir, exist_ok=True)
    
    # Run the matching process
    print("Starting partner matching process...")
    top_matches = embed_info_module.run_matching(top_k=5, output_dir=partner_matches_dir)
    
    if top_matches:
        print(f"✅ Partner matching completed successfully!")
        print(f"Top {len(top_matches)} matches found:")
        
        # Get user pool to display match details
        user_pool = embed_info_module.load_user_pool()
        for i, (idx, score) in enumerate(top_matches):
            user_row = user_pool.iloc[idx]
            name = user_row.get("real_name", f"User {idx+1}")
            nationality = user_row.get("nationality", "Unknown")
            age_group = user_row.get("age_group", "Unknown")
            
            print(f"{i+1}. {name} ({nationality}, {age_group}) - Score: {score:.4f}")
    else:
        print("❌ Partner matching failed or returned no matches")
        
except Exception as e:
    print(f"❌ Error running partner matching: {str(e)}")
    print(traceback.format_exc()) 