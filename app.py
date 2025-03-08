import os
import streamlit as st
from datetime import datetime, timedelta
import pytz
from src.youtube_automation.services.api_services import (
    setup_google_sheets,
    get_youtube_service,
    get_playlist_videos,
    get_spreadsheet_videos
)
from src.youtube_automation.api.youtube_api import download_video, upload_video
from src.youtube_automation.utils.helpers import (
    format_title,
    format_description,
    validate_url,
    ensure_directory,
    clean_filename
)
from src.youtube_automation.templates import render_template_manager
from src.youtube_automation.ui import (
    initialize_session_state,
    render_header,
    get_input_method,
    get_processing_config
)
from src.youtube_automation.processor import process_videos

# Initialize the application
initialize_session_state()
render_header()

# Development mode toggle
dev_mode = st.sidebar.checkbox("Development Mode", value=st.session_state.dev_mode)
st.session_state.dev_mode = dev_mode

# Get input method
input_method = get_input_method()

# Get processing configuration
config = get_processing_config()

# Get videos based on input method
videos = None
if input_method == "YouTube Playlist":
    playlist_url = st.text_input("Enter YouTube Playlist URL")
    if playlist_url and validate_url(playlist_url):
        videos = get_playlist_videos(playlist_url)
else:
    spreadsheet_url = st.text_input("Enter Google Sheets URL")
    if spreadsheet_url:
        sheets_client = setup_google_sheets(dev_mode)
        videos = get_spreadsheet_videos(sheets_client, spreadsheet_url)

# Process videos if available
if videos:
    st.subheader("Processing Videos")
    
    # Create output directory
    output_dir = ensure_directory("downloads")
    
    # Initialize YouTube service
    youtube_service = get_youtube_service(dev_mode)
    
    # Process videos
    process_videos(videos, youtube_service, output_dir, config)
else:
    st.info("Enter a YouTube playlist URL or Google Sheets URL to get started") 