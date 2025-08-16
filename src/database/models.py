"""
Database models for the Automated Video Generator.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Video(Base):
    """Video model representing generated videos."""
    
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    duration = Column(Float)  # Duration in seconds
    resolution = Column(String(20))  # e.g., "1920x1080"
    file_size = Column(Integer)  # File size in bytes
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    uploads = relationship("VideoUpload", back_populates="video")
    generation_logs = relationship("GenerationLog", back_populates="video")

class VideoUpload(Base):
    """Model for tracking video uploads to different platforms."""
    
    __tablename__ = 'video_uploads'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    platform = Column(String(50), nullable=False)  # youtube, instagram, etc.
    platform_video_id = Column(String(100))  # ID returned by platform
    upload_url = Column(String(500))
    status = Column(String(50), default='pending')  # pending, uploading, completed, failed
    error_message = Column(Text)
    uploaded_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    video = relationship("Video", back_populates="uploads")

class GenerationLog(Base):
    """Log of video generation steps and status."""
    
    __tablename__ = 'generation_logs'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    step = Column(String(100), nullable=False)  # text_to_speech, image_generation, etc.
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime)
    duration = Column(Float)  # Duration in seconds
    error_message = Column(Text)
    meta_data = Column(Text)  # JSON string for additional data - renamed from metadata
    
    # Relationships
    video = relationship("Video", back_populates="generation_logs")

class ContentSource(Base):
    """Source of content for video generation (e.g., Google Sheets)."""
    
    __tablename__ = 'content_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)  # google_sheets, manual, api
    config = Column(Text)  # JSON string for configuration
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ScheduledJob(Base):
    """Model for tracking scheduled video generation jobs."""
    
    __tablename__ = 'scheduled_jobs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    job_type = Column(String(50), nullable=False)  # video_generation, upload, etc.
    schedule = Column(String(100), nullable=False)  # Cron expression or interval
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    config = Column(Text)  # JSON string for job configuration
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Analytics(Base):
    """Analytics data for uploaded videos."""
    
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    metric_type = Column(String(50), nullable=False)  # views, likes, comments, etc.
    metric_value = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    video = relationship("Video")
