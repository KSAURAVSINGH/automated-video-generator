"""
Job Scheduler for Automated Video Generation
Manages scheduled tasks using APScheduler
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

@dataclass
class ScheduledJob:
    """Represents a scheduled job"""
    job_id: str
    video_id: int
    schedule_time: datetime
    job_type: str
    metadata: Dict[str, Any]

class JobScheduler:
    """
    Manages scheduled video generation jobs
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}
        self.job_callbacks: Dict[str, callable] = {}
        
        logger.info("📅 Job Scheduler initialized")
    
    async def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("✅ Job Scheduler started")
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("🛑 Job Scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    
    async def schedule_job(self, job_data: Any, callback: Optional[callable] = None):
        """
        Schedule a new job
        
        Args:
            job_data: Job data containing schedule_time and other info
            callback: Optional callback function to execute when job runs
        """
        try:
            # Create unique job ID
            job_id = f"video_{job_data.video_id}_{int(job_data.schedule_time.timestamp())}"
            
            # Schedule the job
            trigger = DateTrigger(run_date=job_data.schedule_time)
            
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                args=[job_id, job_data.video_id],
                id=job_id,
                name=f"Video Generation {job_data.video_id}",
                max_instances=1
            )
            
            # Store job info
            scheduled_job = ScheduledJob(
                job_id=job_id,
                video_id=job_data.video_id,
                schedule_time=job_data.schedule_time,
                job_type="video_generation",
                metadata={
                    'title': getattr(job_data, 'title', 'Unknown'),
                    'description': getattr(job_data, 'description', ''),
                    'genre': getattr(job_data, 'genre', 'Unknown')
                }
            )
            
            self.scheduled_jobs[job_id] = scheduled_job
            
            if callback:
                self.job_callbacks[job_id] = callback
            
            logger.info(f"📅 Scheduled job {job_id} for {job_data.schedule_time}")
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule job: {e}")
            raise
    
    async def _execute_job(self, job_id: str, video_id: int):
        """Execute a scheduled job"""
        try:
            logger.info(f"🎬 Executing scheduled job {job_id} for video {video_id}")
            
            # Execute callback if registered
            if job_id in self.job_callbacks:
                callback = self.job_callbacks.pop(job_id)
                await callback(video_id)
            
            # Remove from scheduled jobs
            if job_id in self.scheduled_jobs:
                del self.scheduled_jobs[job_id]
            
            logger.info(f"✅ Scheduled job {job_id} completed")
            
        except Exception as e:
            logger.error(f"❌ Error executing scheduled job {job_id}: {e}")
    
    async def cancel_job(self, job_id: str):
        """Cancel a scheduled job"""
        try:
            if job_id in self.scheduled_jobs:
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[job_id]
                
                if job_id in self.job_callbacks:
                    del self.job_callbacks[job_id]
                
                logger.info(f"🚫 Cancelled scheduled job {job_id}")
                return True
            else:
                logger.warning(f"⚠️ Job {job_id} not found in scheduled jobs")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cancelling job {job_id}: {e}")
            return False
    
    async def cancel_video_jobs(self, video_id: int):
        """Cancel all jobs for a specific video"""
        try:
            cancelled_count = 0
            jobs_to_cancel = [
                job_id for job_id, job in self.scheduled_jobs.items()
                if job.video_id == video_id
            ]
            
            for job_id in jobs_to_cancel:
                if await self.cancel_job(job_id):
                    cancelled_count += 1
            
            logger.info(f"🚫 Cancelled {cancelled_count} jobs for video {video_id}")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"❌ Error cancelling jobs for video {video_id}: {e}")
            return 0
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs"""
        try:
            jobs = []
            for job_id, job in self.scheduled_jobs.items():
                jobs.append({
                    'job_id': job_id,
                    'video_id': job.video_id,
                    'schedule_time': job.schedule_time.isoformat(),
                    'job_type': job.job_type,
                    'metadata': job.metadata,
                    'time_until_execution': (job.schedule_time - datetime.now()).total_seconds()
                })
            
            return sorted(jobs, key=lambda x: x['schedule_time'])
            
        except Exception as e:
            logger.error(f"❌ Error getting scheduled jobs: {e}")
            return []
    
    def get_job_count(self) -> int:
        """Get total number of scheduled jobs"""
        return len(self.scheduled_jobs)
    
    def is_job_scheduled(self, video_id: int) -> bool:
        """Check if a video has any scheduled jobs"""
        return any(job.video_id == video_id for job in self.scheduled_jobs.values())
    
    async def reschedule_job(self, job_id: str, new_schedule_time: datetime):
        """Reschedule a job to a new time"""
        try:
            if job_id in self.scheduled_jobs:
                # Cancel existing job
                await self.cancel_job(job_id)
                
                # Get original job data
                original_job = self.scheduled_jobs.get(job_id)
                if original_job:
                    # Create new job data
                    from src.core.workflow_controller import VideoJob
                    new_job_data = VideoJob(
                        video_id=original_job.video_id,
                        title=original_job.metadata.get('title', 'Unknown'),
                        description=original_job.metadata.get('description', ''),
                        genre=original_job.metadata.get('genre', 'Unknown'),
                        expected_length=0,  # Will be filled from database
                        schedule_time=new_schedule_time,
                        status=None,  # Will be set by workflow controller
                        created_at=datetime.now(),
                        metadata={}
                    )
                    
                    # Schedule new job
                    await self.schedule_job(new_job_data)
                    
                    logger.info(f"📅 Rescheduled job {job_id} to {new_schedule_time}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error rescheduling job {job_id}: {e}")
            return False
