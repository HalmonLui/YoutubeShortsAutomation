import streamlit as st
from datetime import datetime
import pytz
import os

# Configure the Streamlit page
st.set_page_config(page_title="YouTube Shorts Automation", page_icon="🎥")

def initialize_session_state():
    """Initialize session state variables."""
    if 'dev_mode' not in st.session_state:
        st.session_state.dev_mode = True
    if 'template_number' not in st.session_state:
        st.session_state.template_number = 1
    if 'last_processed_number' not in st.session_state:
        st.session_state.last_processed_number = None
    if 'title_template' not in st.session_state:
        st.session_state.title_template = "Short #{number} - Repost"
    if 'description_template' not in st.session_state:
        st.session_state.description_template = """Original video: {originalUrl}

#shorts #viral #trending"""

def render_header():
    """Render the application header."""
    st.title("YouTube Shorts Automation")

def get_input_method():
    """Get the selected input method."""
    return st.radio(
        "Choose input method:",
        ["YouTube Playlist", "Google Sheets"],
        horizontal=True
    )

def render_template_section():
    """Render the template configuration section."""
    st.subheader("Template Configuration")
    st.info("""Available template variables:
- {number}: Template number (automatically increments for each video)
- {originalUrl}: Original video URL""")

    # Template Manager
    with st.expander("📝 Template Manager", expanded=False):
        from .templates import render_template_manager
        render_template_manager()

    # Template input fields
    col1, col2 = st.columns([3, 1])
    with col1:
        title_template = st.text_input(
            "Title Template",
            value=st.session_state.title_template,
            key='title_template_input',
            help="Enter the template for video titles"
        )
    with col2:
        template_number = st.number_input(
            "Starting Number",
            min_value=1,
            value=st.session_state.template_number,
            help="Set the starting number for video numbering. This will increment automatically.",
            key='template_number_input'
        )

    description_template = st.text_area(
        "Description Template",
        value=st.session_state.description_template,
        key='description_template_input',
        height=150,  # Approximately 5 lines
        help="Enter the template for video descriptions. Supports multiple lines."
    )

    # Update session state
    st.session_state.title_template = title_template
    st.session_state.description_template = description_template
    if st.session_state.last_processed_number is None:
        st.session_state.template_number = template_number

    return {
        'title_template': title_template,
        'description_template': description_template,
        'template_number': template_number
    }

def render_append_section():
    """Render the video append configuration section."""
    st.subheader("Video Append Configuration")
    append_enabled = st.checkbox("Append video to downloads", value=False)
    append_video_path = None

    if append_enabled:
        append_video = st.file_uploader(
            "Upload video to append",
            type=['mp4'],
            help="This video will be appended to the end of each downloaded video"
        )
        if append_video:
            append_video_path = "append_video.mp4"
            with open(append_video_path, "wb") as f:
                f.write(append_video.getbuffer())
            st.success("Append video uploaded successfully!")

    return {
        'enabled': append_enabled,
        'video_path': append_video_path
    }

def render_schedule_section():
    """Render the release schedule configuration section."""
    st.subheader("Release Schedule Configuration")
    schedule_enabled = st.checkbox("Schedule video releases", value=False)
    schedule_config = None

    if schedule_enabled:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now(pytz.timezone('US/Eastern')).date(),
                help="Select the start date for video releases (EST)"
            )
        with col2:
            # Create a list of time options in 30-minute intervals
            time_options = []
            for hour in range(24):
                for minute in [0, 30]:
                    time_options.append(datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time())
            
            # Default to midnight (00:00)
            default_time_index = 0  # Index for 00:00
            
            start_time = st.selectbox(
                "Release Time (EST)",
                options=time_options,
                format_func=lambda x: x.strftime("%I:%M %p"),  # Format as "HH:MM AM/PM"
                index=default_time_index,
                help="Select the time for video releases (EST). Times are shown in 30-minute intervals."
            )
        
        hours_between = st.number_input(
            "Hours between releases",
            min_value=1,
            value=24,
            help="Number of hours to wait between video releases"
        )

        schedule_config = {
            'start_date': start_date,
            'start_time': start_time,
            'hours_between': hours_between
        }

    return {
        'enabled': schedule_enabled,
        'config': schedule_config
    }

def get_processing_config():
    """Get the complete processing configuration."""
    template_config = render_template_section()
    append_config = render_append_section()
    schedule_config = render_schedule_section()

    return {
        'title_template': template_config['title_template'],
        'description_template': template_config['description_template'],
        'template_number': template_config['template_number'],
        'append_enabled': append_config['enabled'],
        'append_video_path': append_config['video_path'],
        'schedule_enabled': schedule_config['enabled'],
        'schedule_config': schedule_config['config']
    } 