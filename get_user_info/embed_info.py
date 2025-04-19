import pandas as pd
import numpy as np
import os
import sys
import pickle
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Get the current directory (where embed_info.py is located)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the parent directory
PARENT_DIR = os.path.dirname(CURRENT_DIR)

# Functions for pretty printing
def print_header(text, emoji="[HEADER]", color="blue"):
    try:
        print(f"\n{emoji} {text} {emoji}")
        print("=" * (len(text) + 10))
    except UnicodeEncodeError:
        print(f"\n== {text} ==")
        print("=" * (len(text) + 10))

def print_info(text, emoji="[INFO]", color="cyan"):
    try:
        print(f"{emoji} {text}")
    except UnicodeEncodeError:
        print(f"INFO: {text}")

def print_success(text, emoji="[SUCCESS]", color="green"):
    try:
        print(f"{emoji} {text}")
    except UnicodeEncodeError:
        # Fallback for Windows systems with GBK encoding issues
        print(f"SUCCESS: {text}")

def print_error(text, emoji="[ERROR]", color="red"):
    try:
        print(f"{emoji} {text}")
    except UnicodeEncodeError:
        print(f"ERROR: {text}")

def print_warning(text, emoji="[WARNING]", color="yellow"):
    try:
        print(f"{emoji} {text}")
    except UnicodeEncodeError:
        print(f"WARNING: {text}")

def print_match(idx, name, nationality, age, score, interests):
    print(f"\nMatch #{idx+1}:")
    print(f"- Name: {name}")
    print(f"- Nationality: {nationality}")
    print(f"- Age Group: {age}")
    print(f"- Match Score: {score:.4f}")
    print(f"- Interests: {interests}")

# Step 0: set API key
# First try to load from parent directory
load_dotenv(os.path.join(PARENT_DIR, '.env'))
# Also try loading from current working directory
load_dotenv()

# Read environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print_error("OpenAI API key not found in environment variables.")
    print_info("Please make sure OPENAI_API_KEY is set in .env file.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)
print_success("OpenAI API key loaded successfully.")


def get_latest_user_answer():
    """
    Get the latest user answer file from the survey results directory.
    
    Returns:
        tuple: (csv_path, dataframe, timestamp)
    """
    # Load environment variables
    load_dotenv(os.path.join(PARENT_DIR, '.env'))
    
    # Use PROJECT_PATH from environment variables if available, consistent with server.py
    PROJECT_PATH = os.getenv("PROJECT_PATH", PARENT_DIR)
    
    # Define directories
    backend_dir = os.path.normpath(os.path.join(CURRENT_DIR, "backend"))
    user_info_match_dir = os.path.normpath(os.path.join(PROJECT_PATH, "UserInfo_and_Match"))
    survey_results_dir = os.path.normpath(os.path.join(user_info_match_dir, "survey_results"))
    
    print_info(f"Looking for user answers in:")
    print_info(f"- Survey Results: {os.path.abspath(survey_results_dir)}")
    print_info(f"- Backend: {os.path.abspath(backend_dir)}")
    
    # First try the survey_results_dir
    csv_files = []
    if os.path.exists(survey_results_dir):
        csv_files = [f for f in os.listdir(survey_results_dir) if f.startswith("user_answer") and f.endswith(".csv")]
    
    # If no files found, check backend directory for backwards compatibility
    if not csv_files and os.path.exists(backend_dir):
        csv_files = [f for f in os.listdir(backend_dir) if f.startswith("user_answer") and f.endswith(".csv")]
        if csv_files:
            # Sort by modified time (newest first)
            csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(backend_dir, x)), reverse=True)
            latest_file = csv_files[0]
            filepath = os.path.normpath(os.path.join(backend_dir, latest_file))
            print_info(f"Using latest file from backend directory: {latest_file}")
        else:
            print_error("No user answer files found in any location.")
            return None, None, None
    elif csv_files:
        # Sort by modified time (newest first)
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(survey_results_dir, x)), reverse=True)
        latest_file = csv_files[0]
        filepath = os.path.normpath(os.path.join(survey_results_dir, latest_file))
        print_info(f"Using latest file from survey results directory: {latest_file}")
    else:
        print_error("No user answer files found in any location.")
        return None, None, None
    
    # Extract timestamp
    try:
        # Format is typically user_answer_YYYYMMDD_HHMMSS.csv
        parts = latest_file.split("_")
        if len(parts) >= 4:
            user_ts = parts[2] + parts[3].split(".")[0]
        else:
            # Fallback to current timestamp
            user_ts = datetime.now().strftime("%Y%m%d%H%M%S")
    except:
        user_ts = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Load the CSV
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
        print_success("Successfully loaded user answers.")
        
        # Display horizontal format with field: value pairs
        print("\n=== USER PROFILE ===")
        
        # Use a single row since it's typically just one user answer
        user_data = df.iloc[0].to_dict() if not df.empty else {}
        
        # Get maximum field name length for alignment
        max_field_length = max([len(field) for field in user_data.keys()]) if user_data else 0
        
        # Print each field: value pair
        for field, value in user_data.items():
            print(f"{field:{max_field_length + 2}}: {value}")
            
        print("=" * 50)
        print(f"File: {filepath}")
        print(f"Timestamp: {user_ts}")
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="ISO-8859-1")
        print_success("Successfully loaded user answers (using ISO-8859-1 encoding).")
        
        # Also display formatted output for ISO-8859-1 encoding
        print("\n=== USER PROFILE (ISO-8859-1 encoding) ===")
        
        # Use a single row since it's typically just one user answer
        user_data = df.iloc[0].to_dict() if not df.empty else {}
        
        # Get maximum field name length for alignment
        max_field_length = max([len(field) for field in user_data.keys()]) if user_data else 0
        
        # Print each field: value pair
        for field, value in user_data.items():
            print(f"{field:{max_field_length + 2}}: {value}")
            
        print("=" * 50)
        print(f"File: {filepath}")
        print(f"Timestamp: {user_ts}")
    
    return filepath, df, user_ts


