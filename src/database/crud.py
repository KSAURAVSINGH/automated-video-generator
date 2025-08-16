"""
CRUD operations for the Automated Video Generator database.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import (
    Video, VideoUpload, GenerationLog, ContentSource, 
    ScheduledJob, Analytics, Base
)

# Video CRUD operations
class VideoCRUD:
    @staticmethod
    def create(db: Session, **kwargs) -> Video:
        """Create a new video record."""
        video = Video(**kwargs)
        db.add(video)
        db.commit()
        db.refresh(video)
        return video
    
    @staticmethod
    def get_by_id(db: Session, video_id: int) -> Optional[Video]:
        """Get video by ID."""
        return db.query(Video).filter(Video.id == video_id).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Video]:
        """Get all videos with pagination."""
        return db.query(Video).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_status(db: Session, status: str) -> List[Video]:
        """Get videos by status."""
        return db.query(Video).filter(Video.status == status).all()
    
    @staticmethod
    def update(db: Session, video_id: int, **kwargs) -> Optional[Video]:
        """Update video record."""
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            for key, value in kwargs.items():
                setattr(video, key, value)
            video.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(video)
        return video
    
    @staticmethod
    def delete(db: Session, video_id: int) -> bool:
        """Delete video record."""
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            db.delete(video)
            db.commit()
            return True
        return False

# VideoUpload CRUD operations
class VideoUploadCRUD:
    @staticmethod
    def create(db: Session, **kwargs) -> VideoUpload:
        """Create a new video upload record."""
        upload = VideoUpload(**kwargs)
        db.add(upload)
        db.commit()
        db.refresh(upload)
        return upload
    
    @staticmethod
    def get_by_video_id(db: Session, video_id: int) -> List[VideoUpload]:
        """Get all uploads for a specific video."""
        return db.query(VideoUpload).filter(VideoUpload.video_id == video_id).all()
    
    @staticmethod
    def get_by_platform(db: Session, platform: str) -> List[VideoUpload]:
        """Get all uploads for a specific platform."""
        return db.query(VideoUpload).filter(VideoUpload.platform == platform).all()
    
    @staticmethod
    def update_status(db: Session, upload_id: int, status: str, 
                     platform_video_id: str = None, error_message: str = None) -> Optional[VideoUpload]:
        """Update upload status."""
        upload = db.query(VideoUpload).filter(VideoUpload.id == upload_id).first()
        if upload:
            upload.status = status
            if platform_video_id:
                upload.platform_video_id = platform_video_id
            if error_message:
                upload.error_message = error_message
            if status == 'completed':
                upload.uploaded_at = datetime.utcnow()
            db.commit()
            db.refresh(upload)
        return upload

# GenerationLog CRUD operations
class GenerationLogCRUD:
    @staticmethod
    def create(db: Session, **kwargs) -> GenerationLog:
        """Create a new generation log record."""
        log = GenerationLog(**kwargs)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_by_video_id(db: Session, video_id: int) -> List[GenerationLog]:
        """Get all generation logs for a specific video."""
        return db.query(GenerationLog).filter(GenerationLog.video_id == video_id).all()
    
    @staticmethod
    def update_status(db: Session, log_id: int, status: str, 
                     error_message: str = None, meta_data: str = None) -> Optional[GenerationLog]:
        """Update generation log status."""
        log = db.query(GenerationLog).filter(GenerationLog.id == log_id).first()
        if log:
            log.status = status
            log.end_time = datetime.utcnow()
            if error_message:
                log.error_message = error_message
            if meta_data:
                log.meta_data = meta_data
            if log.start_time:
                log.duration = (log.end_time - log.start_time).total_seconds()
            db.commit()
            db.refresh(log)
        return log

# ContentSource CRUD operations
class ContentSourceCRUD:
    @staticmethod
    def create(db: Session, **kwargs) -> ContentSource:
        """Create a new content source record."""
        source = ContentSource(**kwargs)
        db.add(source)
        db.commit()
        db.refresh(source)
        return source
    
    @staticmethod
    def get_active(db: Session) -> List[ContentSource]:
        """Get all active content sources."""
        return db.query(ContentSource).filter(ContentSource.is_active == True).all()
    
    @staticmethod
    def update_last_sync(db: Session, source_id: int) -> Optional[ContentSource]:
        """Update last sync timestamp for a content source."""
        source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
        if source:
            source.last_sync = datetime.utcnow()
            db.commit()
            db.refresh(source)
        return source

# ScheduledJob CRUD operations
class ScheduledJobCRUD:
    @staticmethod
    def create(db: Session, **kwargs) -> ScheduledJob:
        """Create a new scheduled job record."""
        job = ScheduledJob(**kwargs)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def get_active(db: Session) -> List[ScheduledJob]:
        """Get all active scheduled jobs."""
        return db.query(ScheduledJob).filter(ScheduledJob.is_active == True).all()
    
    @staticmethod
    def update_last_run(db: Session, job_id: int) -> Optional[ScheduledJob]:
        """Update last run timestamp for a scheduled job."""
        job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if job:
            job.last_run = datetime.utcnow()
            db.commit()
            db.refresh(job)
        return job

# Analytics CRUD operations
class AnalyticsCRUD:
    @staticmethod
    def create(db: Session, **kwargs) -> Analytics:
        """Create a new analytics record."""
        analytics = Analytics(**kwargs)
        db.add(analytics)
        db.commit()
        db.refresh(analytics)
        return analytics
    
    @staticmethod
    def get_by_video_id(db: Session, video_id: int) -> List[Analytics]:
        """Get all analytics for a specific video."""
        return db.query(Analytics).filter(Analytics.video_id == video_id).all()
    
    @staticmethod
    def get_latest_metrics(db: Session, video_id: int, platform: str) -> Dict[str, int]:
        """Get latest metrics for a video on a specific platform."""
        metrics = {}
        for metric_type in ['views', 'likes', 'comments', 'shares']:
            latest = db.query(Analytics).filter(
                and_(
                    Analytics.video_id == video_id,
                    Analytics.platform == platform,
                    Analytics.metric_type == metric_type
                )
            ).order_by(desc(Analytics.recorded_at)).first()
            
            if latest:
                metrics[metric_type] = latest.metric_value
            else:
                metrics[metric_type] = 0
        
        return metrics
