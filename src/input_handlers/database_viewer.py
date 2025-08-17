# input_handlers/database_viewer.py

import streamlit as st
import sys
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add the src directory to the path to import database modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.db_handler import DB_PATH, delete_all_videos

def view_database():
    st.title("📊 Database Viewer - Saved Videos")
    
    # Initialize session state for database viewer persistence
    if 'db_viewer_last_refresh' not in st.session_state:
        st.session_state.db_viewer_last_refresh = datetime.now()
    
    if 'db_viewer_auto_refresh' not in st.session_state:
        st.session_state.db_viewer_auto_refresh = True
    
    if 'db_viewer_expanded_videos' not in st.session_state:
        st.session_state.db_viewer_expanded_videos = {}
    
    if 'db_viewer_filter_status' not in st.session_state:
        st.session_state.db_viewer_filter_status = "all"
    
    if 'db_viewer_filter_genre' not in st.session_state:
        st.session_state.db_viewer_filter_genre = "all"
    
    # Add delete all button at the top
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💾 View and manage all saved video data in the database")
    with col2:
        if st.button("🗑️ Delete All Records", type="secondary"):
            if st.button("⚠️ Confirm Delete All", key="confirm_delete_all_viewer"):
                try:
                    deleted_count = delete_all_videos()
                    st.success(f"✅ {deleted_count} database records deleted successfully!")
                    
                    # Set session state to trigger UI updates everywhere
                    st.session_state.records_deleted_viewer = True
                    st.session_state.deleted_count_viewer = deleted_count
                    
                    # Clear expanded videos state
                    st.session_state.db_viewer_expanded_videos = {}
                    
                    # Rerun to update all UI components
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to delete all records: {e}")
    
    # Show deletion notification if records were deleted
    if st.session_state.get('records_deleted_viewer', False):
        st.success(f"🎉 Successfully deleted {st.session_state.get('deleted_count_viewer', 0)} records from database!")
        st.info("💡 The UI has been refreshed to reflect the changes. All views will show the updated data.")
        
        # Clear the notification after showing
        del st.session_state.records_deleted_viewer
        del st.session_state.deleted_count_viewer
    
    # Refresh controls
    st.markdown("---")
    refresh_col1, refresh_col2, refresh_col3 = st.columns([2, 2, 1])
    
    with refresh_col1:
        # Auto-refresh toggle
        auto_refresh = st.checkbox(
            "Auto-refresh every 30 seconds", 
            value=st.session_state.db_viewer_auto_refresh,
            key="db_auto_refresh_toggle"
        )
        
        if auto_refresh != st.session_state.db_viewer_auto_refresh:
            st.session_state.db_viewer_auto_refresh = auto_refresh
            st.rerun()
    
    with refresh_col2:
        # Manual refresh button
        if st.button("🔄 Manual Refresh"):
            st.session_state.db_viewer_last_refresh = datetime.now()
            st.rerun()
    
    with refresh_col3:
        st.info(f"Last: {st.session_state.db_viewer_last_refresh.strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all videos
        cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        videos = cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        if not videos:
            st.info("📭 No videos found in the database. Create some videos first!")
            return
        
        st.success(f"✅ Found {len(videos)} videos in the database")
        
        # Display videos in a table
        for i, video in enumerate(videos):
            with st.expander(f"🎬 {video[1] or 'Untitled'} - {video[4] or 'No Genre'}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {video[0]}")
                    st.write(f"**Title:** {video[1] or 'N/A'}")
                    st.write(f"**Description:** {video[2] or 'N/A'}")
                    st.write(f"**Captions:** {video[3] or 'N/A'}")
                    st.write(f"**Tags:** {video[4] or 'N/A'}")
                    st.write(f"**Video URL:** {video[5] or 'N/A'}")
                    st.write(f"**Genre:** {video[6] or 'N/A'}")
                
                with col2:
                    st.write(f"**Expected Length:** {video[7] or 'N/A'} seconds")
                    st.write(f"**Schedule Time:** {video[8] or 'N/A'}")
                    st.write(f"**Platforms:** {video[9] or 'N/A'}")
                    st.write(f"**Video Type:** {video[10] or 'N/A'}")
                    st.write(f"**Music Preference:** {video[11] or 'N/A'}")
                    st.write(f"**Channel Name:** {video[12] or 'N/A'}")
                    st.write(f"**Created At:** {video[14] or 'N/A'}")
                
                # Show extra metadata if available
                if video[13]:  # extra_metadata
                    try:
                        metadata = json.loads(video[13])
                        st.subheader("🔧 Extra Metadata")
                        st.json(metadata)
                    except json.JSONDecodeError:
                        st.write(f"**Raw Metadata:** {video[13]}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"📝 Edit {i}", key=f"edit_{i}"):
                        st.session_state.edit_video_id = video[0]
                        st.rerun()
                
                with col2:
                    if st.button(f"🗑️ Delete {i}", key=f"delete_{i}"):
                        if st.button(f"⚠️ Confirm Delete {i}", key=f"confirm_delete_{i}"):
                            cursor.execute("DELETE FROM videos WHERE id = ?", (video[0],))
                            conn.commit()
                            st.success(f"✅ Video {video[0]} deleted successfully!")
                            st.rerun()
                
                with col3:
                    if st.button(f"📋 Copy JSON {i}", key=f"copy_{i}"):
                        # Create JSON representation
                        video_data = dict(zip(columns, video))
                        st.code(json.dumps(video_data, indent=2, default=str))
        
        # Database statistics
        st.subheader("📈 Database Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cursor.execute("SELECT COUNT(*) FROM videos")
            total_videos = cursor.fetchone()[0]
            st.metric("Total Videos", total_videos)
        
        with col2:
            cursor.execute("SELECT COUNT(DISTINCT genre) FROM videos WHERE genre IS NOT NULL")
            unique_genres = cursor.fetchone()[0]
            st.metric("Unique Genres", unique_genres)
        
        with col3:
            cursor.execute("SELECT AVG(expected_length) FROM videos WHERE expected_length IS NOT NULL")
            avg_length = cursor.fetchone()[0]
            if avg_length:
                st.metric("Avg Length (sec)", f"{avg_length:.1f}")
            else:
                st.metric("Avg Length (sec)", "N/A")
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        st.info("💡 Make sure the database has been initialized first.")

if __name__ == "__main__":
    view_database()
