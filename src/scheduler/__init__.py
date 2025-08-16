"""
Scheduler module for the Automated Video Generator
Handles job scheduling and task management
"""

from .job_manager import JobScheduler, ScheduledJob

__all__ = [
    'JobScheduler',
    'ScheduledJob'
]
