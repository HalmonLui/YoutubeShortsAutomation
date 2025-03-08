import os
import re
import requests
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
import webbrowser
from ..models.dummy_models import DummyGoogleSheets, DummyYouTubeService

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',
          'https://www.googleapis.com/auth/youtube.upload']

def setup_google_sheets(dev_mode=True):
    if dev_mode:
        st.warning("⚠️ Running in development mode - Google Sheets integration is mocked")
        return DummyGoogleSheets()
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json', 
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error setting up Google Sheets: {str(e)}")
        if dev_mode:
            return DummyGoogleSheets()
        raise

def get_youtube_service(dev_mode=True):
    """Get an authenticated YouTube service instance."""
    if dev_mode:
        st.warning("⚠️ Running in development mode - YouTube integration is mocked")
        return DummyYouTubeService()
    
    try:
        if not os.path.exists('client_secrets.json'):
            st.error("❌ Missing client_secrets.json file.")
            return DummyYouTubeService()

        # Initialize session state
        if 'credentials' not in st.session_state:
            st.session_state.credentials = None
        if 'auth_in_progress' not in st.session_state:
            st.session_state.auth_in_progress = False

        creds = st.session_state.credentials

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                st.session_state.credentials = creds
            else:
                # Check for auth code in query parameters
                query_params = st.experimental_get_query_params()
                code = query_params.get("code", [None])[0]
                
                if code and st.session_state.auth_in_progress:
                    try:
                        flow = Flow.from_client_secrets_file(
                            'client_secrets.json',
                            scopes=SCOPES,
                            redirect_uri='http://localhost:8501/'
                        )
                        flow.fetch_token(code=code)
                        st.session_state.credentials = flow.credentials
                        st.session_state.auth_in_progress = False
                        st.success("✅ Authentication successful!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Authentication failed: {str(e)}")
                        st.session_state.auth_in_progress = False
                        return DummyYouTubeService()
                else:
                    if not st.session_state.auth_in_progress:
                        st.markdown("""
                        ### YouTube Authentication Required
                        Click the button below to authenticate with your Google account.
                        """)
                        
                        if st.button("🔐 Login with Google"):
                            flow = Flow.from_client_secrets_file(
                                'client_secrets.json',
                                scopes=SCOPES,
                                redirect_uri='http://localhost:8501/'
                            )
                            auth_url, _ = flow.authorization_url(
                                access_type='offline',
                                include_granted_scopes='true'
                            )
                            st.session_state.auth_in_progress = True
                            st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                            st.stop()
                        return DummyYouTubeService()
                    else:
                        st.info("🔄 Waiting for authentication...")
                        return DummyYouTubeService()

        return build('youtube', 'v3', credentials=creds)
    
    except Exception as e:
        st.error(f"Error setting up YouTube service: {str(e)}")
        if dev_mode:
            return DummyYouTubeService()
        raise

def get_playlist_videos(playlist_url):
    try:
        if 'list=' in playlist_url:
            # This is a playlist
            try:
                # Extract playlist ID
                playlist_id = re.search(r'list=([^&]+)', playlist_url).group(1)
                st.write(f"Playlist ID: {playlist_id}")
                
                # Make direct request to get playlist data
                playlist_api_url = f'https://www.youtube.com/playlist?list={playlist_id}'
                response = requests.get(playlist_api_url)
                html_content = response.text
                
                # Extract video IDs using regex
                video_ids = re.findall(r'(?:watch\?v=|/shorts/)([a-zA-Z0-9_-]{11})', html_content)
                video_ids = list(dict.fromkeys(video_ids))  # Remove duplicates
                
                st.write(f"Found {len(video_ids)} unique videos")
                
                # Convert to shorts format
                videos = []
                for video_id in video_ids:
                    short_url = f"https://www.youtube.com/shorts/{video_id}"
                    videos.append({
                        "youtube_url": short_url
                    })
                    st.write(f"Added video: {short_url}")
                
                if not videos:
                    st.warning("No videos found in the playlist")
                else:
                    st.info(f"Successfully processed {len(videos)} videos from the playlist")
                return videos
            except Exception as e:
                st.error(f"Error processing playlist: {str(e)}")
                st.write("Full error details:", str(e))
                return []
        else:
            # Single video URL
            if '/shorts/' in playlist_url:
                video_id = re.search(r'(?<=shorts/)[^&?/]+', playlist_url)
            else:
                video_id = re.search(r'(?<=v=)[^&]+', playlist_url)
            
            if video_id:
                return [{
                    "youtube_url": f"https://www.youtube.com/shorts/{video_id.group(0)}"
                }]
            st.warning("Could not extract video ID from URL")
            return []
    except Exception as e:
        st.error(f"Error accessing videos: {str(e)}")
        st.write("Full error details:", str(e))
        return []

def get_spreadsheet_videos(sheets_client, spreadsheet_url):
    try:
        worksheet = sheets_client.open_by_url(spreadsheet_url).sheet1
        return worksheet.get_all_records()
    except Exception as e:
        st.error(f"Error accessing spreadsheet: {str(e)}")
        return [] 