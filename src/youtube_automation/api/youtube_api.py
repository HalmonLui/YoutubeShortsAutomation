# Standard library imports
import os
import time

# Third-party imports
import streamlit as st
import pytz
import yt_dlp
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def download_video(url, output_path, max_retries=3):
    """
    Download a video from YouTube using yt-dlp with retry logic and better error handling.
    
    Args:
        url (str): YouTube video URL
        output_path (str): Directory to save the video
        max_retries (int): Maximum number of retry attempts
    """
    for attempt in range(max_retries):
        try:
            # Add progress information
            st.write(f"Attempting to download video (attempt {attempt + 1}/{max_retries})...")
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),  # Use video ID for consistent naming
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'ignoreerrors': True,
                'merge_output_format': 'mp4'
            }
            
            # Create yt-dlp object and get video info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video information first
                info = ydl.extract_info(url, download=False)
                if not info:
                    st.error("Could not get video information")
                    continue
                
                video_id = info.get('id')
                if not video_id:
                    st.error("Could not get video ID")
                    continue

                # Show video information
                st.info(f"""Video details:
- Title: {info.get('title', 'Unknown')}
- ID: {video_id}
- Duration: {info.get('duration', 0)} seconds
- Resolution: {info.get('height', 'Unknown')}p""")
                
                # Download the video
                st.write("Downloading video in highest quality available...")
                ydl.download([url])
                
                # Get the expected output filename
                expected_video_path = os.path.join(output_path, f"{video_id}.mp4")
                st.write(f"Looking for downloaded file at: {expected_video_path}")
                
                # Check if file exists
                if os.path.exists(expected_video_path):
                    st.success(f"Successfully downloaded video to {expected_video_path}")
                    return expected_video_path
                else:
                    # If the expected path doesn't exist, try to find any .mp4 file that was just created
                    mp4_files = [f for f in os.listdir(output_path) if f.endswith('.mp4')]
                    st.write(f"Found {len(mp4_files)} MP4 files in output directory: {mp4_files}")
                    
                    if mp4_files:
                        # Get the most recently created .mp4 file
                        latest_file = max([os.path.join(output_path, f) for f in mp4_files], 
                                        key=os.path.getctime)
                        st.success(f"Found downloaded video at alternate location: {latest_file}")
                        return latest_file
                    
                    st.error(f"Download completed but file not found in {output_path}")
                    st.write(f"Directory contents: {os.listdir(output_path)}")
                    continue
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle specific error cases
            if "private video" in error_msg:
                st.error("This video is private and cannot be accessed.")
            elif "copyright" in error_msg:
                st.error("This video is not available due to copyright restrictions.")
            elif "removed" in error_msg:
                st.error("This video has been removed or deleted.")
            elif "not available" in error_msg:
                st.error("This video is not available. It might be restricted in your region.")
            else:
                st.error(f"Error downloading video: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Progressive waiting: 2s, 4s, 6s
                st.warning(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                st.error("Maximum retry attempts reached. Could not download the video.")
                return None
    
    return None

def upload_video(youtube, video_path, title, description, privacy_status="private", scheduled_time=None):
    """Upload a video to YouTube.
    
    Args:
        youtube: Authenticated YouTube service instance
        video_path (str): Path to video file
        title (str): Video title
        description (str): Video description
        privacy_status (str): One of 'private', 'public', 'unlisted', or 'scheduled'
        scheduled_time (datetime): When to publish the video (if privacy_status is 'scheduled')
    
    Returns:
        str: Video ID if successful, None otherwise
    """
    try:
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': '22'  # People & Blogs category
            },
            'status': {
                'privacyStatus': 'private',  # Always start as private for scheduled videos
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Handle scheduling
        if scheduled_time:
            # Convert to UTC for YouTube API
            if scheduled_time.tzinfo is None:
                est = pytz.timezone('US/Eastern')
                scheduled_time = est.localize(scheduled_time)
            utc_time = scheduled_time.astimezone(pytz.UTC)
            
            # Add publishAt time - video will automatically become public at this time
            body['status'].update({
                'publishAt': utc_time.isoformat()
            })
            st.write(f"Video will be published at: {utc_time.isoformat()} UTC")

        # Upload the video
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(
                video_path, 
                chunksize=-1, 
                resumable=True
            )
        )
        
        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                st.write(f"Upload progress: {progress}%")
        
        video_id = response['id']
        
        if scheduled_time:
            st.success(f"Video uploaded and scheduled! It will remain private until {scheduled_time.strftime('%Y-%m-%d %I:%M %p %Z')}")
        else:
            # For non-scheduled videos, update to the requested privacy status if it's not private
            if privacy_status != 'private':
                update_body = {
                    'id': video_id,
                    'status': {
                        'privacyStatus': privacy_status
                    }
                }
                try:
                    youtube.videos().update(
                        part='status',
                        body=update_body
                    ).execute()
                except Exception as e:
                    st.warning(f"Video uploaded but privacy status might not be set correctly: {str(e)}")
            st.success(f"Video uploaded successfully! Video ID: {video_id}")
        
        return video_id
        
    except HttpError as e:
        st.error(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return None
    except Exception as e:
        st.error(f"An error occurred during upload: {str(e)}")
        return None 