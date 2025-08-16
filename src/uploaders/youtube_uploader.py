"""
YouTube Uploader for Automated Video Generation
Handles video uploads to YouTube using YouTube Data API v3
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import pickle

logger = logging.getLogger(__name__)

class YouTubeUploader:
    """
    Handles YouTube video uploads
    """
    
    def __init__(self, credentials_path: str = "credentials.json"):
        self.credentials_path = credentials_path
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.api_name = 'youtube'
        self.api_version = 'v3'
        self.youtube = None
        self.credentials = None
        
        logger.info("📤 YouTube Uploader initialized")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with YouTube API
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.info("🔐 Authenticating with YouTube API...")
            
            # Check if we have valid credentials
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If credentials are invalid or expired, refresh them
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    # Need to get new credentials
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"❌ Credentials file not found: {self.credentials_path}")
                        logger.info("💡 Please download credentials.json from Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes
                    )
                    # Use out-of-band flow with manual authorization
                    self.credentials = flow.run_local_server(port=0, open_browser=False)
                
                # Save credentials for next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.credentials, token)
            
            # Build YouTube service
            self.youtube = build(
                self.api_name, 
                self.api_version, 
                credentials=self.credentials
            )
            
            logger.info("✅ YouTube authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ YouTube authentication failed: {e}")
            return False
    
    async def upload_video(self, video_path: str, title: str, description: str,
                          tags: List[str] = None, category: str = "28",  # 28 = Science & Technology
                          privacy_status: str = "private", 
                          thumbnail_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category: YouTube category ID
            privacy_status: Privacy status (private, unlisted, public)
            thumbnail_path: Optional path to thumbnail image
            
        Returns:
            Dictionary with upload result
        """
        try:
            # Ensure authentication
            if not self.youtube:
                if not await self.authenticate():
                    raise RuntimeError("Failed to authenticate with YouTube")
            
            logger.info(f"📤 Starting YouTube upload: {title}")
            
            # Validate video file
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': category
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path, 
                chunksize=1024*1024,  # 1MB chunks
                resumable=True
            )
            
            # Start upload
            upload_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Monitor upload progress
            response = None
            error = None
            
            while response is None:
                try:
                    status, response = upload_request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"📤 Upload progress: {progress}%")
                except HttpError as e:
                    if e.resp.status < 500:
                        error = e
                        break
                    else:
                        # Retry on server errors
                        await asyncio.sleep(1)
                        continue
            
            if error:
                raise error
            
            if response:
                video_id = response['id']
                logger.info(f"✅ Video uploaded successfully! YouTube ID: {video_id}")
                
                # Upload thumbnail if provided
                if thumbnail_path and os.path.exists(thumbnail_path):
                    await self._upload_thumbnail(video_id, thumbnail_path)
                
                # Get video details
                video_details = await self._get_video_details(video_id)
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                    'title': title,
                    'privacy_status': privacy_status,
                    'upload_time': video_details.get('publishedAt'),
                    'duration': video_details.get('duration'),
                    'view_count': video_details.get('viewCount', 0),
                    'like_count': video_details.get('likeCount', 0)
                }
            else:
                raise RuntimeError("Upload completed but no response received")
                
        except Exception as e:
            logger.error(f"❌ YouTube upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'video_path': video_path,
                'title': title
            }
    
    async def _upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Upload a thumbnail for the video
        
        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🖼️ Uploading thumbnail for video {video_id}")
            
            # Validate thumbnail file
            if not os.path.exists(thumbnail_path):
                logger.warning(f"⚠️ Thumbnail file not found: {thumbnail_path}")
                return False
            
            # Check file size (YouTube limit: 2MB)
            file_size = os.path.getsize(thumbnail_path)
            if file_size > 2 * 1024 * 1024:
                logger.warning(f"⚠️ Thumbnail too large: {file_size} bytes (max 2MB)")
                return False
            
            # Upload thumbnail
            media = MediaFileUpload(thumbnail_path, resumable=True)
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            
            logger.info(f"✅ Thumbnail uploaded successfully for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Thumbnail upload failed: {e}")
            return False
    
    async def _get_video_details(self, video_id: str) -> Dict[str, Any]:
        """
        Get detailed information about an uploaded video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video details
        """
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if response['items']:
                video = response['items'][0]
                return {
                    'publishedAt': video['snippet'].get('publishedAt'),
                    'duration': video['contentDetails'].get('duration'),
                    'viewCount': int(video['statistics'].get('viewCount', 0)),
                    'likeCount': int(video['statistics'].get('likeCount', 0)),
                    'commentCount': int(video['statistics'].get('commentCount', 0))
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get video details: {e}")
            return {}
    
    async def update_video(self, video_id: str, title: str = None, 
                          description: str = None, tags: List[str] = None,
                          category: str = None, privacy_status: str = None) -> bool:
        """
        Update video metadata
        
        Args:
            video_id: YouTube video ID
            title: New title
            description: New description
            tags: New tags
            category: New category ID
            privacy_status: New privacy status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.youtube:
                if not await self.authenticate():
                    return False
            
            logger.info(f"📝 Updating video {video_id}")
            
            # Build update body
            body = {'id': video_id}
            
            if any([title, description, tags, category]):
                body['snippet'] = {}
                if title:
                    body['snippet']['title'] = title
                if description:
                    body['snippet']['description'] = description
                if tags:
                    body['snippet']['tags'] = tags
                if category:
                    body['snippet']['categoryId'] = category
            
            if privacy_status:
                body['status'] = {'privacyStatus': privacy_status}
            
            # Update video
            self.youtube.videos().update(
                part=','.join(body.keys()),
                body=body
            ).execute()
            
            logger.info(f"✅ Video {video_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update video {video_id}: {e}")
            return False
    
    async def delete_video(self, video_id: str) -> bool:
        """
        Delete a video from YouTube
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.youtube:
                if not await self.authenticate():
                    return False
            
            logger.info(f"🗑️ Deleting video {video_id}")
            
            self.youtube.videos().delete(id=video_id).execute()
            
            logger.info(f"✅ Video {video_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete video {video_id}: {e}")
            return False
    
    async def get_channel_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated channel
        
        Returns:
            Dictionary with channel information
        """
        try:
            if not self.youtube:
                if not await self.authenticate():
                    return {}
            
            response = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                    'video_count': int(channel['statistics'].get('videoCount', 0)),
                    'view_count': int(channel['statistics'].get('viewCount', 0))
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get channel info: {e}")
            return {}
    
    def get_upload_quota(self) -> Dict[str, Any]:
        """
        Get current upload quota information
        
        Returns:
            Dictionary with quota information
        """
        try:
            if not self.youtube:
                return {'error': 'Not authenticated'}
            
            # Note: YouTube API doesn't provide direct quota info
            # This is a placeholder for future implementation
            return {
                'note': 'YouTube API quota information not directly available',
                'recommendation': 'Monitor usage in Google Cloud Console'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get quota info: {e}")
            return {'error': str(e)}
