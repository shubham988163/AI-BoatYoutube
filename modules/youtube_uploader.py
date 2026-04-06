"""
BookGyaan — YouTube Uploader
===============================
Upload videos to YouTube using the YouTube Data API v3.
Requires OAuth2 client credentials (client_secrets.json).
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_SCOPES,
    YOUTUBE_CATEGORY_ID, YOUTUBE_DEFAULT_LANGUAGE,
    YOUTUBE_PRIVACY_STATUS, CHANNEL_HANDLE
)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list,
    thumbnail_path: str = None,
    privacy_status: str = None
) -> dict:
    """
    Upload a video to YouTube.
    
    Args:
        video_path: Path to the video file
        title: Video title
        description: Video description
        tags: List of tags
        thumbnail_path: Path to thumbnail image (optional)
        privacy_status: "public", "private", or "unlisted" (default from settings)
    
    Returns:
        dict with upload result including video ID and URL
    """
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    import pickle

    privacy = privacy_status or YOUTUBE_PRIVACY_STATUS

    print(f"\n📤 Uploading to YouTube ({privacy})...")
    print(f"   Video: {video_path}")
    print(f"   Title: {title}")

    # ─── Authentication ──────────────────────────────────────────────────

    credentials = _get_credentials()
    youtube = build("youtube", "v3", credentials=credentials)

    # ─── Upload Video ────────────────────────────────────────────────────

    body = {
        "snippet": {
            "title": title[:100],  # YouTube max title length
            "description": description[:5000],  # YouTube max description length
            "tags": tags[:30],  # YouTube max 30 tags
            "categoryId": YOUTUBE_CATEGORY_ID,
            "defaultLanguage": YOUTUBE_DEFAULT_LANGUAGE,
            "defaultAudioLanguage": YOUTUBE_DEFAULT_LANGUAGE
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024  # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    # Resumable upload with progress
    print("   📦 Uploading...")
    response = None
    retry_count = 0
    max_retries = 3

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"   ⏳ Upload progress: {progress}%")
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                raise Exception(f"Upload failed after {max_retries} retries: {e}")
            print(f"   ⚠️  Upload error, retrying ({retry_count}/{max_retries}): {e}")
            time.sleep(5 * retry_count)

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print(f"   ✅ Video uploaded successfully!")
    print(f"   🆔 Video ID: {video_id}")
    print(f"   🔗 URL: {video_url}")

    # ─── Set Thumbnail ───────────────────────────────────────────────────

    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            print(f"   🖼️  Setting thumbnail...")
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print(f"   ✅ Thumbnail set!")
        except Exception as e:
            print(f"   ⚠️  Thumbnail upload failed (may need channel verification): {e}")

    return {
        "video_id": video_id,
        "url": video_url,
        "title": title,
        "privacy": privacy
    }


def _get_credentials():
    """Get or refresh YouTube API credentials."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle

    token_path = Path(YOUTUBE_CLIENT_SECRETS_FILE).parent / "youtube_token.pickle"

    credentials = None

    # Load saved credentials
    if token_path.exists():
        with open(token_path, "rb") as token:
            credentials = pickle.load(token)

    # Refresh or get new credentials
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception:
            credentials = None

    if not credentials or not credentials.valid:
        if not Path(YOUTUBE_CLIENT_SECRETS_FILE).exists():
            raise FileNotFoundError(
                f"YouTube client secrets file not found: {YOUTUBE_CLIENT_SECRETS_FILE}\n"
                f"Download it from Google Cloud Console:\n"
                f"  1. Go to https://console.cloud.google.com/apis/credentials\n"
                f"  2. Create OAuth 2.0 Client ID (Desktop App)\n"
                f"  3. Download the JSON file as 'client_secrets.json'\n"
                f"  4. Place it in: {Path(YOUTUBE_CLIENT_SECRETS_FILE).parent}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            YOUTUBE_CLIENT_SECRETS_FILE,
            YOUTUBE_SCOPES
        )
        credentials = flow.run_local_server(port=0)

        # Save credentials for next time
        with open(token_path, "wb") as token:
            pickle.dump(credentials, token)
        print(f"   🔑 Credentials saved to: {token_path}")

    return credentials


# ─── CLI Usage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", required=True, help="Video file path")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", nargs="*", default=[], help="Video tags")
    parser.add_argument("--thumbnail", help="Thumbnail image path")
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"],
                        default=YOUTUBE_PRIVACY_STATUS)
    args = parser.parse_args()

    result = upload_video(
        args.video, args.title, args.description,
        args.tags, args.thumbnail, args.privacy
    )
    print(f"\n🎉 Done! Watch at: {result['url']}")
