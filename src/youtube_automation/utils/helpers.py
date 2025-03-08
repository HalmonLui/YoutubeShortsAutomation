import os
import re
import streamlit as st

def format_title(template, number=None, original_url=None):
    """Format the title template with provided variables."""
    title = template
    if number is not None:
        title = title.replace('{number}', str(number))
    if original_url is not None:
        title = title.replace('{originalUrl}', original_url)
    return title

def format_description(template, number=None, original_url=None):
    """Format the description template with provided variables."""
    description = template
    if number is not None:
        description = description.replace('{number}', str(number))
    if original_url is not None:
        description = description.replace('{originalUrl}', original_url)
    return description

def validate_url(url):
    """Validate if the URL is a valid YouTube video or playlist URL."""
    youtube_pattern = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
    if not re.match(youtube_pattern, url):
        st.error("Invalid YouTube URL format")
        return False
    return True

def ensure_directory(path):
    """Ensure that a directory exists, create it if it doesn't."""
    if not os.path.exists(path):
        os.makedirs(path)
        st.info(f"Created directory: {path}")
    return path

def clean_filename(filename):
    """Clean a filename by removing invalid characters."""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Ensure the filename is not empty
    if not filename:
        filename = 'unnamed'
    return filename 