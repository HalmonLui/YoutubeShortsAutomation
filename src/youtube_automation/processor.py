import os
import streamlit as st
from datetime import datetime, timedelta
import pytz
from moviepy.editor import VideoFileClip, concatenate_videoclips
from .api.youtube_api import download_video, upload_video
from .utils.helpers import format_title, format_description, clean_filename

def process_videos(videos, youtube_service, output_dir, config):
    """
    Process a list of videos according to the given configuration.
    
    Args:
        videos: List of video dictionaries containing video URLs
        youtube_service: YouTube API service instance
        output_dir: Directory to save downloaded videos
        config: Dictionary containing processing configuration:
            - title_template: Template for video titles
            - description_template: Template for video descriptions
            - template_number: Starting number for templates
            - append_enabled: Whether to append videos
            - append_video_path: Path to video to append
            - schedule_enabled: Whether to schedule releases
            - schedule_config: Dictionary with scheduling configuration:
                - start_date: Start date for releases
                - start_time: Start time for releases
                - hours_between: Hours between releases
    """
    for i, video in enumerate(videos, 1):
        video_url = video.get('youtube_url')
        if not video_url:
            continue
        
        with st.expander(f"Processing video {i}"):
            st.write(f"Video URL: {video_url}")
            
            # Format title and description
            current_number = config['template_number']
            title = format_title(config['title_template'], number=current_number, original_url=video_url)
            description = format_description(config['description_template'], number=current_number, original_url=video_url)
            
            # Calculate scheduled time if enabled
            scheduled_time = None
            if config.get('schedule_enabled'):
                schedule_config = config['schedule_config']
                est_tz = pytz.timezone('US/Eastern')
                base_time = datetime.combine(schedule_config['start_date'], schedule_config['start_time'])
                base_time = est_tz.localize(base_time)
                scheduled_time = base_time + timedelta(hours=(i-1) * schedule_config['hours_between'])
                st.write(f"Scheduled release time (EST): {scheduled_time.strftime('%Y-%m-%d %I:%M %p')}")
            
            # Increment template number
            config['template_number'] += 1
            
            st.write(f"Title: {title}")
            st.write(f"Description: {description}")
            
            # Process the video
            success = process_single_video(
                video_url=video_url,
                output_dir=output_dir,
                youtube_service=youtube_service,
                title=title,
                description=description,
                scheduled_time=scheduled_time,
                append_enabled=config.get('append_enabled', False),
                append_video_path=config.get('append_video_path'),
                video_number=i
            )
            
            if not success:
                st.error("Skipping to next video...")
                continue

def process_single_video(video_url, output_dir, youtube_service, title, description, 
                        scheduled_time=None, append_enabled=False, append_video_path=None, 
                        video_number=1):
    """Process a single video including download, append, and upload."""
    
    # Download video
    video_filename = clean_filename(f"video_{video_number}.mp4")
    video_path = os.path.join(output_dir, video_filename)
    
    if not os.path.exists(video_path):
        video_path = download_video(video_url, output_dir)
        if not video_path:
            return False
        
        # Append video if enabled
        if append_enabled and append_video_path and os.path.exists(append_video_path):
            try:
                st.write("Appending video...")
                # Load both videos
                main_clip = VideoFileClip(video_path)
                append_clip = VideoFileClip(append_video_path)
                
                # Concatenate videos
                final_clip = concatenate_videoclips([main_clip, append_clip])
                
                # Save the final video
                final_path = os.path.join(output_dir, f"final_{video_filename}")
                final_clip.write_videofile(final_path)
                
                # Close clips to free up memory
                main_clip.close()
                append_clip.close()
                final_clip.close()
                
                # Update video path to the concatenated version
                video_path = final_path
                st.success("Video appended successfully!")
                
            except Exception as e:
                st.error(f"Error appending video: {str(e)}")
                return False
        
        # Upload video
        st.write("Uploading video...")
        video_id = upload_video(youtube_service, video_path, title, description, scheduled_time=scheduled_time)
        if not video_id:
            return False
    
    return True 