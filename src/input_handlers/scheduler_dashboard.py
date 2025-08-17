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
    get_videos_ready_for_processing,
    update_video_status,
    get_video_by_id
)
from src.core.workflow_controller import WorkflowController, start_workflow, stop_workflow, get_workflow_status

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
    
    # Initialize session state for dashboard persistence
    if 'dashboard_last_refresh' not in st.session_state:
        st.session_state.dashboard_last_refresh = datetime.now()
    
    if 'dashboard_auto_refresh' not in st.session_state:
        st.session_state.dashboard_auto_refresh = True
    
    if 'dashboard_expanded_sections' not in st.session_state:
        st.session_state.dashboard_expanded_sections = {
            'pending': False,
            'processing': False,
            'completed': False
        }
    
    # Initialize session state for workflow controller
    if 'workflow_controller' not in st.session_state:
        st.session_state.workflow_controller = None
        st.session_state.scheduler_running = False
        st.session_state.workflow_status = None
    
    # Initialize automatic processing
    if 'auto_processing_enabled' not in st.session_state:
        st.session_state.auto_processing_enabled = True
    
    # Initialize auto processing task
    if 'auto_processing_task' not in st.session_state:
        st.session_state.auto_processing_task = None
    
    def is_auto_processing_enabled():
        """Check if auto-processing is enabled using flag file"""
        flag_file = Path("temp/auto_processing_enabled.flag")
        return flag_file.exists()
    
    def stop_auto_processing():
        """Safely stop the automatic processing background thread"""
        try:
            # Delete the flag file to signal the thread to stop
            flag_file = Path("temp/auto_processing_enabled.flag")
            if flag_file.exists():
                flag_file.unlink()
                print("🛑 Auto-processing flag file removed")
            
            # Wait for thread to finish
            if st.session_state.auto_processing_task and st.session_state.auto_processing_task.is_alive():
                st.session_state.auto_processing_task.join(timeout=5)  # Wait up to 5 seconds
                st.session_state.auto_processing_task = None
                print("🛑 Auto-processing thread stopped")
                return True
            else:
                print("🛑 No active auto-processing thread found")
                return True
        except Exception as e:
            print(f"❌ Error stopping auto-processing: {e}")
            return False
    
    # Sidebar controls
    st.sidebar.title("🎛️ System Controls")
    
    # Automatic Processing Toggle
    st.sidebar.subheader("🤖 Automatic Processing")
    
    # Check current status using flag file
    current_auto_status = is_auto_processing_enabled()
    
    auto_processing = st.sidebar.checkbox(
        "Enable Automatic Processing", 
        value=current_auto_status,
        key="auto_processing_toggle",
        help="Automatically process videos when they're ready"
    )
    
    # Update session state and flag file based on toggle
    if auto_processing != current_auto_status:
        if auto_processing:
            # Enable auto-processing
            flag_file = Path("temp/auto_processing_enabled.flag")
            flag_file.parent.mkdir(exist_ok=True)
            flag_file.touch()
            st.session_state.auto_processing_enabled = True
            st.sidebar.success("✅ Automatic processing enabled")
        else:
            # Disable auto-processing
            if stop_auto_processing():
                st.session_state.auto_processing_enabled = False
                st.sidebar.success("🛑 Automatic processing disabled")
            else:
                st.sidebar.error("❌ Failed to disable automatic processing")
                st.rerun()
    
    if st.session_state.auto_processing_enabled:
        st.sidebar.success("🟢 Automatic Processing: ENABLED")
        
        # Auto-process pending videos
        try:
            pending_videos = get_videos_ready_for_processing()
            if pending_videos:
                st.sidebar.info(f"📋 Found {len(pending_videos)} videos ready for processing")
                
                # Auto-start processing for each pending video
                for video_data in pending_videos:
                    video_id = video_data['id']
                    title = video_data['title']
                    
                    # Check if video is still pending
                    current_status = get_video_by_id(video_id)
                    if current_status and current_status['status'] == 'pending':
                        # Auto-start processing
                        try:
                            update_video_status(video_id, "uploading")
                            st.sidebar.success(f"🚀 Auto-started processing: {title[:30]}...")
                        except Exception as e:
                            st.sidebar.error(f"❌ Failed to auto-start: {title[:30]}...")
            else:
                st.sidebar.info("📭 No videos ready for processing")
        except Exception as e:
            st.sidebar.error(f"❌ Error checking pending videos: {e}")
    else:
        st.sidebar.warning("🟡 Automatic Processing: DISABLED")
    
    st.sidebar.markdown("---")
    
    # Workflow Controller Status
    st.sidebar.subheader("🚀 Workflow Controller")
    
    if not st.session_state.scheduler_running:
        if st.sidebar.button("🚀 Start Automated Processing", type="primary"):
            try:
                with st.spinner("Starting automated video processing system..."):
                    # Start the workflow controller
                    asyncio.run(start_workflow())
                    st.session_state.scheduler_running = True
                    st.session_state.workflow_status = "running"
                    
                st.success("✅ Automated processing system started successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to start automated processing: {e}")
                st.info("💡 Make sure you have the required credentials and dependencies set up")
    else:
        if st.sidebar.button("🛑 Stop Automated Processing", type="secondary"):
            try:
                with st.spinner("Stopping automated processing system..."):
                    # Stop the workflow controller
                    asyncio.run(stop_workflow())
                    st.session_state.scheduler_running = False
                    st.session_state.workflow_status = "stopped"
                
                st.success("✅ Automated processing system stopped successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to stop automated processing: {e}")
    
    # Show workflow status
    if st.session_state.scheduler_running:
        st.sidebar.success("🟢 Automated Processing: RUNNING")
        
        # Get workflow status
        try:
            workflow_status = get_workflow_status()
            if workflow_status:
                st.sidebar.metric("Active Jobs", workflow_status.get('active_jobs_count', 0))
                st.sidebar.metric("Queue Length", workflow_status.get('queue_length', 0))
                
                # Show active jobs
                active_jobs = workflow_status.get('active_jobs', [])
                if active_jobs:
                    st.sidebar.subheader("🔄 Active Processing Jobs")
                    for job in active_jobs[:3]:  # Show first 3
                        st.sidebar.write(f"🎬 {job['title'][:20]}...")
                        st.sidebar.write(f"   📊 {job['progress']}")
        except Exception as e:
            st.sidebar.error(f"Error getting workflow status: {e}")
    else:
        st.sidebar.error("🔴 Automated Processing: STOPPED")
        st.sidebar.info("💡 Click 'Start Automated Processing' to begin automatic video generation and upload")
    
    st.sidebar.markdown("---")
    
    # Refresh controls
    st.sidebar.subheader("🔄 Refresh Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox(
        "Auto-refresh every 30 seconds", 
        value=st.session_state.dashboard_auto_refresh,
        key="auto_refresh_toggle"
    )
    
    if auto_refresh != st.session_state.dashboard_auto_refresh:
        st.session_state.dashboard_auto_refresh = auto_refresh
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Manual Refresh"):
        st.session_state.dashboard_last_refresh = datetime.now()
        st.rerun()
    
    # Last refresh info
    st.sidebar.info(f"Last refresh: {st.session_state.dashboard_last_refresh.strftime('%H:%M:%S')}")
    
    st.sidebar.markdown("---")
    
    # Quick actions
    st.sidebar.subheader("⚡ Quick Actions")
    
    if st.button("🔄 Refresh Status"):
        st.rerun()
    
    # Automated Processing Status
    if is_auto_processing_enabled():
        st.sidebar.markdown("---")
        st.sidebar.subheader("🤖 Auto-Processing Status")
        
        try:
            # Get recent auto-processing activity
            pending_videos = get_videos_ready_for_processing()
            if pending_videos:
                st.sidebar.info(f"📋 {len(pending_videos)} videos ready for processing")
                
                # Show recent auto-processing activity
                for video_data in pending_videos[:3]:  # Show first 3
                    video_id = video_data['id']
                    title = video_data['title']
                    schedule_time = video_data['schedule_time']
                    
                    st.sidebar.write(f"🎬 {title[:25]}...")
                    st.sidebar.write(f"   ⏰ {schedule_time}")
                    
                    # Auto-start button for immediate processing
                    if st.sidebar.button(f"🚀 Process Now {video_id}", key=f"auto_process_{video_id}"):
                        try:
                            update_video_status(video_id, "uploading")
                            st.sidebar.success(f"✅ Started processing: {title[:20]}...")
                            st.rerun()
                        except Exception as e:
                            st.sidebar.error(f"❌ Failed to start: {e}")
            else:
                st.sidebar.info("📭 No videos ready for processing")
                
        except Exception as e:
            st.sidebar.error(f"❌ Error checking auto-processing: {e}")
    
    if st.button("📊 System Health Check"):
        try:
            if st.session_state.scheduler_running:
                st.success("✅ Automated processing system is running")
                
                # Check database connection
                try:
                    get_video_processing_stats()
                    st.success("✅ Database connection OK")
                except:
                    st.error("❌ Database connection failed")
                
                # Check workflow status
                try:
                    workflow_status = get_workflow_status()
                    if workflow_status:
                        st.success(f"✅ Workflow controller status: {workflow_status.get('is_running', 'Unknown')}")
                    else:
                        st.warning("⚠️ Workflow controller status unknown")
                except:
                    st.warning("⚠️ Could not get workflow controller status")
                    
            else:
                st.warning("⚠️ Automated processing system is not running")
                
        except Exception as e:
            st.error(f"❌ Health check failed: {e}")
    
    # Main content area - Three main sections
    st.subheader("🎬 Video Processing Overview")
    
    # Background automatic processing task
    if is_auto_processing_enabled():
        # Create a background task for automatic processing
        if not st.session_state.auto_processing_task or not st.session_state.auto_processing_task.is_alive():
            import threading
            import time
            
            def auto_process_videos():
                """Background task to automatically process pending videos"""
                # This function runs in a separate thread without Streamlit context
                # Use a flag file or database-based approach instead of session state
                
                # Create a flag file to track if auto-processing should continue
                flag_file = Path("temp/auto_processing_enabled.flag")
                flag_file.parent.mkdir(exist_ok=True)
                
                # Create the flag file to indicate auto-processing is enabled
                flag_file.touch()
                
                try:
                    while flag_file.exists():
                        try:
                            # Check if flag file still exists (user can delete it to stop)
                            if not flag_file.exists():
                                break
                            
                            # Get videos ready for processing
                            pending_videos = get_videos_ready_for_processing()
                            
                            for video_data in pending_videos:
                                video_id = video_data['id']
                                title = video_data['title']
                                
                                # Check if video is still pending
                                current_status = get_video_by_id(video_id)
                                if current_status and current_status['status'] == 'pending':
                                    # Auto-start processing
                                    try:
                                        update_video_status(video_id, "uploading")
                                        # Use print instead of st.success in background thread
                                        print(f"🚀 Auto-started processing: {title[:30]}...")
                                    except Exception as e:
                                        print(f"❌ Failed to auto-start: {title[:30]}... - Error: {e}")
                            
                            # Wait before next check
                            time.sleep(10)  # Check every 10 seconds
                            
                        except Exception as e:
                            print(f"❌ Auto-processing error: {e}")
                            time.sleep(30)  # Wait longer on error
                            
                except Exception as e:
                    print(f"❌ Critical auto-processing error: {e}")
                finally:
                    # Clean up flag file when thread ends
                    if flag_file.exists():
                        flag_file.unlink()
            
            # Start background thread
            try:
                st.session_state.auto_processing_task = threading.Thread(
                    target=auto_process_videos, 
                    daemon=True,
                    name="AutoProcessingThread"
                )
                st.session_state.auto_processing_task.start()
                
                st.info("🤖 Background automatic processing started")
            except Exception as e:
                st.error(f"❌ Failed to start background processing: {e}")
                st.session_state.auto_processing_task = None
    
    # Get database stats
    try:
        db_stats = get_video_processing_stats()
        
        # Create metrics
        metrics_col1, metrics_col2, metrics_col3, metrics_col4, metrics_col5 = st.columns(5)
        
        with metrics_col1:
            st.metric("⏳ Pending", db_stats.get('pending', 0))
        
        with metrics_col2:
            st.metric("🖼️ Image Generation", db_stats.get('image_generation', 0))
        
        with metrics_col3:
            st.metric("🎬 Video Assembly", db_stats.get('video_assembly', 0))
        
        with metrics_col4:
            st.metric("✅ Completed", db_stats.get('completed', 0))
        
        with metrics_col5:
            st.metric("❌ Failed", db_stats.get('failed', 0))
        
    except Exception as e:
        st.error(f"Error getting database stats: {e}")
    
    st.markdown("---")
    
    # Automated Processing Status
    if st.session_state.scheduler_running:
        st.subheader("🤖 Automated Processing Status")
        
        # Get workflow status
        try:
            workflow_status = get_workflow_status()
            if workflow_status:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🔄 Active Jobs", workflow_status.get('active_jobs_count', 0))
                
                with col2:
                    st.metric("📋 Queue Length", workflow_status.get('queue_length', 0))
                
                with col3:
                    st.metric("🚀 System Status", "Running" if workflow_status.get('is_running', False) else "Stopped")
                
                # Show active jobs details
                active_jobs = workflow_status.get('active_jobs', [])
                if active_jobs:
                    st.subheader("🔄 Currently Processing Jobs")
                    for job in active_jobs:
                        with st.expander(f"🎬 {job['title']} (ID: {job['video_id']})", expanded=False):
                            st.write(f"**Status:** {job['progress']}")
                            st.write(f"**Video ID:** {job['video_id']}")
                            st.write(f"**Title:** {job['title']}")
                            
                            # Progress indicator
                            if "Generating Images" in job['progress']:
                                st.info("🖼️ Generating images for video...")
                            elif "Assembling Video" in job['progress']:
                                st.info("🎬 Assembling video from images...")
                            elif "Uploading to YouTube" in job['progress']:
                                st.info("📤 Uploading video to YouTube...")
                            elif "Completed" in job['progress']:
                                st.success("✅ Video processing completed!")
                            elif "Failed" in job['progress']:
                                st.error("❌ Video processing failed")
                else:
                    st.info("📭 No jobs currently being processed")
                    
        except Exception as e:
            st.error(f"Error getting workflow status: {e}")
            st.info("💡 The workflow controller may not be fully initialized yet")
    
    st.markdown("---")
    
    # Section 1: Pending Schedules (Upcoming Videos)
    st.subheader("⏰ Pending Schedules - Upcoming Videos")
    st.markdown("*Videos scheduled to be processed in the future*")
    
    try:
        all_videos = get_all_videos()
        pending_videos = []
        upcoming_videos = []
        
        current_time = datetime.now()
        
        for video in all_videos:
            if video['status'] == 'pending' and video['schedule_time']:
                try:
                    # Parse schedule time
                    if isinstance(video['schedule_time'], str):
                        schedule_time = datetime.fromisoformat(video['schedule_time'].replace('Z', '+00:00'))
                    else:
                        schedule_time = video['schedule_time']
                    
                    # Calculate time until processing
                    time_until = schedule_time - current_time
                    
                    if time_until.total_seconds() > 0:
                        upcoming_videos.append({
                            'video': video,
                            'schedule_time': schedule_time,
                            'time_until': time_until
                        })
                    else:
                        pending_videos.append({
                            'video': video,
                            'schedule_time': schedule_time,
                            'time_until': time_until
                        })
                except Exception as e:
                    st.warning(f"Could not parse schedule time for video {video['id']}: {e}")
        
        # Sort by schedule time
        upcoming_videos.sort(key=lambda x: x['schedule_time'])
        pending_videos.sort(key=lambda x: x['schedule_time'])
        
        # Display upcoming videos (future schedules)
        if upcoming_videos:
            st.success(f"📅 Found {len(upcoming_videos)} upcoming scheduled videos")
            
            for item in upcoming_videos:
                video = item['video']
                schedule_time = item['schedule_time']
                time_until = item['time_until']
                
                # Format time display
                if time_until.days > 0:
                    time_display = f"{time_until.days} days, {time_until.seconds // 3600} hours"
                elif time_until.seconds > 3600:
                    time_display = f"{time_until.seconds // 3600} hours, {(time_until.seconds % 3600) // 60} minutes"
                else:
                    time_display = f"{time_until.seconds // 60} minutes"
                
                with st.expander(f"🎬 {video['title']} - ⏰ {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} (in {time_display})", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {video['id']}")
                        st.write(f"**Description:** {video['description'][:100]}...")
                        st.write(f"**Genre:** {video['genre']}")
                        st.write(f"**Expected Length:** {video['expected_length']} seconds")
                        st.write(f"**Platforms:** {video['platforms']}")
                    
                    with col2:
                        st.write(f"**Schedule Time:** {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Time Until Processing:** {time_display}")
                        st.write(f"**Created:** {video['created_at']}")
                        st.write(f"**Video Type:** {video['video_type']}")
                        
                        # Countdown timer
                        st.info(f"⏳ Will be processed in: {time_display}")
                        
                        # Manual processing button (for immediate processing)
                        if st.button(f"🚀 Process Now {video['id']}", key=f"process_now_{video['id']}"):
                            try:
                                # Update status directly to uploading - skip image generation completely
                                update_video_status(video['id'], "uploading")
                                st.success(f"✅ Video {video['id']} queued for immediate processing!")
                                st.info("🔄 Video moved directly to 'Currently Processing' section (skipping image generation)")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to queue video: {e}")
        else:
            st.info("📭 No upcoming scheduled videos found")
        
        # Display pending videos (ready for processing)
        if pending_videos:
            st.warning(f"🚀 Found {len(pending_videos)} videos ready for processing")
            
            for item in pending_videos:
                video = item['video']
                schedule_time = item['schedule_time']
                
                with st.expander(f"🎬 {video['title']} - ⏰ {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} (READY NOW)", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {video['id']}")
                        st.write(f"**Description:** {video['description'][:100]}...")
                        st.write(f"**Genre:** {video['genre']}")
                        st.write(f"**Expected Length:** {video['expected_length']} seconds")
                        st.write(f"**Platforms:** {video['platforms']}")
                    
                    with col2:
                        st.write(f"**Schedule Time:** {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Status:** Ready for processing")
                        st.write(f"**Created:** {video['created_at']}")
                        st.write(f"**Video Type:** {video['video_type']}")
                        
                        st.success("🚀 This video is ready to be processed now!")
                        
                        # Action buttons
                        if st.button(f"🎬 Process Now {video['id']}", key=f"process_{video['id']}"):
                            try:
                                # Update status directly to uploading - skip image generation completely
                                update_video_status(video['id'], "uploading")
                                st.success(f"✅ Video {video['id']} queued for immediate processing!")
                                st.info("🔄 Video moved directly to 'Currently Processing' section (skipping image generation)")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to queue video: {e}")
        
        elif not upcoming_videos:
            st.info("📭 No pending videos found")
            
    except Exception as e:
        st.error(f"Error getting pending videos: {e}")
    
    st.markdown("---")
    
    # Section 2: Currently Processing Videos
    st.subheader("🔄 Currently Processing Videos")
    st.markdown("*Videos currently being generated, assembled, or uploaded*")
    
    try:
        processing_videos = [v for v in all_videos if v['status'] in ['image_generation', 'video_assembly', 'uploading']]
        
        if processing_videos:
            st.info(f"🔄 Found {len(processing_videos)} videos currently being processed")
            
            for video in processing_videos:
                status_icons = {
                    'image_generation': '🖼️',
                    'video_assembly': '🎬',
                    'uploading': '📤'
                }
                
                status_icons_text = {
                    'image_generation': '🖼️ Generating Images (SKIPPED)',
                    'video_assembly': '🎬 Assembling Video (SKIPPED)',
                    'uploading': '📤 Uploading to YouTube'
                }
                
                status_icon = status_icons.get(video['status'], '⚪')
                status_text = status_icons_text.get(video['status'], 'Processing')
                
                with st.expander(f"{status_icon} {video['title']} - {status_text}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {video['id']}")
                        st.write(f"**Description:** {video['description'][:100]}...")
                        st.write(f"**Genre:** {video['genre']}")
                        st.write(f"**Expected Length:** {video['expected_length']} seconds")
                    
                    with col2:
                        st.write(f"**Status:** {status_icon} {status_text}")
                        st.write(f"**Created:** {video['created_at']}")
                        st.write(f"**Updated:** {video['updated_at']}")
                        st.write(f"**Video Type:** {video['video_type']}")
                        
                        # Progress indicator with better visual feedback
                        if video['status'] == 'image_generation':
                            st.info("⏭️ **Image Generation SKIPPED - Moving directly to upload**")
                            st.progress(0.75, text="75% - Image Generation Skipped, Going to Upload")
                        elif video['status'] == 'video_assembly':
                            st.info("⏭️ **Video Assembly SKIPPED - Moving directly to upload**")
                            st.progress(0.75, text="75% - Video Assembly Skipped, Going to Upload")
                        elif video['status'] == 'uploading':
                            st.info("📤 **Uploading video to YouTube...**")
                            st.progress(0.75, text="75% - YouTube Upload")
                        
                        # Show processing time
                        if 'updated_at' in video and video['updated_at']:
                            try:
                                if isinstance(video['updated_at'], str):
                                    updated_time = datetime.fromisoformat(video['updated_at'].replace('Z', '+00:00'))
                                else:
                                    updated_time = video['updated_at']
                                
                                processing_duration = current_time - updated_time
                                if processing_duration.total_seconds() > 0:
                                    minutes = int(processing_duration.total_seconds() // 60)
                                    st.write(f"**Processing Duration:** {minutes} minutes")
                            except:
                                pass
                        
                        # Automated processing info
                        st.success("🤖 **Fully Automated Processing**")
                        st.info("💡 This video is being processed automatically - no manual intervention needed!")
                        
                        # Show next expected step
                        if video['status'] == 'image_generation':
                            st.info("⏭️ **Next Step**: Image generation skipped, moving directly to YouTube upload")
                        elif video['status'] == 'video_assembly':
                            st.info("⏭️ **Next Step**: Video assembly skipped, moving directly to YouTube upload")
                        elif video['status'] == 'uploading':
                            st.info("⏭️ **Next Step**: Video will automatically be marked as completed")
                        
        else:
            st.info("📭 No videos currently being processed")
            
    except Exception as e:
        st.error(f"Error getting processing videos: {e}")
    
    st.markdown("---")
    
    # Section 3: Completed/Finished Videos
    st.subheader("✅ Completed & Finished Videos")
    st.markdown("*Videos that have finished processing, failed, or were cancelled*")
    
    try:
        completed_videos = [v for v in all_videos if v['status'] in ['completed', 'failed', 'cancelled']]
        
        if completed_videos:
            # Group by status
            status_groups = {}
            for video in completed_videos:
                status = video['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(video)
            
            # Display by status
            for status, videos in status_groups.items():
                status_icons = {
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '⏹️'
                }
                
                status_icons_text = {
                    'completed': '✅ Successfully Completed',
                    'failed': '❌ Processing Failed',
                    'cancelled': '⏹️ Processing Cancelled'
                }
                
                status_icon = status_icons.get(status, '⚪')
                status_text = status_icons_text.get(status, status.replace('_', ' ').title())
                
                st.subheader(f"{status_icon} {status_text} Videos ({len(videos)})")
                
                for video in videos:
                    with st.expander(f"{status_icon} {video['title']} - {status_text}", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**ID:** {video['id']}")
                            st.write(f"**Description:** {video['description'][:100]}...")
                            st.write(f"**Genre:** {video['genre']}")
                            st.write(f"**Expected Length:** {video['expected_length']} seconds")
                        
                        with col2:
                            st.write(f"**Status:** {status_icon} {status_text}")
                            st.write(f"**Created:** {video['created_at']}")
                            st.write(f"**Updated:** {video['updated_at']}")
                            st.write(f"**Video Type:** {video['video_type']}")
                            
                            # Status-specific information and actions
                            if status == 'completed':
                                st.success("✅ Video processing completed successfully!")
                                st.info("🎉 Video has been uploaded to YouTube")
                                
                                # Show completion time
                                if 'updated_at' in video and video['updated_at']:
                                    try:
                                        if isinstance(video['updated_at'], str):
                                            completion_time = datetime.fromisoformat(video['updated_at'].replace('Z', '+00:00'))
                                        else:
                                            completion_time = video['updated_at']
                                        st.write(f"**Completed At:** {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
                                    except:
                                        pass
                                
                            elif status == 'failed':
                                st.error("❌ Video processing failed")
                                st.warning("🔍 Check logs for error details")
                                
                                # Automated retry info
                                st.info("🤖 **Automatic Retry System**")
                                st.info("💡 Failed videos will be automatically retried by the system")
                                
                                # Show retry count if available
                                if 'retry_count' in video.get('extra_metadata', {}):
                                    retry_count = video['extra_metadata']['retry_count']
                                    st.write(f"**Retry Attempts:** {retry_count}/3")
                                
                            elif status == 'cancelled':
                                st.warning("⏹️ Video processing was cancelled")
                                st.info("📝 Video can be restarted if needed")
                                
                                # Automated restart info
                                st.info("🤖 **Automatic Restart System**")
                                st.info("💡 Cancelled videos can be automatically restarted by the system")
        else:
            st.info("📭 No completed videos found")
            
    except Exception as e:
        st.error(f"Error getting completed videos: {e}")
    
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
        st.warning("⚠️ Enable real-time monitoring by starting the Automated Processing system")
    
    # Footer
    st.markdown("---")
    st.markdown("*Scheduler Dashboard - Automated Video Generation System*")

def main():
    """Main function for standalone execution"""
    scheduler_dashboard()

if __name__ == "__main__":
    main()
