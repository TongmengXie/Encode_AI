#!/usr/bin/env python
"""
UI utility functions for WanderMatch application.
Contains functions for displaying information to the user through the terminal.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from typing import Dict, Any, Optional, Tuple, List

# Initialize console
console = Console()

def clear_screen():
    """Clear the terminal screen for better readability."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text, emoji="🌍", color="blue", centered=True):
    """Print a formatted header with emoji."""
    if centered:
        console.print(f"[bold {color}]{emoji} {text} {emoji}[/bold {color}]", justify="center")
    else:
        console.print(f"[bold {color}]{emoji} {text}[/bold {color}]")

def print_subheader(text):
    """Print a formatted subheader."""
    console.print(f"[bold cyan]== {text} ==[/bold cyan]")

def print_info(text):
    """Print information text."""
    console.print(f"[cyan]ℹ️ {text}[/cyan]")

def print_success(text):
    """Print success text."""
    console.print(f"[green]✅ {text}[/green]")

def print_warning(text):
    """Print warning text."""
    console.print(f"[yellow]⚠️ {text}[/yellow]")

def print_error(text):
    """Print error text."""
    console.print(f"[red]❌ {text}[/red]")

def input_prompt(prompt_text, default=None):
    """Display a styled input prompt with optional default value."""
    return Prompt.ask(f"[bold blue]?[/bold blue] {prompt_text}", default=default)

def print_progress(text, emoji="🔄", color="blue"):
    """Print a progress message."""
    console.print(f"[{color}]{emoji} {text}[/{color}]") 