# YouTube Shorts Automation

This application automates the process of downloading YouTube shorts, appending a video to them, and scheduling their upload to YouTube.

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Required Credentials:
- `credentials.json`: Google Sheets API service account credentials
- `client_secrets.json`: YouTube API OAuth 2.0 client credentials

### Getting the Credentials

1. For Google Sheets API (`credentials.json`):
   - Go to Google Cloud Console
   - Create a new project
   - Enable Google Sheets API
   - Create a service account
   - Download the JSON key and rename it to `credentials.json`

2. For YouTube API (`client_secrets.json`):
   - Go to Google Cloud Console
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download the client configuration and rename it to `client_secrets.json`

## Running the Application

```bash
streamlit run app.py
```

## Usage

1. Enter your Google Spreadsheet URL containing YouTube shorts links
2. Upload the video you want to append to each short
3. Configure the title and description templates
4. Set up the scheduling parameters
5. Click "Process Videos" to start the automation

## Spreadsheet Format

Your Google Spreadsheet should have the following column:
- `youtube_url`: The URL of the YouTube short to download

You can add additional columns that can be used in title and description templates. 