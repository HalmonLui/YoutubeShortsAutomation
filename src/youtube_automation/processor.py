import os
import streamlit as st
from datetime import datetime, timedelta
import pytz
import time
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
        config: Dictionary containing processing configuration
        
    Returns:
        List of dictionaries containing processed video information
    """
    processed_videos = []
    total_videos = len(videos)
    
    # Create progress tracking elements
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_text = st.empty()
    
    # Initialize timing variables
    start_time = time.time()
    processed_count = 0
    
    for i, video in enumerate(videos, 1):
        video_url = video.get('youtube_url')
        if not video_url:
            continue
        
        # Update progress and timing information
        progress = (i - 1) / total_videos
        progress_bar.progress(progress)
        
        elapsed_time = time.time() - start_time
        if processed_count > 0:
            avg_time_per_video = elapsed_time / processed_count
            remaining_videos = total_videos - i + 1
            estimated_time = remaining_videos * avg_time_per_video
            time_text.text(f"⏱️ Elapsed: {format_time(elapsed_time)} | Estimated remaining: {format_time(estimated_time)}")
        else:
            time_text.text(f"⏱️ Elapsed: {format_time(elapsed_time)} | Calculating remaining time...")
        
        status_text.text(f"Processing video {i} of {total_videos}: {video_url}")
        
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
            
            if success:
                processed_video = {
                    'Starting Number': current_number,
                    'Scheduled Date': scheduled_time.strftime('%Y-%m-%d %I:%M %p EST') if scheduled_time else 'Immediate',
                    'Original Video URL': video_url,
                    'Uploaded Video URL': f"https://youtube.com/watch?v={success}" if isinstance(success, str) else 'Processing'
                }
                processed_videos.append(processed_video)
                st.success(f"Successfully processed video {i}")
                processed_count += 1
            
            # Increment template number
            config['template_number'] += 1
            
            st.write(f"Title: {title}")
            st.write(f"Description: {description}")
    
    # Update final progress
    progress_bar.progress(1.0)
    final_elapsed = time.time() - start_time
    time_text.text(f"✅ Completed in {format_time(final_elapsed)} | Processed {processed_count} videos")
    status_text.text("Processing complete!")
    
    return processed_videos

def format_time(seconds):
    """Format time in seconds to a readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def process_single_video(video_url, output_dir, youtube_service, title, description, 
                        scheduled_time=None, append_enabled=False, append_video_path=None, 
                        video_number=1):
    """Process a single video including download, append, and upload.
    
    Returns:
        str: Video ID if successful, False otherwise
    """
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
        return video_id
    
    return False 