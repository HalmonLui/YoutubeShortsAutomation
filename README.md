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

## Setting Up YouTube API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3 for your project
4. Go to Credentials and create a new OAuth 2.0 Client ID
5. Download the client configuration file and rename it to `client_secrets.json`
6. Get your refresh token by following these steps:
   - Go to [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
   - Click the gear icon in the top right
   - Check "Use your own OAuth credentials"
   - Enter your client ID and client secret from the `client_secrets.json` file
   - Select "YouTube Data API v3" from the list of APIs
   - Click "Authorize APIs"
   - After authorizing, click "Exchange authorization code for tokens"
   - Copy the refresh token

7. Update your `client_secrets.json` file to include the refresh token:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

The application will now use these credentials directly without requiring web-based login.

## Required Scopes

The following YouTube API scopes are required:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`

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