def load_user_pool():
    """
    Load the user pool data.
    
    Returns:
        DataFrame: The user pool data with a filepath attribute
    """
    # First try to load from the current directory
    user_pool_path = os.path.join(CURRENT_DIR, "user_pool.csv")
    
    # If not found, try the parent directory
    if not os.path.exists(user_pool_path):
        user_pool_path = os.path.join(PARENT_DIR, "user_pool.csv")
    
    # If still not found, search in common directories
    if not os.path.exists(user_pool_path):
        for potential_dir in [CURRENT_DIR, PARENT_DIR, os.getcwd()]:
            for root, dirs, files in os.walk(potential_dir):
                if "user_pool.csv" in files:
                    user_pool_path = os.path.join(root, "user_pool.csv")
                    break
    
    if not os.path.exists(user_pool_path):
        print_error("User pool file not found.")
        return None
    
    print_info(f"Loading user pool from: {user_pool_path}")
    
    try:
        user_pool = pd.read_csv(user_pool_path, encoding="utf-8")
        print_success(f"User pool loaded with {len(user_pool)} potential matches.")
    except UnicodeDecodeError:
        user_pool = pd.read_csv(user_pool_path, encoding="ISO-8859-1")
        print_success(f"User pool loaded with {len(user_pool)} potential matches (using ISO-8859-1 encoding).")
    
    # Store the file path for caching purposes
    user_pool.filepath = user_pool_path
    
    return user_pool


# Function to embed answers
def embed_answer_list(answer_list):
    """
    Create embeddings for a list of answers using OpenAI's API.
    
    Args:
        answer_list (list): List of string answers to embed
        
    Returns:
        list: List of embeddings
    """
    response = client.embeddings.create(
        input=answer_list,
        model="text-embedding-ada-002"
    )
    return [r.embedding for r in response.data]


# Calculate cosine similarity between two vectors
def cosine_similarity(a, b):
    """
    Calculate cosine similarity between two vectors.
    OpenAI vectors are already normalized, so we can just use dot product.
    
    Args:
        a (list): First vector
        b (list): Second vector
        
    Returns:
        float: Cosine similarity between a and b
    """
    return np.dot(a, b)


# Find top matches
def get_top_matches(similarity_matrix, weights, top_k=3):
    """
    Given a similarity matrix and question weights, return the top-k most similar users.

    Args:
        similarity_matrix (list of list of float): Per-question cosine similarities.
        weights (list of float): Weights for each question (must match question count).
        top_k (int): Number of top users to return.

    Returns:
        list of tuples: [(user_index, weighted_score), ...] sorted by descending similarity.
    """
    weighted_scores = []
    for row in similarity_matrix:
        score = sum([s * w for s, w in zip(row, weights)])
        weighted_scores.append(score)

    top_users = sorted(enumerate(weighted_scores), key=lambda x: x[1], reverse=True)[:top_k]
    return top_users


