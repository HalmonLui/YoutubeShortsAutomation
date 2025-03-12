import os
import streamlit as st
import pandas as pd
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

# Initialize variables for video URLs
videos = None

# URL input container
url_container = st.container()
with url_container:
    if input_method == "YouTube Playlist":
        url_input = st.text_input(
            "Enter YouTube Playlist URL",
            key="playlist_url",
            help="Paste a YouTube playlist URL here"
        )
        if url_input and not validate_url(url_input):
            st.error("Please enter a valid YouTube URL")
    else:
        url_input = st.text_input(
            "Enter Google Sheets URL",
            key="sheets_url",
            help="Paste a Google Sheets URL here"
        )

# Add start button - enabled as soon as there's any text in the URL field
start_button = st.button(
    "Start Processing",
    type="primary",
    disabled=not bool(url_input),
    help="Click to start processing videos"
)

if start_button:
    # Get videos based on input method
    if input_method == "YouTube Playlist":
        if validate_url(url_input):
            videos = get_playlist_videos(url_input)
        else:
            st.error("Please enter a valid YouTube URL")
    else:
        sheets_client = setup_google_sheets(dev_mode)
        videos = get_spreadsheet_videos(sheets_client, url_input)

    # Process videos if available
    if videos:
        st.subheader("Processing Videos")
        
        # Create output directory
        output_dir = ensure_directory("downloads")
        
        # Initialize YouTube service
        youtube_service = get_youtube_service(dev_mode)
        
        # Process videos and get results
        processed_videos = process_videos(videos, youtube_service, output_dir, config)
        
        # Display results in a table
        if processed_videos:
            st.subheader("Processed Videos Summary")
            st.write(f"Total videos processed: {len(processed_videos)}")
            
            try:
                # Create DataFrame
                df = pd.DataFrame(processed_videos)
                st.write("DataFrame created with columns:", df.columns.tolist())
                
                # Get all columns including pattern search columns
                base_columns = ["Starting Number", "Scheduled Date", "Uploaded Video URL", "Channel Name", "Original Video URL"]
                pattern_columns = [col for col in df.columns if col not in base_columns]
                
                # Combine base columns with pattern columns at the end
                all_columns = base_columns + pattern_columns
                
                # Reorder columns
                df = df[all_columns]
                
                # Create column configuration
                column_config = {
                    "Starting Number": st.column_config.NumberColumn(
                        "Starting Number",
                        help="Template number used for the video"
                    ),
                    "Scheduled Date": st.column_config.TextColumn(
                        "Scheduled Date",
                        help="Scheduled release date and time (EST)"
                    ),
                    "Uploaded Video URL": st.column_config.TextColumn(
                        "Uploaded Video URL",
                        help="Link to the uploaded video"
                    ),
                    "Channel Name": st.column_config.TextColumn(
                        "Channel Name",
                        help="Original channel name"
                    ),
                    "Original Video URL": st.column_config.TextColumn(
                        "Original Video URL",
                        help="Link to the original video"
                    )
                }
                
                # Add configuration for pattern search columns
                for col in pattern_columns:
                    column_config[col] = st.column_config.TextColumn(
                        col,
                        help=f"Pattern match result for {col}"
                    )
                
                # Display the table with highlighting
                st.dataframe(
                    df,
                    column_config=column_config,
                    hide_index=True,
                    use_container_width=True
                )
                
                # Add download button for the entire table
                st.write("")  # Add some spacing
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download Summary as CSV",
                    csv,
                    "processed_videos.csv",
                    "text/csv",
                    key='download-csv',
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error displaying results table: {str(e)}")
                st.write("Raw data:", processed_videos)
        else:
            st.warning("No videos were processed successfully")
    elif videos is not None:  # Only show error if videos were attempted to be fetched
        st.error("No videos found in the provided URL")
elif not url_input:
    st.info("Enter a YouTube playlist URL or Google Sheets URL to get started") 