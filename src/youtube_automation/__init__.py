"""
YouTube Shorts Automation Package

This package provides functionality for automating the process of downloading,
processing, and uploading YouTube Shorts videos.
"""

from .api.youtube_api import download_video, upload_video
from .services.api_services import (
    setup_google_sheets,
    get_youtube_service,
    get_playlist_videos,
    get_spreadsheet_videos
)
from .utils.helpers import (
    format_title,
    format_description,
    validate_url,
    ensure_directory,
    clean_filename
)
from .templates import (
    load_templates,
    save_template,
    delete_template,
    render_template_manager
)

__version__ = '0.1.0'
__author__ = 'YouTube Shorts Automation Team' 