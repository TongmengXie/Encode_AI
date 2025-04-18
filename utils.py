#!/usr/bin/env python
"""
Utility functions for WanderMatch application
"""
import os
import sys
import json
import time
import hashlib
import pickle
from typing import Dict, Any, Optional, Tuple, List

# Helper print functions
def print_header(text, emoji="[HEADER]", color="blue", centered=False):
    try:
        if centered:
            # Calculate width based on terminal size or default to 80
            try:
                terminal_width = os.get_terminal_size().columns
            except:
                terminal_width = 80
            
            # Center the text
            line = f"{emoji} {text} {emoji}"
            padding = (terminal_width - len(line)) // 2
            if padding > 0:
                print(" " * padding + line)
            else:
                print(line)
        else:
            print(f"{emoji} {text}")
    except UnicodeEncodeError:
        # Fallback for terminals that don't support emojis
        print(f"== {text} ==")

def print_info(text, emoji="[INFO]", color="cyan"):
    print(f"{emoji} {text}")

def print_success(text, emoji="[SUCCESS]", color="green"):
    print(f"{emoji} {text}")

def print_error(text, emoji="[ERROR]", color="red"):
    print(f"{emoji} {text}")

def print_warning(text, emoji="[WARNING]", color="yellow"):
    print(f"{emoji} {text}")

def print_progress(text, emoji="[PROGRESS]", color="blue"):
    print(f"{emoji} {text}")

# Environment variable helper
def get_env_var(key, default=None):
    """Read an environment variable, falling back to reading directly from .env file if needed"""
    value = os.getenv(key)
    if not value:
        # Try to load directly from .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            try:
                                env_key, env_value = line.strip().split('=', 1)
                                if env_key == key:
                                    return env_value
                            except ValueError:
                                # Skip lines that don't follow key=value format
                                continue
            except Exception as e:
                print_warning(f"Error reading .env file: {str(e)}")
    return value if value else default

# Cache management functions
def get_pool_file_hash(user_pool_path):
    """Calculate a hash of the user pool file for cache validation."""
    hash_md5 = hashlib.md5()
    with open(user_pool_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_cached_embeddings(user_pool_path, cache_dir):
    """Load cached embeddings for the user pool if available."""
    # Generate cache path
    cache_file = os.path.join(cache_dir, "user_pool_embeddings.pkl")
    hash_file = os.path.join(cache_dir, "user_pool_hash.txt")
    
    # Print absolute paths
    print_info(f"Looking for embedding cache at: {os.path.abspath(cache_file)}")
    print_info(f"Looking for hash file at: {os.path.abspath(hash_file)}")
    
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

def save_embeddings_cache(pool_embedded_lists, user_pool_path, cache_dir):
    """Save embeddings for the user pool to cache."""
    # Generate cache path
    cache_file = os.path.join(cache_dir, "user_pool_embeddings.pkl")
    hash_file = os.path.join(cache_dir, "user_pool_hash.txt")
    
    # Print absolute paths
    print_info(f"Saving embedding cache to: {os.path.abspath(cache_file)}")
    print_info(f"Saving hash file to: {os.path.abspath(hash_file)}")
    
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