# Save similarity matrix to a CSV file
def save_similarity_matrix(similarity_matrix, output_dir=None, output_name=None):
    """
    Save the similarity matrix to a CSV file.

    Args:
        similarity_matrix (list of list of float): Matrix of per-question similarities.
        output_dir (str): Directory to save the matrix (defaults to results directory)
        output_name (str): Name of the output file (defaults to similarity_matrix_timestamp.csv)
        
    Returns:
        str: Path to the saved file
    """
    if output_dir is None:
        # Create results directory in the current directory if it doesn't exist
        results_dir = os.path.join(CURRENT_DIR, "results")
        os.makedirs(results_dir, exist_ok=True)
        output_dir = results_dir
    
    if output_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"similarity_matrix_{timestamp}.csv"
    
    output_path = os.path.join(output_dir, output_name)
    
    df = pd.DataFrame(similarity_matrix)
    df.index = [f"User {i+1}" for i in range(len(df))]
    df.columns = [f"Q{j+1}" for j in range(len(df.columns))]
    df.to_csv(output_path, encoding='utf-8')
    
    print_success(f"Similarity matrix saved to: {output_path}")
    return output_path


# Save top matches to a CSV file
def save_top_matches(top_matches, user_pool, output_dir=None, output_name=None):
    """
    Save the top matches to a CSV file.

    Args:
        top_matches (list of tuples): [(user_index, weighted_score), ...].
        user_pool (DataFrame): DataFrame containing user data.
        output_dir (str): Directory to save the matrix (defaults to results directory)
        output_name (str): Name of the output file (defaults to top_matches_timestamp.csv)
        
    Returns:
        str: Path to the saved file
    """
    if output_dir is None:
        # Create results directory in the current directory if it doesn't exist
        results_dir = os.path.join(CURRENT_DIR, "results")
        os.makedirs(results_dir, exist_ok=True)
        output_dir = results_dir
    
    if output_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"top_matches_{timestamp}.csv"
    
    output_path = os.path.join(output_dir, output_name)
    
    # Extract data and scores
    top_users_data = []
    for idx, score in top_matches:
        user_data = user_pool.iloc[idx].to_dict()
        user_data['match_score'] = score
        top_users_data.append(user_data)
    
    # Create DataFrame and save - explicitly use UTF-8 encoding
    df = pd.DataFrame(top_users_data)
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print_success(f"Top matches saved to: {output_path}")
    return output_path


