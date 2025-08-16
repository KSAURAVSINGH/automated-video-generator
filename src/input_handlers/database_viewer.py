# input_handlers/database_viewer.py

import streamlit as st
import sys
import os
import sqlite3
import json
from pathlib import Path

# Add the src directory to the path to import database modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.db_handler import DB_PATH

def view_database():
    st.title("📊 Database Viewer - Saved Videos")
    
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
