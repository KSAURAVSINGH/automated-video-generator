"""
YouTube analytics and statistics collection for the Automated Video Generator.
"""

import requests
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import json

from ..config.settings import YOUTUBE_API_KEY
from ..database.db_init import get_db
from ..database.crud import AnalyticsCRUD, VideoCRUD, VideoUploadCRUD
from ..uploaders.youtube_uploader import youtube_uploader

logger = logging.getLogger(__name__)

class YouTubeAnalytics:
    """YouTube analytics and statistics collector."""
    
    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with YouTube Data API."""
        try:
            if not self.api_key:
                raise ValueError("YouTube API key not configured")
            
            # Use the existing YouTube uploader instance
            self.youtube = youtube_uploader.youtube
            logger.info("YouTube analytics initialized successfully")
            
        except Exception as e:
            logger.error(f"YouTube analytics initialization failed: {e}")
            raise
    
    def collect_video_stats(self, youtube_video_id: str, video_id: int) -> bool:
        """
        Collect and store statistics for a YouTube video.
        
        Args:
            youtube_video_id: YouTube video ID
            video_id: Database video ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get video statistics from YouTube API
            video_info = youtube_uploader.get_video_info(youtube_video_id)
            
            if not video_info:
                logger.warning(f"Could not get video info for {youtube_video_id}")
                return False
            
            # Store analytics data
            with get_db() as db:
                # Store view count
                AnalyticsCRUD.create(db,
                    video_id=video_id,
                    platform='youtube',
                    metric_type='views',
                    metric_value=video_info['view_count']
                )
                
                # Store like count
                AnalyticsCRUD.create(db,
                    video_id=video_id,
                    platform='youtube',
                    metric_type='likes',
                    metric_value=video_info['like_count']
                )
                
                # Store comment count
                AnalyticsCRUD.create(db,
                    video_id=video_id,
                    platform='youtube',
                    metric_type='comments',
                    metric_value=video_info['comment_count']
                )
            
            logger.info(f"Analytics collected for video {video_id} (YouTube: {youtube_video_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to collect analytics for video {video_id}: {e}")
            return False
    
    def collect_channel_stats(self) -> Optional[Dict[str, Any]]:
        """
        Collect and store channel statistics.
        
        Returns:
            Channel statistics dictionary if successful, None otherwise
        """
        try:
            channel_info = youtube_uploader.get_channel_info()
            
            if not channel_info:
                logger.warning("Could not get channel information")
                return None
            
            logger.info(f"Channel stats collected: {channel_info['subscriber_count']} subscribers")
            return channel_info
            
        except Exception as e:
            logger.error(f"Failed to collect channel stats: {e}")
            return None
    
    def get_video_performance_summary(self, video_id: int) -> Dict[str, Any]:
        """
        Get a summary of video performance across all platforms.
        
        Args:
            video_id: Database video ID
        
        Returns:
            Performance summary dictionary
        """
        try:
            with get_db() as db:
                # Get video information
                video = VideoCRUD.get_by_id(db, video_id)
                if not video:
                    return {"error": "Video not found"}
                
                # Get all analytics for this video
                analytics = AnalyticsCRUD.get_by_video_id(db, video_id)
                
                # Group by platform
                platform_stats = {}
                for analytic in analytics:
                    platform = analytic.platform
                    if platform not in platform_stats:
                        platform_stats[platform] = {}
                    
                    platform_stats[platform][analytic.metric_type] = analytic.metric_value
                
                # Get upload information
                uploads = VideoUploadCRUD.get_by_video_id(db, video_id)
                upload_status = {upload.platform: upload.status for upload in uploads}
                
                summary = {
                    'video_id': video_id,
                    'title': video.title,
                    'status': video.status,
                    'created_at': video.created_at.isoformat() if video.created_at else None,
                    'platform_stats': platform_stats,
                    'upload_status': upload_status,
                    'total_views': sum(
                        stats.get('views', 0) for stats in platform_stats.values()
                    ),
                    'total_likes': sum(
                        stats.get('likes', 0) for stats in platform_stats.values()
                    ),
                    'total_comments': sum(
                        stats.get('comments', 0) for stats in platform_stats.values()
                    )
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get video performance summary: {e}")
            return {"error": str(e)}
    
    def get_platform_comparison(self, video_id: int) -> Dict[str, Any]:
        """
        Compare video performance across different platforms.
        
        Args:
            video_id: Database video ID
        
        Returns:
            Platform comparison dictionary
        """
        try:
            with get_db() as db:
                # Get analytics for this video
                analytics = AnalyticsCRUD.get_by_video_id(db, video_id)
                
                # Group by platform and metric type
                comparison = {}
                for analytic in analytics:
                    platform = analytic.platform
                    metric = analytic.metric_type
                    
                    if platform not in comparison:
                        comparison[platform] = {}
                    
                    comparison[platform][metric] = analytic.metric_value
                
                # Calculate engagement rates
                for platform, metrics in comparison.items():
                    views = metrics.get('views', 0)
                    likes = metrics.get('likes', 0)
                    comments = metrics.get('comments', 0)
                    
                    if views > 0:
                        metrics['like_rate'] = (likes / views) * 100
                        metrics['comment_rate'] = (comments / views) * 100
                        metrics['engagement_rate'] = ((likes + comments) / views) * 100
                    else:
                        metrics['like_rate'] = 0
                        metrics['comment_rate'] = 0
                        metrics['engagement_rate'] = 0
                
                return comparison
                
        except Exception as e:
            logger.error(f"Failed to get platform comparison: {e}")
            return {"error": str(e)}
    
    def get_trending_analysis(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze trending patterns across all videos.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Trending analysis dictionary
        """
        try:
            with get_db() as db:
                # Get videos from the specified time period
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # This would need to be implemented in the CRUD layer
                # For now, we'll get all videos and filter in Python
                all_videos = VideoCRUD.get_all(db, limit=1000)
                recent_videos = [
                    video for video in all_videos 
                    if video.created_at and video.created_at >= cutoff_date
                ]
                
                # Collect analytics for recent videos
                total_views = 0
                total_likes = 0
                total_comments = 0
                platform_breakdown = {}
                
                for video in recent_videos:
                    analytics = AnalyticsCRUD.get_by_video_id(db, video.id)
                    
                    for analytic in analytics:
                        platform = analytic.platform
                        if platform not in platform_breakdown:
                            platform_breakdown[platform] = {
                                'views': 0, 'likes': 0, 'comments': 0, 'videos': 0
                            }
                        
                        platform_breakdown[platform]['views'] += analytic.metric_value
                        if analytic.metric_type == 'likes':
                            total_likes += analytic.metric_value
                        elif analytic.metric_type == 'comments':
                            total_comments += analytic.metric_value
                        elif analytic.metric_type == 'views':
                            total_views += analytic.metric_value
                    
                    # Count videos per platform
                    uploads = VideoUploadCRUD.get_by_video_id(db, video.id)
                    for upload in uploads:
                        if upload.platform in platform_breakdown:
                            platform_breakdown[upload.platform]['videos'] += 1
                
                # Calculate averages
                video_count = len(recent_videos)
                avg_views = total_views / video_count if video_count > 0 else 0
                avg_likes = total_likes / video_count if video_count > 0 else 0
                avg_comments = total_comments / video_count if video_count > 0 else 0
                
                analysis = {
                    'period_days': days,
                    'total_videos': video_count,
                    'total_views': total_views,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'averages': {
                        'views_per_video': avg_views,
                        'likes_per_video': avg_likes,
                        'comments_per_video': avg_comments
                    },
                    'platform_breakdown': platform_breakdown,
                    'engagement_metrics': {
                        'overall_like_rate': (total_likes / total_views * 100) if total_views > 0 else 0,
                        'overall_comment_rate': (total_comments / total_views * 100) if total_views > 0 else 0
                    }
                }
                
                return analysis
                
        except Exception as e:
            logger.error(f"Failed to get trending analysis: {e}")
            return {"error": str(e)}
    
    def export_analytics_report(self, video_id: int = None, 
                              format: str = 'json') -> Optional[str]:
        """
        Export analytics data in various formats.
        
        Args:
            video_id: Specific video ID (optional, exports all if None)
            format: Export format ('json', 'csv')
        
        Returns:
            Exported data string if successful, None otherwise
        """
        try:
            if video_id:
                # Export specific video analytics
                data = self.get_video_performance_summary(video_id)
            else:
                # Export all analytics
                data = self.get_trending_analysis()
            
            if format == 'json':
                return json.dumps(data, indent=2, default=str)
            elif format == 'csv':
                # Simple CSV conversion for basic data
                if isinstance(data, dict) and 'platform_stats' in data:
                    csv_lines = ['Platform,Metric,Value']
                    for platform, stats in data['platform_stats'].items():
                        for metric, value in stats.items():
                            csv_lines.append(f'{platform},{metric},{value}')
                    return '\n'.join(csv_lines)
                else:
                    return str(data)
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to export analytics report: {e}")
            return None
    
    def schedule_analytics_collection(self, video_ids: List[int] = None) -> bool:
        """
        Schedule analytics collection for videos.
        
        Args:
            video_ids: List of video IDs to collect analytics for (None for all)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db() as db:
                if video_ids:
                    videos = [VideoCRUD.get_by_id(db, vid) for vid in video_ids]
                    videos = [v for v in videos if v]  # Filter out None values
                else:
                    videos = VideoCRUD.get_all(db, limit=1000)
                
                # Get videos that have been uploaded to YouTube
                youtube_videos = []
                for video in videos:
                    uploads = VideoUploadCRUD.get_by_video_id(db, video.id)
                    for upload in uploads:
                        if upload.platform == 'youtube' and upload.platform_video_id:
                            youtube_videos.append((video.id, upload.platform_video_id))
                
                # Collect analytics for each video
                success_count = 0
                for video_id, youtube_id in youtube_videos:
                    if self.collect_video_stats(youtube_id, video_id):
                        success_count += 1
                
                logger.info(f"Analytics collection completed: {success_count}/{len(youtube_videos)} videos")
                return success_count > 0
                
        except Exception as e:
            logger.error(f"Failed to schedule analytics collection: {e}")
            return False

# Global YouTube analytics instance
youtube_analytics = YouTubeAnalytics()
