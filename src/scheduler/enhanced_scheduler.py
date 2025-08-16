"""
Enhanced Scheduler for Automated Video Generation
Automatically picks up scheduled tasks from database and starts processing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from src.database.db_handler import (
    get_scheduled_videos, 
    get_videos_ready_for_processing,
    update_video_status,
    get_video_by_id
)

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    """Represents a scheduled video generation task"""
    video_id: int
    title: str
    description: str
    genre: str
    expected_length: int
    schedule_time: datetime
    status: str
    metadata: Dict[str, Any]

class EnhancedScheduler:
    """
    Enhanced scheduler that automatically monitors database and picks up scheduled tasks
    """
    
    def __init__(self, workflow_callback: Optional[Callable] = None):
        self.scheduler = AsyncIOScheduler()
        self.workflow_callback = workflow_callback
        self.monitoring_task = None
        self.is_running = False
        
        # Configuration
        self.check_interval = 60  # Check database every 60 seconds
        self.max_concurrent_tasks = 3
        self.active_tasks: Dict[int, ScheduledTask] = {}
        
        logger.info("📅 Enhanced Scheduler initialized")
    
    async def start(self):
        """Start the enhanced scheduler"""
        try:
            # Start the APScheduler
            self.scheduler.start()
            
            # Start the database monitoring task
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._monitor_database())
            
            logger.info("✅ Enhanced Scheduler started successfully")
            logger.info(f"   📊 Monitoring database every {self.check_interval} seconds")
            logger.info(f"   🎯 Max concurrent tasks: {self.max_concurrent_tasks}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start enhanced scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the enhanced scheduler"""
        try:
            self.is_running = False
            
            # Stop the monitoring task
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Stop the APScheduler
            self.scheduler.shutdown()
            
            logger.info("🛑 Enhanced Scheduler stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping enhanced scheduler: {e}")
    
    async def _monitor_database(self):
        """Continuously monitor database for scheduled tasks"""
        logger.info("🔍 Starting database monitoring...")
        
        while self.is_running:
            try:
                await self._check_for_scheduled_tasks()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("🛑 Database monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in database monitoring: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_for_scheduled_tasks(self):
        """Check database for videos ready to be processed"""
        try:
            # Get videos that are ready for processing
            ready_videos = get_videos_ready_for_processing()
            
            if not ready_videos:
                return
            
            logger.info(f"🔍 Found {len(ready_videos)} videos ready for processing")
            
            # Process each ready video
            for video_data in ready_videos:
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    logger.info(f"⏳ Max concurrent tasks reached ({self.max_concurrent_tasks}), waiting...")
                    break
                
                await self._process_scheduled_video(video_data)
                
        except Exception as e:
            logger.error(f"❌ Error checking for scheduled tasks: {e}")
    
    async def _process_scheduled_video(self, video_data: Dict[str, Any]):
        """Process a scheduled video"""
        video_id = video_data['id']
        
        try:
            # Check if video is already being processed
            if video_id in self.active_tasks:
                logger.info(f"⏳ Video {video_id} already being processed")
                return
            
            # Check if video still exists and is still pending
            current_video = get_video_by_id(video_id)
            if not current_video or current_video['status'] != 'pending':
                logger.info(f"⚠️ Video {video_id} no longer available or not pending")
                return
            
            # Create scheduled task
            scheduled_task = ScheduledTask(
                video_id=video_id,
                title=video_data['title'],
                description=video_data['description'],
                genre=video_data['genre'],
                expected_length=video_data['expected_length'],
                schedule_time=video_data['schedule_time'],
                status=video_data['status'],
                metadata={
                    'platforms': video_data.get('platforms'),
                    'video_type': video_data.get('video_type'),
                    'music_pref': video_data.get('music_pref'),
                    'channel_name': video_data.get('channel_name'),
                    'extra_metadata': video_data.get('extra_metadata')
                }
            )
            
            # Add to active tasks
            self.active_tasks[video_id] = scheduled_task
            
            # Update status to image generation
            update_video_status(video_id, 'image_generation')
            
            logger.info(f"🎬 Starting scheduled video processing: {video_id} - {video_data['title']}")
            
            # Call workflow callback if available
            if self.workflow_callback:
                try:
                    await self.workflow_callback(scheduled_task)
                except Exception as e:
                    logger.error(f"❌ Error in workflow callback for video {video_id}: {e}")
                    # Mark as failed
                    update_video_status(video_id, 'failed')
                    if video_id in self.active_tasks:
                        del self.active_tasks[video_id]
            else:
                logger.warning(f"⚠️ No workflow callback registered for video {video_id}")
                
        except Exception as e:
            logger.error(f"❌ Error processing scheduled video {video_id}: {e}")
            # Mark as failed
            update_video_status(video_id, 'failed')
            if video_id in self.active_tasks:
                del self.active_tasks[video_id]
    
    async def schedule_video(self, video_data: Dict[str, Any]) -> bool:
        """Schedule a video for future processing"""
        try:
            video_id = video_data['id']
            schedule_time = video_data['schedule_time']
            
            if not schedule_time:
                logger.warning(f"⚠️ No schedule time for video {video_id}")
                return False
            
            # Parse schedule time if it's a string
            if isinstance(schedule_time, str):
                try:
                    schedule_time = datetime.fromisoformat(schedule_time)
                except:
                    logger.error(f"❌ Invalid schedule time format for video {video_id}: {schedule_time}")
                    return False
            
            # Create APScheduler job
            job_id = f"video_{video_id}_{int(schedule_time.timestamp())}"
            
            self.scheduler.add_job(
                func=self._execute_scheduled_video,
                trigger=DateTrigger(run_date=schedule_time),
                args=[video_id],
                id=job_id,
                name=f"Video {video_id}: {video_data['title']}",
                max_instances=1
            )
            
            logger.info(f"📅 Scheduled video {video_id} for {schedule_time}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule video: {e}")
            return False
    
    async def _execute_scheduled_video(self, video_id: int):
        """Execute a scheduled video (called by APScheduler)"""
        try:
            logger.info(f"🎬 Executing scheduled video {video_id}")
            
            # Get current video data
            video_data = get_video_by_id(video_id)
            if not video_data:
                logger.error(f"❌ Video {video_id} not found")
                return
            
            # Check if it's ready to process
            if video_data['status'] == 'pending':
                await self._process_scheduled_video(video_data)
            else:
                logger.info(f"⚠️ Video {video_id} status is {video_data['status']}, skipping")
                
        except Exception as e:
            logger.error(f"❌ Error executing scheduled video {video_id}: {e}")
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs from APScheduler"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'job_id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            return jobs
        except Exception as e:
            logger.error(f"❌ Error getting scheduled jobs: {e}")
            return []
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get currently active processing tasks"""
        try:
            tasks = []
            for video_id, task in self.active_tasks.items():
                tasks.append({
                    'video_id': video_id,
                    'title': task.title,
                    'description': task.description,
                    'genre': task.genre,
                    'schedule_time': task.schedule_time.isoformat() if task.schedule_time else None,
                    'status': task.status,
                    'expected_length': task.expected_length
                })
            return tasks
        except Exception as e:
            logger.error(f"❌ Error getting active tasks: {e}")
            return []
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        try:
            return {
                'is_running': self.is_running,
                'active_task_count': len(self.active_tasks),
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'scheduled_job_count': len(self.scheduler.get_jobs()),
                'check_interval_seconds': self.check_interval
            }
        except Exception as e:
            logger.error(f"❌ Error getting scheduler stats: {e}")
            return {}
    
    async def cancel_video_processing(self, video_id: int) -> bool:
        """Cancel processing of a specific video"""
        try:
            if video_id in self.active_tasks:
                # Update status to cancelled
                update_video_status(video_id, 'cancelled')
                
                # Remove from active tasks
                del self.active_tasks[video_id]
                
                logger.info(f"🚫 Cancelled processing for video {video_id}")
                return True
            else:
                logger.warning(f"⚠️ Video {video_id} not in active tasks")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cancelling video {video_id}: {e}")
            return False
    
    def get_video_by_id(self, video_id: int):
        """Get video data by ID from database"""
        try:
            return get_video_by_id(video_id)
        except Exception as e:
            logger.error(f"❌ Error getting video {video_id}: {e}")
            return None
