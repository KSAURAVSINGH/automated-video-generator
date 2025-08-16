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
                    job = VideoJob(
                        video_id=video_data['id'],
                        title=video_data['title'],
                        description=video_data['description'],
                        genre=video_data['genre'],
                        expected_length=video_data['expected_length'],
                        schedule_time=datetime.fromisoformat(video_data['schedule_time']),
                        status=VideoStatus.PENDING,
                        created_at=datetime.now(),
                        metadata=json.loads(video_data.get('extra_metadata', '{}'))
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
            # Check if we should skip generation and use existing video
            if job.metadata.get('skip_generation', False):
                if job.metadata.get('use_existing_video', False) and job.metadata.get('existing_video_path'):
                    # Use the specified existing video file
                    existing_video_path = job.metadata.get('existing_video_path')
                    logger.info(f"⏭️ Using existing video file: {existing_video_path}")
                    
                    # Set the video path in metadata
                    job.metadata['video_path'] = existing_video_path
                    job.metadata['generation_method'] = 'existing_video'
                    
                    # Skip to video assembly
                    job.status = VideoStatus.VIDEO_ASSEMBLY
                    update_video_status(job.video_id, "video_assembly")
                    job.progress = "50%"
                    logger.info(f"✅ Using existing video: {existing_video_path}")
                else:
                    # Use mock video
                    logger.info(f"⏭️ Skipping video generation for video {job.video_id} (using mock video)")
                    await self._process_mock_video(job)
            else:
                # Step 1: Generate video using Pyramid Flow (if enabled) or fallback to image-based
                if PYRAMID_FLOW_ENABLED and self.pyramid_flow_generator:
                    await self._generate_video_with_pyramid_flow(job)
                else:
                    await self._generate_images(job)
                    await self._assemble_video(job)
            
            # Step 2: YouTube Upload
            await self._upload_to_youtube(job)
            
            # Step 3: Mark as completed
            job.status = VideoStatus.COMPLETED
            update_video_status(job.video_id, "completed")
            job.progress = "100%"
            logger.info(f"✅ Video {job.video_id} processing completed successfully.")
            
        except Exception as e:
            logger.error(f"❌ Error processing video {job.video_id}: {e}")
            job.status = VideoStatus.FAILED
            update_video_status(job.video_id, "failed")
            job.progress = "Failed"
            
            # Clean up any partial files
            await self._cleanup_job_files(job)
    
    async def _process_mock_video(self, job: VideoJob):
        """Process job using mock video instead of generating new one"""
        try:
            logger.info(f"🎬 Processing mock video for job {job.video_id}")
            
            # Step 1: Mock image generation (skip actual generation)
            job.status = VideoStatus.IMAGE_GENERATION
            update_video_status(job.video_id, "image_generation")
            job.progress = "25%"
            logger.info(f"🖼️ Mock image generation completed for video {job.video_id}")
            
            # Step 2: Mock video assembly (use existing video)
            job.status = VideoStatus.VIDEO_ASSEMBLY
            update_video_status(job.video_id, "video_assembly")
            job.progress = "50%"
            
            # Find an existing video file to use
            mock_video_path = self._find_mock_video()
            if mock_video_path:
                job.metadata['video_path'] = mock_video_path
                job.metadata['generation_method'] = 'mock_video'
                logger.info(f"🎬 Mock video assembly completed: {mock_video_path}")
            else:
                # Create a simple mock video if none exists
                mock_video_path = await self._create_simple_mock_video(job)
                job.metadata['video_path'] = mock_video_path
                job.metadata['generation_method'] = 'simple_mock'
                logger.info(f"🎬 Simple mock video created: {mock_video_path}")
            
            job.progress = "75%"
            logger.info(f"✅ Mock video processing completed for video {job.video_id}")
            
        except Exception as e:
            logger.error(f"❌ Error in mock video processing for video {job.video_id}: {e}")
            raise
    
    def _find_mock_video(self) -> Optional[str]:
        """Find an existing video file to use as mock"""
        try:
            temp_dir = Path("temp")
            if temp_dir.exists():
                # Look for existing video files
                for video_file in temp_dir.rglob("*.mp4"):
                    if video_file.stat().st_size > 1000:  # At least 1KB
                        return str(video_file)
            return None
        except Exception as e:
            logger.error(f"❌ Error finding mock video: {e}")
            return None
    
    async def _create_simple_mock_video(self, job: VideoJob) -> str:
        """Create a simple mock video file for testing"""
        try:
            # Create temp directory
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Create a simple text file as mock video
            mock_video_path = f"temp/mock_video_{job.video_id}.mp4"
            
            with open(mock_video_path, 'w') as f:
                f.write(f"Mock video for job {job.video_id}\n")
                f.write(f"Title: {job.title}\n")
                f.write(f"Description: {job.description}\n")
                f.write(f"Created for testing purposes\n")
            
            logger.info(f"📝 Created simple mock video: {mock_video_path}")
            return mock_video_path
            
        except Exception as e:
            logger.error(f"❌ Error creating simple mock video: {e}")
            raise
    
    async def _generate_images(self, job: VideoJob):
        """Generate images for the video"""
        logger.info(f"🎨 Generating images for video {job.video_id}")
        
        job.status = VideoStatus.IMAGE_GENERATION
        update_video_status(job.video_id, "image_generation")
        
        # Generate story images based on the prompt
        story_prompt = f"{job.title}: {job.description}"
        
        # Generate multiple images for the story
        image_paths = self.image_manager.generate_story_images(
            video_id=job.video_id,
            story_prompt=story_prompt,
            num_scenes=5,  # 5 scenes for the video
            scene_variations=2  # 2 variations per scene
        )
        
        # Store image paths in job metadata
        job.metadata['generated_images'] = image_paths
        job.metadata['image_count'] = sum(len(images) for images in image_paths.values())
        
        logger.info(f"✅ Generated {job.metadata['image_count']} images for video {job.video_id}")
    
    async def _generate_video_with_pyramid_flow(self, job: VideoJob):
        """Generate video directly using Pyramid Flow text-to-video"""
        logger.info(f"🎬 Generating video with Pyramid Flow for video {job.video_id}")
        
        job.status = VideoStatus.VIDEO_ASSEMBLY
        update_video_status(job.video_id, "video_assembly")
        
        # Create story prompt from title and description
        story_prompt = f"{job.title}: {job.description}"
        
        # Generate video using Pyramid Flow
        video_path = await generate_video_with_pyramid_flow(
            video_id=job.video_id,
            prompt=story_prompt,
            preset="standard"  # Can be customized based on job requirements
        )
        
        if video_path:
            # Store video path in job metadata
            job.metadata['video_path'] = video_path
            job.metadata['generation_method'] = 'pyramid_flow'
            job.metadata['story_prompt'] = story_prompt
            
            logger.info(f"✅ Video generated with Pyramid Flow: {video_path}")
        else:
            # Fallback to image-based generation if Pyramid Flow fails
            logger.warning(f"⚠️ Pyramid Flow generation failed, falling back to image-based method")
            await self._generate_images(job)
            await self._assemble_video(job)
    
    async def _assemble_video(self, job: VideoJob):
        """Assemble the final video from images and audio"""
        logger.info(f"🎬 Assembling video for video {job.video_id}")
        
        job.status = VideoStatus.VIDEO_ASSEMBLY
        update_video_status(job.video_id, "video_assembly")
        
        # Get the generated images
        image_paths = job.metadata.get('generated_images', {})
        
        # Create video from images
        video_path = self.video_editor.create_video_from_images(
            video_id=job.video_id,
            image_paths=image_paths,
            duration=job.expected_length,
            title=job.title,
            description=job.description
        )
        
        # Store video path in job metadata
        job.metadata['video_path'] = video_path
        
        logger.info(f"✅ Video assembled successfully: {video_path}")
    
    async def _upload_to_youtube(self, job: VideoJob):
        """Upload video to YouTube"""
        try:
            job.status = VideoStatus.UPLOADING
            update_video_status(job.video_id, "uploading")
            
            video_path = job.metadata.get('video_path')
            if not video_path:
                raise ValueError("No video path found in job metadata")
            
            # Check if this is a mock video but proceed with real upload
            if job.metadata.get('generation_method') in ['mock_video', 'simple_mock']:
                logger.info(f"🎬 Mock video detected for job {job.video_id}, but proceeding with real YouTube upload")
            
            # Real YouTube upload (when credentials are provided)
            logger.info(f"📤 Starting YouTube upload for video {job.video_id}")
            
            # Map genre to YouTube category ID
            genre_to_category = {
                "technology": "28",      # Science & Technology
                "entertainment": "24",   # Entertainment
                "education": "27",       # Education
                "gaming": "20",          # Gaming
                "music": "10",           # Music
                "sports": "17",          # Sports
                "news": "25",            # News & Politics
                "howto": "26",           # Howto & Style
                "travel": "19",          # Travel & Events
                "autos": "2",            # Autos & Vehicles
                "pets": "15",            # Pets & Animals
                "comedy": "23",          # Comedy
                "film": "1",             # Film & Animation
                "people": "22",          # People & Blogs
            }
            
            category_id = genre_to_category.get(job.genre.lower(), "28")  # Default to Technology
            
            # Use real YouTube uploader with credentials
            upload_result = await self.youtube_uploader.upload_video(
                video_path=video_path,
                title=job.title,
                description=job.description,
                tags=job.metadata.get('tags', []),
                category=category_id,
                privacy_status='private'  # Start as private for safety
            )
            
            # Store upload result in job metadata
            job.metadata['youtube_upload'] = upload_result
            
            logger.info(f"✅ YouTube upload completed for video {job.video_id}: {upload_result.get('video_id')}")
            
        except Exception as e:
            logger.error(f"❌ YouTube upload failed for video {job.video_id}: {e}")
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
            video_job = VideoJob(
                video_id=scheduled_task.video_id,
                title=scheduled_task.title,
                description=scheduled_task.description,
                genre=scheduled_task.genre,
                expected_length=scheduled_task.expected_length,
                schedule_time=scheduled_task.schedule_time,
                status=VideoStatus.IMAGE_GENERATION,
                created_at=scheduled_task.schedule_time,
                metadata=scheduled_task.metadata
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
