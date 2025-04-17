#!/usr/bin/env python
"""
UI utility functions for WanderMatch application.
Contains functions for displaying information to the user through the terminal.
"""
import os
from typing import Dict, Any, Optional, Tuple, List

def clear_screen():
    """Clear the terminal screen for better readability."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text, emoji="[HEADER]", color="blue", centered=True):
    """Print a formatted header with emoji."""
    try:
        if centered:
            # Calculate width based on terminal size or default to 80
            try:
                terminal_width = os.get_terminal_size().columns
            except:
                terminal_width = 80
            
            # Center the text
            line = f"[HEADER] {text} [HEADER]"
            padding = (terminal_width - len(line)) // 2
            if padding > 0:
                print(" " * padding + line)
            else:
                print(line)
        else:
            print(f"[HEADER] {text}")
    except UnicodeEncodeError:
        # Fallback for terminals that don't support emojis
        print(f"== {text} ==")

def print_subheader(text):
    """Print a formatted subheader."""
    print(f"== {text} ==")

def print_info(text):
    """Print information text."""
    print(f"[INFO] {text}")

def print_success(text):
    """Print success text."""
    print(f"[SUCCESS] {text}")

def print_warning(text):
    """Print warning text."""
    print(f"[WARNING] {text}")

def print_error(text):
    """Print error text."""
    print(f"[ERROR] {text}")

def input_prompt(prompt_text, default=None):
    """Display a styled input prompt with optional default value."""
    if default:
        user_input = input(f"[INPUT] {prompt_text} (default: {default}): ")
        return user_input if user_input else default
    else:
        return input(f"[INPUT] {prompt_text}: ")

def print_progress(text, emoji="[PROGRESS]", color="blue"):
    """Print a progress message."""
    print(f"[PROGRESS] {text}") 