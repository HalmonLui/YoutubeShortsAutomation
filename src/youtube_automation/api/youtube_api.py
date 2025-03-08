import os
import streamlit as st
from googleapiclient.http import MediaFileUpload
import yt_dlp
import time

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

def upload_video(youtube_service, video_path, title, description, privacy_status="private", scheduled_time=None):
    """
    Upload a video to YouTube with optional scheduling.
    
    Args:
        youtube_service: YouTube API service instance
        video_path: Path to the video file
        title: Video title
        description: Video description
        privacy_status: Privacy status (private, unlisted, public)
        scheduled_time: Optional datetime for scheduled release (in EST)
    """
    try:
        if not os.path.exists(video_path):
            st.error(f"Video file not found: {video_path}")
            return None

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': '22'  # People & Blogs category
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        # Add scheduling if provided
        if scheduled_time:
            body['status']['publishAt'] = scheduled_time.isoformat()
            # If scheduling, set initial status to private
            body['status']['privacyStatus'] = 'private'
            st.write(f"Video will be published at: {scheduled_time.strftime('%Y-%m-%d %I:%M %p')} EST")

        insert_request = youtube_service.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True
            )
        )

        response = insert_request.execute()
        video_id = response.get('id')
        if video_id:
            if scheduled_time:
                st.success(f"Successfully scheduled video with ID: {video_id}")
            else:
                st.success(f"Successfully uploaded video with ID: {video_id}")
            return video_id
        else:
            st.error("Upload completed but no video ID received")
            return None

    except Exception as e:
        st.error(f"Error uploading video: {str(e)}")
        return None 