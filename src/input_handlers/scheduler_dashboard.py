"""
Scheduler Dashboard
Streamlit interface to monitor and control the automated video generation scheduler
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.db_handler import (
    get_all_videos, 
    get_video_processing_stats,
    get_scheduled_videos,
    get_videos_ready_for_processing
)
from src.core.workflow_controller import WorkflowController

def scheduler_dashboard():
    """Main scheduler dashboard interface"""
    
    st.set_page_config(
        page_title="Scheduler Dashboard", 
        page_icon="📅", 
        layout="wide"
    )
    
    st.title("📅 Scheduler Dashboard")
    st.markdown("Monitor and control the automated video generation system")
    st.markdown("---")
    
    # Initialize session state
    if 'workflow_controller' not in st.session_state:
        st.session_state.workflow_controller = None
        st.session_state.scheduler_running = False
    
    # Sidebar controls
    st.sidebar.title("🎛️ System Controls")
    
    # Start/Stop Workflow Controller
    if st.sidebar.button("🚀 Start Workflow Controller", 
                         disabled=st.session_state.scheduler_running):
        try:
            with st.spinner("Starting workflow controller..."):
                # Initialize workflow controller
                workflow_controller = WorkflowController()
                asyncio.run(workflow_controller.start())
                
                st.session_state.workflow_controller = workflow_controller
                st.session_state.scheduler_running = True
                
            st.success("✅ Workflow Controller started successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to start workflow controller: {e}")
    
    if st.sidebar.button("🛑 Stop Workflow Controller", 
                         disabled=not st.session_state.scheduler_running):
        try:
            with st.spinner("Stopping workflow controller..."):
                if st.session_state.workflow_controller:
                    asyncio.run(st.session_state.workflow_controller.stop())
                    st.session_state.workflow_controller = None
                    st.session_state.scheduler_running = False
                
            st.success("✅ Workflow Controller stopped successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to stop workflow controller: {e}")
    
    st.sidebar.markdown("---")
    
    # System Status
    st.sidebar.subheader("📊 System Status")
    if st.session_state.scheduler_running:
        st.sidebar.success("🟢 Running")
        
        # Get scheduler stats
        try:
            if st.session_state.workflow_controller:
                scheduler_stats = st.session_state.workflow_controller.scheduler.get_scheduler_stats()
                
                st.sidebar.metric("Active Tasks", scheduler_stats.get('active_task_count', 0))
                st.sidebar.metric("Scheduled Jobs", scheduler_stats.get('scheduled_job_count', 0))
                st.sidebar.metric("Max Concurrent", scheduler_stats.get('max_concurrent_tasks', 0))
                
        except Exception as e:
            st.sidebar.error(f"Error getting stats: {e}")
    else:
        st.sidebar.error("🔴 Stopped")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎬 Video Processing Status")
        
        # Get database stats
        try:
            db_stats = get_video_processing_stats()
            
            # Create metrics
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            
            with metrics_col1:
                st.metric("Pending", db_stats.get('pending', 0))
            
            with metrics_col2:
                st.metric("Image Generation", db_stats.get('image_generation', 0))
            
            with metrics_col3:
                st.metric("Video Assembly", db_stats.get('video_assembly', 0))
            
            with metrics_col4:
                st.metric("Completed", db_stats.get('completed', 0))
            
        except Exception as e:
            st.error(f"Error getting database stats: {e}")
        
        # Video list
        st.subheader("📋 Video Queue")
        
        try:
            all_videos = get_all_videos()
            
            if all_videos:
                # Create a DataFrame-like display
                for video in all_videos[:10]:  # Show first 10
                    with st.expander(f"🎬 {video['title']} (ID: {video['id']})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Description:** {video['description']}")
                            st.write(f"**Genre:** {video['genre']}")
                            st.write(f"**Expected Length:** {video['expected_length']} seconds")
                            st.write(f"**Status:** {video['status']}")
                        
                        with col2:
                            st.write(f"**Schedule Time:** {video['schedule_time']}")
                            st.write(f"**Created:** {video['created_at']}")
                            st.write(f"**Updated:** {video['updated_at']}")
                            
                            # Status badge
                            status_color = {
                                'pending': '🟡',
                                'image_generation': '🔵',
                                'video_assembly': '🟠',
                                'uploading': '🟣',
                                'completed': '🟢',
                                'failed': '🔴',
                                'cancelled': '⚫'
                            }.get(video['status'], '⚪')
                            
                            st.write(f"**Status:** {status_color} {video['status']}")
                        
                        # Action buttons
                        if video['status'] == 'pending':
                            if st.button(f"⏸️ Pause {video['id']}", key=f"pause_{video['id']}"):
                                st.info("Pause functionality coming soon...")
                            
                            if st.button(f"❌ Cancel {video['id']}", key=f"cancel_{video['id']}"):
                                st.info("Cancel functionality coming soon...")
                        
                        elif video['status'] in ['image_generation', 'video_assembly']:
                            st.info("🔄 Video is currently being processed...")
                        
                        elif video['status'] == 'completed':
                            st.success("✅ Video processing completed!")
                        
                        elif video['status'] == 'failed':
                            st.error("❌ Video processing failed")
                            if st.button(f"🔄 Retry {video['id']}", key=f"retry_{video['id']}"):
                                st.info("Retry functionality coming soon...")
                
                if len(all_videos) > 10:
                    st.info(f"Showing first 10 videos. Total: {len(all_videos)}")
            else:
                st.info("📭 No videos found in database")
                
        except Exception as e:
            st.error(f"Error getting videos: {e}")
    
    with col2:
        st.subheader("📅 Scheduled Jobs")
        
        try:
            if st.session_state.scheduler_running and st.session_state.workflow_controller:
                # Get scheduled jobs
                scheduled_jobs = st.session_state.workflow_controller.scheduler.get_scheduled_jobs()
                active_tasks = st.session_state.workflow_controller.scheduler.get_active_tasks()
                
                if scheduled_jobs:
                    st.write(f"**Scheduled:** {len(scheduled_jobs)}")
                    for job in scheduled_jobs[:5]:  # Show first 5
                        st.write(f"📋 {job['name']}")
                        if job['next_run_time']:
                            st.write(f"   ⏰ {job['next_run_time']}")
                else:
                    st.info("📭 No scheduled jobs")
                
                st.markdown("---")
                
                if active_tasks:
                    st.write(f"**Active:** {len(active_tasks)}")
                    for task in active_tasks[:5]:  # Show first 5
                        st.write(f"🎬 {task['title']}")
                        st.write(f"   📊 {task['status']}")
                else:
                    st.info("📭 No active tasks")
                    
            else:
                st.info("⚠️ Workflow Controller not running")
                
        except Exception as e:
            st.error(f"Error getting scheduler info: {e}")
        
        st.markdown("---")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("🔄 Refresh Status"):
            st.rerun()
        
        if st.button("📊 System Health Check"):
            try:
                if st.session_state.scheduler_running:
                    st.success("✅ System is running")
                    
                    # Check database connection
                    try:
                        get_video_processing_stats()
                        st.success("✅ Database connection OK")
                    except:
                        st.error("❌ Database connection failed")
                        
                else:
                    st.warning("⚠️ System is not running")
                    
            except Exception as e:
                st.error(f"❌ Health check failed: {e}")
    
    # Bottom section - Real-time monitoring
    st.markdown("---")
    st.subheader("🔍 Real-time Monitoring")
    
    # Auto-refresh every 30 seconds
    if st.session_state.scheduler_running:
        st.info("🔄 Auto-refreshing every 30 seconds...")
        
        # Placeholder for real-time updates
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Last Check", datetime.now().strftime("%H:%M:%S"))
        
        with col2:
            st.metric("System Uptime", "Running")
        
        with col3:
            st.metric("Next Check", (datetime.now() + timedelta(seconds=30)).strftime("%H:%M:%S"))
    else:
        st.warning("⚠️ Enable real-time monitoring by starting the Workflow Controller")
    
    # Footer
    st.markdown("---")
    st.markdown("*Scheduler Dashboard - Automated Video Generation System*")

def main():
    """Main function for standalone execution"""
    scheduler_dashboard()

if __name__ == "__main__":
    main()