def get_pool_file_hash(user_pool_path):
    """
    Calculate a hash of the user pool file for cache validation.
    
    Args:
        user_pool_path (str): Path to user pool CSV file
        
    Returns:
        str: MD5 hash of the file
    """
    hash_md5 = hashlib.md5()
    with open(user_pool_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_cached_embeddings(user_pool_path):
    """
    Load cached embeddings for the user pool if available.
    
    Args:
        user_pool_path (str): Path to the user pool CSV file
        
    Returns:
        tuple: (embeddings_list, is_cache_valid)
    """
    # Generate cache path
    cache_dir = os.path.dirname(user_pool_path)
    cache_file = os.path.join(cache_dir, "user_pool_embeddings.pkl")
    hash_file = os.path.join(cache_dir, "user_pool_hash.txt")
    
    # Print absolute paths
    print_info(f"Looking for embedding cache at: {os.path.abspath(cache_file)}")
    print_info(f"Looking for hash file at: {os.path.abspath(hash_file)}")
    print_info(f"User pool path: {os.path.abspath(user_pool_path)}")
    
    # Check if cache files exist
    if not os.path.exists(cache_file) or not os.path.exists(hash_file):
        print_info("Embeddings cache not found.")
        return None, False
    
    # Check if user pool has changed since cache was created
    current_hash = get_pool_file_hash(user_pool_path)
    with open(hash_file, "r") as f:
        cached_hash = f.read().strip()
    
    if current_hash != cached_hash:
        print_warning("User pool has changed since embeddings were cached.")
        return None, False
    
    # Load cached embeddings
    try:
        with open(cache_file, "rb") as f:
            pool_embedded_lists = pickle.load(f)
        print_success(f"Loaded cached embeddings for {len(pool_embedded_lists)} users from {os.path.abspath(cache_file)}")
        return pool_embedded_lists, True
    except Exception as e:
        print_warning(f"Error loading cached embeddings: {str(e)}")
        return None, False


def save_embeddings_cache(pool_embedded_lists, user_pool_path):
    """
    Save embeddings for the user pool to cache.
    
    Args:
        pool_embedded_lists (list): List of embeddings for each user in the pool
        user_pool_path (str): Path to the user pool CSV file
    """
    # Generate cache path
    cache_dir = os.path.dirname(user_pool_path)
    cache_file = os.path.join(cache_dir, "user_pool_embeddings.pkl")
    hash_file = os.path.join(cache_dir, "user_pool_hash.txt")
    
    # Print absolute paths
    print_info(f"Saving embedding cache to: {os.path.abspath(cache_file)}")
    print_info(f"Saving hash file to: {os.path.abspath(hash_file)}")
    print_info(f"Using user pool from: {os.path.abspath(user_pool_path)}")
    
    # Save embeddings
    try:
        with open(cache_file, "wb") as f:
            pickle.dump(pool_embedded_lists, f)
        
        # Save hash of current user pool file
        current_hash = get_pool_file_hash(user_pool_path)
        with open(hash_file, "w") as f:
            f.write(current_hash)
            
        print_success(f"Saved embeddings for {len(pool_embedded_lists)} users to cache at {os.path.abspath(cache_file)}")
    except Exception as e:
        print_warning(f"Error saving embeddings cache: {str(e)}")


def run_matching(user_answers=None, weights=None, top_k=5, output_dir=None, silent=False):
    """
    Run the matching process for user answers against the user pool.
    
    Args:
        user_answers (list, optional): List of user answers. If None, will load from latest file.
        weights (list, optional): List of weights for each question. If None, uses default weights.
        top_k (int): Number of top matches to return.
        output_dir (str, optional): Directory to save output files. If None, uses results directory.
        silent (bool): Whether to suppress printing of matches.
        
    Returns:
        list: List of top matches as [(user_index, score), ...]
    """
    print_header("RUNNING PARTNER MATCHING", emoji="[MATCHING]", color="magenta")
    
    # Set default weights if not provided
    if weights is None:
        weights = [0.0, 0.2, 0.1, 0.3, 0.1, 0.3, 0.3, 0.1, 0.3, 0.1, 0.1, 0.1]
    
    # Set default output directory to results subfolder
    if output_dir is None:
        results_dir = os.path.join(CURRENT_DIR, "results")
        os.makedirs(results_dir, exist_ok=True)
        output_dir = results_dir
    
    # Load user answers if not provided
    if user_answers is None:
        _, user_df, user_ts = get_latest_user_answer()
        if user_df is None:
            print_error("Could not load user answers.")
            return None
        
        user_answers = user_df.iloc[0].tolist()
    
    # Load user pool
    user_pool = load_user_pool()
    if user_pool is None:
        print_error("Could not load user pool.")
        return None
    
    print_info(f"User pool loaded successfully with {len(user_pool)} potential partners.")
    
    # Create embeddings for user answers
    print_header("CREATING EMBEDDINGS", emoji="[EMBEDDING]", color="blue")
    print_info("Creating embeddings for user answers...")
    sample_embedded_list = []
    for value in user_answers:
        if isinstance(value, str):
            sample_embedded = embed_answer_list([value])
            sample_embedded_list.append(sample_embedded[0])
        else:
            # Convert non-string values to strings
            value_str = str(value) if not pd.isna(value) else "N/A"
            sample_embedded = embed_answer_list([value_str])
            sample_embedded_list.append(sample_embedded[0])
    
    # Get user pool file path to use for caching
    if hasattr(user_pool, 'filepath'):
        user_pool_path = user_pool.filepath
        print_info(f"Using user pool filepath from DataFrame: {os.path.abspath(user_pool_path)}")
    else:
        # Find where the user pool was loaded from
        potential_paths = [
            os.path.join(CURRENT_DIR, "user_pool.csv"),
            os.path.join(PARENT_DIR, "user_pool.csv")
        ]
        print_info(f"Searching for user_pool.csv in the following locations:")
        for path in potential_paths:
            print_info(f"  - {os.path.abspath(path)} (Exists: {os.path.exists(path)})")
        
        for potential_path in potential_paths:
            if os.path.exists(potential_path):
                user_pool_path = potential_path
                print_info(f"Found user_pool.csv at: {os.path.abspath(user_pool_path)}")
                break
        else:
            # If we can't determine the path, use a path in the current directory
            user_pool_path = os.path.join(os.getcwd(), "user_pool.csv")
            print_warning(f"Could not find user_pool.csv in expected locations. Using current directory: {os.path.abspath(user_pool_path)}")
    
    # Try to load cached embeddings
    pool_embedded_lists, is_cache_valid = load_cached_embeddings(user_pool_path)
    
    # Create embeddings for user pool if no valid cache
    if not is_cache_valid:
        print_info("Creating new embeddings for potential partners...")
        pool_embedded_lists = []
        
        # Basic output
        for idx in range(len(user_pool)):
            print(f"  Embedding potential partner {idx+1}/{len(user_pool)}")
            old_user_answer = user_pool.iloc[idx].tolist()
            embed_old_user_answer = []
            for col_idx, value in enumerate(old_user_answer):
                column_name = user_pool.columns[col_idx]
                if isinstance(value, str):
                    pool_embedded = embed_answer_list([value])
                    embed_old_user_answer.append(pool_embedded[0])
                elif pd.isna(value):
                    pool_embedded = embed_answer_list(["N/A"])
                    embed_old_user_answer.append(pool_embedded[0])
                else:
                    pool_embedded = embed_answer_list([str(value)])
                    embed_old_user_answer.append(pool_embedded[0])
            pool_embedded_lists.append(embed_old_user_answer)
        
        # Save the embeddings for future use
        save_embeddings_cache(pool_embedded_lists, user_pool_path)
    else:
        print_info("Using cached embeddings for potential partners.")
    
    # Calculate similarity matrix
    print_header("CALCULATING MATCH SCORES", emoji="[CALCULATING]", color="cyan")
    print_info("Calculating similarities between user and potential partners...")
    similarity_matrix = []
    for pool_user_embeds in pool_embedded_lists:
        row_similarity = []
        for i in range(min(len(sample_embedded_list), len(pool_user_embeds))):
            sim = cosine_similarity(sample_embedded_list[i], pool_user_embeds[i])
            row_similarity.append(sim)
        similarity_matrix.append(row_similarity)
    
    # Get top matches
    print_info(f"Finding top {top_k} matches...")
    top_matches = get_top_matches(similarity_matrix, weights, top_k=top_k)
    
    # Save results to the results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_similarity_matrix(similarity_matrix, output_dir, f"similarity_matrix_{timestamp}.csv")
    save_top_matches(top_matches, user_pool, output_dir, f"top_matches_{timestamp}.csv")
    
    # Print results only if not silent
    if not silent:
        print_header("TOP TRAVEL PARTNER MATCHES", emoji="[PARTNERS]", color="green")
        for i, (idx, score) in enumerate(top_matches):
            user_row = user_pool.iloc[idx]
            name = user_row["real_name"] if "real_name" in user_row else f"User {idx+1}"
            nationality = user_row["nationality"] if "nationality" in user_row else "Unknown"
            age_group = user_row["age_group"] if "age_group" in user_row else "Unknown"
            bucket_list = user_row["bucket_list"] if "bucket_list" in user_row else "Unknown interests"
            
            print_match(i, name, nationality, age_group, score, bucket_list)
    
    return top_matches


# Run as a standalone script
if __name__ == "__main__":
    print_header("TRAVEL PARTNER MATCHING", emoji="[SEARCH]", color="magenta")
    
    # Get the latest user answer file
    filepath, user_df, user_ts = get_latest_user_answer()
    
    if filepath:
        print_info(f"Using user answers from {filepath}")
        user_answers = user_df.iloc[0].tolist()
        
        # Define weights for different questions
        weights = [0.0, 0.2, 0.1, 0.3, 0.1, 0.3, 0.3, 0.1, 0.3, 0.1, 0.1, 0.1]
        
        # Run matching
        top_matches = run_matching(user_answers, weights, top_k=3)
        
        if top_matches:
            print_success("Matching completed successfully!")
        else:
            print_error("Matching failed.")
    else:
        print_error("No user answer files found. Please run the questionnaire first.")

