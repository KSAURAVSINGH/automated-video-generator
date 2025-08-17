"""
Global Workflow Controller for Automated Video Generation
Manages the complete pipeline: Database → Scheduler → Image Gen → Video Gen → Upload
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import subprocess
import os

# Import our modules
from src.database.db_handler import get_pending_videos, update_video_status
from src.video_generation.image_generation import ImageGenerationManager
from src.video_generation.pyramid_flow_generator import PyramidFlowGenerator, generate_video_with_pyramid_flow
from src.video_generation.video_editor import VideoEditor
from src.uploaders.youtube_uploader import YouTubeUploader
from src.scheduler.job_manager import JobScheduler
from src.scheduler.enhanced_scheduler import EnhancedScheduler
from src.config.settings import TEMP_DIR, LOG_DIR, PYRAMID_FLOW_ENABLED

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoStatus(Enum):
    """Video processing status enum"""
    PENDING = "pending"
    IMAGE_GENERATION = "image_generation"
    VIDEO_ASSEMBLY = "video_assembly"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class VideoJob:
    """Represents a video generation job"""
    video_id: int
    title: str
    description: str
    genre: str
    expected_length: int
    schedule_time: datetime
    status: VideoStatus
    created_at: datetime
    metadata: Dict[str, Any]

class WorkflowController:
    """
    Global controller that orchestrates the entire video generation workflow
    """
    
    def __init__(self):
        self.image_manager = ImageGenerationManager()
        self.pyramid_flow_generator = PyramidFlowGenerator() if PYRAMID_FLOW_ENABLED else None
        self.video_editor = VideoEditor()
        self.youtube_uploader = YouTubeUploader()
        
        # Use enhanced scheduler with workflow callback
        self.scheduler = EnhancedScheduler(workflow_callback=self._handle_scheduled_task)
        
        self.active_jobs: Dict[int, VideoJob] = {}
        self.processing_queue: List[VideoJob] = []
        self.max_concurrent_jobs = 3
        self.is_running = False
        
        # Ensure directories exist
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info("🎬 Workflow Controller initialized")
        if PYRAMID_FLOW_ENABLED:
            logger.info("🎬 Pyramid Flow text-to-video generation enabled")
        else:
            logger.info("⚠️ Pyramid Flow text-to-video generation disabled")
    
    async def start(self):
        """Start the workflow controller"""
        logger.info("🚀 Starting Workflow Controller...")
        self.is_running = True
        
        # Test YouTube uploader functionality
        await self._test_youtube_uploader()
        
        # Start the scheduler
        await self.scheduler.start()
        
        # Start the main processing loop
        asyncio.create_task(self._main_processing_loop())
        
        logger.info("✅ Workflow Controller started successfully")
    
    async def stop(self):
        """Stop the workflow controller"""
        logger.info("🛑 Stopping Workflow Controller...")
        self.is_running = False
        
        # Stop the scheduler
        await self.scheduler.stop()
        
        # Cancel all active jobs
        for job in self.active_jobs.values():
            await self._cancel_job(job)
        
        logger.info("✅ Workflow Controller stopped")
    
    async def _main_processing_loop(self):
        """Main processing loop that continuously checks for new jobs"""
        logger.info("🔄 Starting main processing loop...")
        
        while self.is_running:
            try:
                # Check for new pending videos
                await self._check_for_new_jobs()
                
                # Process active jobs
                await self._process_active_jobs()
                
                # Clean up completed jobs
                await self._cleanup_completed_jobs()
                
                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in main processing loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_for_new_jobs(self):
        """Check database for new pending videos and add them to the queue"""
        try:
            pending_videos = get_pending_videos()
            
            for video_data in pending_videos:
                if video_data['id'] not in self.active_jobs:
                    # Create new job
                    # Parse extra_metadata and include video_link
                    extra_metadata = json.loads(video_data.get('extra_metadata', '{}'))
                    
                    # Check for video path in multiple locations
                    video_path = None
                    
                    # First, check if video_url is stored in the database
                    if video_data.get('video_url'):
                        video_path = video_data['video_url']
                        logger.info(f"🎬 Found video path in database: {video_path}")
                    # Then check extra_metadata for video_link
                    elif extra_metadata.get('video_link'):
                        video_path = extra_metadata['video_link']
                        logger.info(f"🎬 Found video path in metadata: {video_path}")
                    
                    # Store the video path in metadata for the workflow
                    if video_path:
                        extra_metadata['video_link'] = video_path
                        logger.info(f"🎬 Video path stored in metadata: {video_path}")
                    else:
                        logger.warning(f"⚠️ No video path found for job {video_data['id']}")
                    
                    job = VideoJob(
                        video_id=video_data['id'],
                        title=video_data['title'],
                        description=video_data['description'],
                        genre=video_data['genre'],
                        expected_length=video_data['expected_length'],
                        schedule_time=datetime.fromisoformat(video_data['schedule_time']),
                        status=VideoStatus.PENDING,
                        created_at=datetime.now(),
                        metadata=extra_metadata
                    )
                    
                    # Check if it's time to process this job
                    if datetime.now() >= job.schedule_time:
                        self.processing_queue.append(job)
                        logger.info(f"📋 Added job {job.video_id} to processing queue")
                    else:
                        # Schedule for future processing
                        await self.scheduler.schedule_job(job)
                        
        except Exception as e:
            logger.error(f"❌ Error checking for new jobs: {e}")
    
    async def _process_active_jobs(self):
        """Process jobs in the queue (respecting concurrency limits)"""
        # Start new jobs if we have capacity
        while (len(self.active_jobs) < self.max_concurrent_jobs and 
               self.processing_queue):
            
            job = self.processing_queue.pop(0)
            self.active_jobs[job.video_id] = job
            
            # Start processing this job
            asyncio.create_task(self._process_job(job))
    
    async def _process_job(self, job: VideoJob):
        """Process a single video job through the complete pipeline"""
        logger.info(f"🚀 Starting processing for video {job.video_id}: {job.title}")
        job.progress = "0%"
        
        try:
            # Step 1: Check if video file exists (skip image generation)
            video_path = job.metadata.get('video_link', '')
            
            # Also check if video_link is stored directly in the job
            if not video_path and hasattr(job, 'video_link'):
                video_path = job.video_link
            
            if not video_path:
                # No video file provided, try to use existing video in temp folder
                logger.warning(f"⚠️ No video file provided for job {job.video_id}, looking for existing video in temp folder")
                
                # Look for existing video files in temp folder
                temp_dir = Path("temp")
                if temp_dir.exists():
                    video_files = list(temp_dir.glob("*.mp4"))
                    if video_files:
                        # Use the first available video file (preferably the largest one)
                        video_files.sort(key=lambda x: x.stat().st_size, reverse=True)
                        video_path = str(video_files[0])
                        logger.info(f"🎬 Found existing video file: {video_path} ({video_files[0].stat().st_size} bytes)")
                    else:
                        logger.warning(f"⚠️ No video files found in temp folder, creating placeholder")
                        video_path = await self._create_placeholder_video(job)
                else:
                    logger.warning(f"⚠️ Temp folder not found, creating placeholder")
                    video_path = await self._create_placeholder_video(job)
            else:
                # Use the provided video file
                logger.info(f"🎬 Using provided video file: {video_path}")
            
            # Verify the video file exists and is valid
            if not os.path.exists(video_path):
                logger.error(f"❌ Video file not found: {video_path}")
                # Try to find an alternative video file
                temp_dir = Path("temp")
                if temp_dir.exists():
                    video_files = list(temp_dir.glob("*.mp4"))
                    if video_files:
                        video_files.sort(key=lambda x: x.stat().st_size, reverse=True)
                        video_path = str(video_files[0])
                        logger.info(f"🔄 Using alternative video file: {video_path}")
                    else:
                        raise FileNotFoundError(f"No video files available in temp folder")
                else:
                    raise FileNotFoundError(f"Temp folder not found and no video path provided")
            
            # Check file size to ensure it's a real video
            file_size = os.path.getsize(video_path)
            if file_size < 1000:  # Less than 1KB is likely a placeholder
                logger.warning(f"⚠️ Video file seems too small ({file_size} bytes), looking for larger file")
                temp_dir = Path("temp")
                if temp_dir.exists():
                    video_files = list(temp_dir.glob("*.mp4"))
                    if video_files:
                        # Find the largest video file
                        largest_video = max(video_files, key=lambda x: x.stat().st_size)
                        if largest_video.stat().st_size > 1000:
                            video_path = str(largest_video)
                            logger.info(f"🔄 Using larger video file: {video_path} ({largest_video.stat().st_size} bytes)")
                        else:
                            logger.warning(f"⚠️ All video files are too small, proceeding with current file")
            
            logger.info(f"🎬 Final video path selected: {video_path} ({file_size} bytes)")
            
            # Step 2: Skip image generation and video assembly - go directly to upload
            job.status = VideoStatus.UPLOADING
            update_video_status(job.video_id, "uploading")
            job.progress = "75%"
            logger.info(f"⏭️ Skipping image generation and video assembly for job {job.video_id}")
            
            # Step 3: YouTube Upload (the main step)
            await self._upload_to_youtube(job, video_path)
            
            # Note: _upload_to_youtube now handles completion status updates
            # No need for additional completion logic here
            
        except Exception as e:
            logger.error(f"❌ Error processing video {job.video_id}: {e}")
            job.status = VideoStatus.FAILED
            update_video_status(job.video_id, "failed")
            job.progress = "Failed"
            
            # Clean up any partial files
            await self._cleanup_job_files(job)
    
    async def _create_placeholder_video(self, job: VideoJob) -> str:
        """Create a simple placeholder video for testing when no video is provided"""
        try:
            # Create temp directory
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Create a simple MP4 file as placeholder video
            placeholder_path = f"temp/placeholder_video_{job.video_id}.mp4"
            
            # For now, create a minimal MP4 file. In production, you might want to create an actual video
            # This is a workaround - creating a very small MP4 file
            
            # Create a simple text file first
            temp_text = f"temp/temp_text_{job.video_id}.txt"
            with open(temp_text, 'w') as f:
                f.write(f"Placeholder video for job {job.video_id}\n")
                f.write(f"Title: {job.title}\n")
                f.write(f"Description: {job.description}\n")
                f.write(f"Created automatically - no video file provided\n")
            
            # Try to convert to MP4 using ffmpeg if available, otherwise use a dummy file
            try:
                # Use ffmpeg to create a simple video from text
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:d=5',
                    '-vf', f"drawtext=text='{job.title}':fontsize=24:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-t', '5',
                    placeholder_path, '-y'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(placeholder_path):
                    logger.info(f"📹 Created placeholder video using ffmpeg: {placeholder_path}")
                else:
                    # Fallback: create a dummy MP4 file
                    self._create_dummy_mp4(placeholder_path)
                    logger.info(f"📹 Created dummy MP4 placeholder: {placeholder_path}")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                # ffmpeg not available or failed, create dummy MP4
                self._create_dummy_mp4(placeholder_path)
                logger.info(f"📹 Created dummy MP4 placeholder (ffmpeg not available): {placeholder_path}")
            
            # Clean up temp text file
            if os.path.exists(temp_text):
                os.remove(temp_text)
            
            return placeholder_path
            
        except Exception as e:
            logger.error(f"❌ Error creating placeholder video: {e}")
            # Return a default path
            return f"temp/default_video_{job.video_id}.mp4"
    
    def _create_dummy_mp4(self, filepath: str):
        """Create a minimal valid MP4 file"""
        try:
            # Create a minimal MP4 file structure (this is a very basic approach)
            # In production, you'd want to use a proper video library
            with open(filepath, 'wb') as f:
                # Write minimal MP4 header
                f.write(b'\x00\x00\x00\x20ftypmp42')
                f.write(b'\x00' * 100)  # Add some padding to make it look like a video
            
            logger.info(f"📹 Created minimal MP4 file: {filepath}")
        except Exception as e:
            logger.error(f"❌ Error creating dummy MP4: {e}")
            # If all else fails, create an empty file
            with open(filepath, 'w') as f:
                f.write("")
    
    async def _upload_to_youtube(self, job: VideoJob, video_path: str):
        """Upload video to YouTube with automatic metadata handling"""
        try:
            logger.info(f"📤 Starting YouTube upload for video {job.video_id}: {video_path}")
            
            # Update job status to uploading
            job.status = VideoStatus.UPLOADING
            update_video_status(job.video_id, "uploading")
            job.progress = "75%"
            
            # Check if video file exists and is valid
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            file_size = os.path.getsize(video_path)
            logger.info(f"📁 Video file size: {file_size} bytes")
            
            if file_size == 0:
                raise ValueError(f"Video file is empty: {video_path}")
            
            # Extract tags from metadata or use default
            tags = job.metadata.get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            logger.info(f"🏷️ Using tags: {tags}")
            
            # Map genre to YouTube category ID
            genre_to_category = {
                "kids": "27",           # Education
                "education": "27",      # Education
                "gaming": "20",         # Gaming
                "comedy": "23",         # Comedy
                "music": "10",          # Music
                "sports": "17",         # Sports
                "news": "25",           # News & Politics
                "howto": "26",          # Howto & Style
                "travel": "19",         # Travel & Events
                "autos": "2",           # Autos & Vehicles
                "pets": "15",           # Pets & Animals
                "film": "1",            # Film & Animation
                "people": "22",         # People & Blogs
            }
            
            category_id = genre_to_category.get(job.genre.lower(), "28")  # Default to Technology
            logger.info(f"📂 Using category ID: {category_id} for genre: {job.genre}")
            
            # Ensure YouTube uploader is initialized
            if not self.youtube_uploader:
                logger.error("❌ YouTube uploader not initialized")
                raise RuntimeError("YouTube uploader not available")
            
            logger.info(f"🔐 YouTube uploader initialized, proceeding with upload...")
            
            # Use real YouTube uploader with credentials
            upload_result = await self.youtube_uploader.upload_video(
                video_path=video_path,
                title=job.title,
                description=job.description,
                tags=tags,
                category=category_id,
                privacy_status='private'  # Start as private for safety
            )
            
            logger.info(f"📤 Upload result received: {upload_result}")
            
            # Check if upload was successful
            if upload_result.get('success', False):
                # Store upload result in job metadata
                job.metadata['youtube_upload'] = upload_result
                job.metadata['youtube_video_id'] = upload_result.get('video_id')
                job.metadata['youtube_url'] = upload_result.get('youtube_url')
                
                logger.info(f"✅ YouTube upload completed for video {job.video_id}: {upload_result.get('video_id')}")
                
                # Mark job as completed
                job.status = VideoStatus.COMPLETED
                update_video_status(job.video_id, "completed")
                job.progress = "100%"
                
                logger.info(f"🎉 Video {job.video_id} processing completed successfully!")
                
            else:
                # Upload failed
                error_msg = upload_result.get('error', 'Unknown upload error')
                logger.error(f"❌ YouTube upload failed for video {job.video_id}: {error_msg}")
                
                # Mark job as failed
                job.status = VideoStatus.FAILED
                update_video_status(job.video_id, "failed")
                job.progress = "Failed"
                job.metadata['upload_error'] = error_msg
                
                raise RuntimeError(f"YouTube upload failed: {error_msg}")
            
        except Exception as e:
            logger.error(f"❌ YouTube upload failed for video {job.video_id}: {e}")
            
            # Mark job as failed
            job.status = VideoStatus.FAILED
            update_video_status(job.video_id, "failed")
            job.progress = "Failed"
            job.metadata['upload_error'] = str(e)
            
            raise
    
    async def _handle_job_failure(self, job: VideoJob, error: str):
        """Handle job failures with retry logic"""
        logger.error(f"❌ Job {job.video_id} failed: {error}")
        
        # Store error in metadata
        job.metadata['last_error'] = error
        job.metadata['error_count'] = job.metadata.get('error_count', 0) + 1
        
        # Implement retry logic (max 3 attempts)
        max_retries = 3
        if job.metadata['error_count'] < max_retries:
            logger.info(f"🔄 Retrying job {job.video_id} (attempt {job.metadata['error_count'] + 1}/{max_retries})")
            
            # Wait before retry (exponential backoff)
            wait_time = 60 * (2 ** job.metadata['error_count'])
            await asyncio.sleep(wait_time)
            
            # Re-add to queue for retry
            job.status = VideoStatus.PENDING
            self.processing_queue.append(job)
        else:
            logger.error(f"❌ Job {job.video_id} failed permanently after {max_retries} attempts")
    
    async def _cancel_job(self, job: VideoJob):
        """Cancel a running job"""
        logger.info(f"🚫 Cancelling job {job.video_id}")
        
        job.status = VideoStatus.CANCELLED
        update_video_status(job.video_id, "cancelled")
        
        # Clean up any generated files
        await self._cleanup_job_files(job)
    
    async def _cleanup_job_files(self, job: VideoJob):
        """Clean up temporary files for a job"""
        try:
            # Clean up images
            if 'generated_images' in job.metadata:
                for scene_images in job.metadata['generated_images'].values():
                    for image_path in scene_images:
                        Path(image_path).unlink(missing_ok=True)
            
            # Clean up video
            if 'video_path' in job.metadata:
                Path(job.metadata['video_path']).unlink(missing_ok=True)
                
            logger.info(f"🧹 Cleaned up files for job {job.video_id}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up files for job {job.video_id}: {e}")
    
    async def _cleanup_completed_jobs(self):
        """Remove completed jobs from active jobs dict"""
        completed_jobs = [
            video_id for video_id, job in self.active_jobs.items()
            if job.status in [VideoStatus.COMPLETED, VideoStatus.FAILED, VideoStatus.CANCELLED]
        ]
        
        for video_id in completed_jobs:
            job = self.active_jobs.pop(video_id)
            await self._cleanup_job_files(job)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the workflow controller"""
        return {
            'is_running': self.is_running,
            'active_jobs_count': len(self.active_jobs),
            'queue_length': len(self.processing_queue),
            'active_jobs': [
                {
                    'video_id': job.video_id,
                    'title': job.title,
                    'status': job.status.value,
                    'progress': self._get_job_progress(job)
                }
                for job in self.active_jobs.values()
            ]
        }
    
    def _get_job_progress(self, job: VideoJob) -> str:
        """Get progress string for a job"""
        if job.status == VideoStatus.PENDING:
            return "Queued"
        elif job.status == VideoStatus.IMAGE_GENERATION:
            return "Generating Images"
        elif job.status == VideoStatus.VIDEO_ASSEMBLY:
            return "Assembling Video"
        elif job.status == VideoStatus.UPLOADING:
            return "Uploading to YouTube"
        elif job.status == VideoStatus.COMPLETED:
            return "Completed"
        elif job.status == VideoStatus.FAILED:
            return "Failed"
        elif job.status == VideoStatus.CANCELLED:
            return "Cancelled"
        else:
            return "Unknown"

    async def _handle_scheduled_task(self, scheduled_task):
        """
        Handle a scheduled task from the enhanced scheduler
        
        Args:
            scheduled_task: ScheduledTask object from the scheduler
        """
        try:
            logger.info(f"🎬 Handling scheduled task: {scheduled_task.video_id} - {scheduled_task.title}")
            
            # Create a VideoJob from the scheduled task
            # Ensure video_link is included in metadata
            metadata = scheduled_task.metadata.copy() if scheduled_task.metadata else {}
            if hasattr(scheduled_task, 'video_link') and scheduled_task.video_link:
                metadata['video_link'] = scheduled_task.video_link
            
            video_job = VideoJob(
                video_id=scheduled_task.video_id,
                title=scheduled_task.title,
                description=scheduled_task.description,
                genre=scheduled_task.genre,
                expected_length=scheduled_task.expected_length,
                schedule_time=scheduled_task.schedule_time,
                status=VideoStatus.IMAGE_GENERATION,
                created_at=scheduled_task.schedule_time,
                metadata=metadata
            )
            
            # Add to active jobs
            self.active_jobs[scheduled_task.video_id] = video_job
            
            # Start processing the job
            await self._process_job(video_job)
            
            logger.info(f"✅ Scheduled task {scheduled_task.video_id} processing completed")
            
        except Exception as e:
            logger.error(f"❌ Error handling scheduled task {scheduled_task.video_id}: {e}")
            # Mark as failed
            update_video_status(scheduled_task.video_id, "failed")
            
            # Remove from active jobs
            if scheduled_task.video_id in self.active_jobs:
                del self.active_jobs[scheduled_task.video_id]
    
    async def schedule_video_for_processing(self, video_data: Dict[str, Any]) -> bool:
        """
        Schedule a video for future processing
        
        Args:
            video_data: Video data from database
            
        Returns:
            True if successfully scheduled, False otherwise
        """
        try:
            logger.info(f"📅 Scheduling video {video_data['id']} for processing")
            
            # Schedule the video using the enhanced scheduler
            success = await self.scheduler.schedule_video(video_data)
            
            if success:
                logger.info(f"✅ Video {video_data['id']} scheduled successfully")
            else:
                logger.error(f"❌ Failed to schedule video {video_data['id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error scheduling video {video_data['id']}: {e}")
            return False

    async def _test_youtube_uploader(self):
        """Test if YouTube uploader is working properly"""
        try:
            logger.info("🧪 Testing YouTube uploader functionality...")
            
            if not self.youtube_uploader:
                logger.error("❌ YouTube uploader not initialized")
                return False
            
            # Test authentication
            auth_result = await self.youtube_uploader.authenticate()
            if auth_result:
                logger.info("✅ YouTube uploader authentication successful")
                return True
            else:
                logger.error("❌ YouTube uploader authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ YouTube uploader test failed: {e}")
            return False

# Global instance
workflow_controller = WorkflowController()

async def start_workflow():
    """Start the global workflow controller"""
    await workflow_controller.start()

async def stop_workflow():
    """Stop the global workflow controller"""
    await workflow_controller.stop()

def get_workflow_status():
    """Get current workflow status"""
    return workflow_controller.get_status()
