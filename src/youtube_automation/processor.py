import os
import streamlit as st
from datetime import datetime, timedelta
import pytz
import time
import re
from moviepy.editor import VideoFileClip, concatenate_videoclips
from .api.youtube_api import download_video, upload_video
from .utils.helpers import format_title, format_description, clean_filename

def extract_pattern_match(text, pattern):
    """
    Extract pattern matches from text, where {#} in the pattern matches any number.
    Returns a list of all matches found, empty list if none found.
    """
    if not text or not pattern:
        st.write("❌ Text or pattern is empty")
        return []
    
    try:
        # Replace {#} with regex pattern for numbers and make case insensitive
        pattern_regex = pattern.replace('{#}', r'(\d+)')
        st.write(f"🔍 Text to search: '{text}'")
        st.write(f"🔍 Pattern before conversion: '{pattern}'")
        st.write(f"🔍 Pattern after conversion: '{pattern_regex}'")
        
        # Case insensitive search for all matches
        matches = re.finditer(pattern_regex, text, re.IGNORECASE)
        found_matches = [match.group(0) for match in matches]
        
        if found_matches:
            st.write(f"✅ Found matches: {found_matches}")
            return found_matches
        st.write("❌ No matches found")
        return []
    except Exception as e:
        st.error(f"Error in pattern matching: {str(e)}")
        return []

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    if '/shorts/' in url:
        # Handle shorts URL format
        match = re.search(r'/shorts/([a-zA-Z0-9_-]{11})', url)
    else:
        # Handle regular video URL format
        match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})(?:\?|&|/|$)', url)
    
    if match:
        return match.group(1)
    return None

def get_video_info(video_url, youtube_service=None):
    """Get video title and description from YouTube using yt-dlp."""
    try:
        import yt_dlp
        st.write(f"📥 Fetching info for video: {video_url}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_info = {
                'title': info.get('title', ''),
                'description': info.get('description', '')
            }
            
        st.write(f"📝 Video title: '{video_info['title']}'")
        st.write(f"📝 Video description: '{video_info['description']}'")
        return video_info
        
    except Exception as e:
        st.error(f"Could not fetch video info: {str(e)}")
        return {'title': '', 'description': ''}

def process_videos(videos, youtube_service, output_dir, config):
    """Process a list of videos according to the given configuration."""
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
            
            # Get original video info for pattern matching
            original_video_info = get_video_info(video_url, youtube_service)
            st.write("📥 Original video information:")
            st.write(f"Title: {original_video_info['title']}")
            st.write(f"Description: {original_video_info['description']}")
            
            # Format title and description for the new video
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
            
            # Create processed_video dictionary before processing to store pattern matches
            processed_video = {
                'Starting Number': current_number,
                'Scheduled Date': scheduled_time.strftime('%Y-%m-%d %I:%M %p EST') if scheduled_time else 'Immediate',
                'Original Video URL': video_url,
                'Uploaded Video URL': 'Processing'  # Will be updated after successful upload
            }
            
            # Add pattern matches from original video info
            if config.get('search_patterns'):
                st.write("🔎 Starting pattern matching process...")
                st.write(f"📝 Original video title to search: '{original_video_info['title']}'")
                
                for pattern_config in config['search_patterns']:
                    pattern = pattern_config['pattern']
                    column_name = pattern_config['column_name']
                    st.write(f"\n📌 Processing pattern: '{pattern}' for column: '{column_name}'")
                    
                    # First, search in title
                    title_matches = extract_pattern_match(original_video_info['title'], pattern)
                    if title_matches:
                        # Use first title match if multiple found
                        match = title_matches[0]
                        st.write(f"✅ Found match in title: '{match}' (prioritized)")
                        processed_video[column_name] = match
                        st.write(f"✅ Set column '{column_name}' to value: '{match}'")
                    else:
                        st.write("⏳ No match in title, checking description...")
                        # If no title match, search in description
                        desc_matches = extract_pattern_match(original_video_info['description'], pattern)
                        if desc_matches:
                            # Use first description match
                            match = desc_matches[0]
                            st.write(f"✅ Found match in description: '{match}' (first match)")
                            processed_video[column_name] = match
                            st.write(f"✅ Set column '{column_name}' to value: '{match}'")
                        else:
                            processed_video[column_name] = ''
                            st.write(f"❌ No matches found, set column '{column_name}' to empty string")
                    
                    st.write(f"👉 Final value for column '{column_name}': '{processed_video[column_name]}'")
            
            # Process the video
            success = process_single_video(
                video_url=video_url,
                output_dir=output_dir,
                youtube_service=youtube_service,
                title=title,
                description=description,
                privacy_status="private",
                scheduled_time=scheduled_time,
                append_enabled=config.get('append_enabled', False),
                append_video_path=config.get('append_video_path'),
                video_number=i
            )
            
            if success:
                # Update the upload URL after successful processing
                processed_video['Uploaded Video URL'] = f"https://youtube.com/watch?v={success}" if isinstance(success, str) else 'Processing'
                processed_videos.append(processed_video)
                st.success(f"Successfully processed video {i}")
                processed_count += 1
            
            # Increment template number
            config['template_number'] += 1
            
            st.write(f"New Title: {title}")
            st.write(f"New Description: {description}")
    
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
                        privacy_status="private", scheduled_time=None, append_enabled=False, 
                        append_video_path=None, video_number=1):
    """Process a single video including download, append, and upload.
    
    Args:
        video_url (str): URL of the video to process
        output_dir (str): Directory to save downloaded videos
        youtube_service: Authenticated YouTube service instance
        title (str): Title for the uploaded video
        description (str): Description for the uploaded video
        privacy_status (str): One of 'private', 'public', 'unlisted'
        scheduled_time (datetime): When to publish the video (if privacy_status is 'scheduled')
        append_enabled (bool): Whether to append another video
        append_video_path (str): Path to video to append
        video_number (int): Number in sequence for this video
    
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
                
                # Get dimensions
                main_width, main_height = main_clip.size
                append_width, append_height = append_clip.size
                
                st.write(f"Main video resolution: {main_width}x{main_height}")
                st.write(f"Append video resolution: {append_width}x{append_height}")
                
                # Resize append clip if resolutions don't match
                if main_width != append_width or main_height != append_height:
                    st.write(f"Resizing append video to match main video resolution: {main_width}x{main_height}")
                    append_clip = append_clip.resize(
                        width=main_width,
                        height=main_height
                    )
                
                # Concatenate videos
                final_clip = concatenate_videoclips([main_clip, append_clip])
                
                # Save the final video with the same resolution
                final_path = os.path.join(output_dir, f"final_{video_filename}")
                st.write("Saving final video...")
                final_clip.write_videofile(
                    final_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True
                )
                
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
        video_id = upload_video(
            youtube_service, 
            video_path, 
            title, 
            description, 
            privacy_status=privacy_status if privacy_status != "scheduled" else "private",
            scheduled_time=scheduled_time
        )
        if not video_id:
            return False
        return video_id
    
    return False 