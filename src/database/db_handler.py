import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# Database configuration
DB_PATH = "videos.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create videos table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        captions TEXT,
        tags TEXT,
        video_url TEXT,
        genre TEXT,
        expected_length INTEGER,
        schedule_time TEXT,
        platforms TEXT,
        video_type TEXT,
        music_pref TEXT,
        channel_name TEXT,
        extra_metadata TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def save_video(data: dict):
    """Save form data into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO videos (
        title, description, captions, tags, video_url, genre,
        expected_length, schedule_time, platforms, video_type,
        music_pref, channel_name, extra_metadata
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("title"),
        data.get("description"),
        data.get("captions"),
        ",".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else data.get("tags"),
        data.get("video_link"),
        data.get("genre"),
        data.get("expected_length"),
        data.get("schedule_time"),
        ",".join(data.get("platforms", [])) if isinstance(data.get("platforms"), list) else data.get("platforms"),
        data.get("video_type"),
        data.get("music_pref"),
        data.get("channel_name"),
        json.dumps(data.get("extra_metadata", {}))
    ))
    conn.commit()
    conn.close()

def get_pending_videos():
    """Get all pending videos from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, title, description, genre, expected_length, schedule_time, 
           platforms, video_type, music_pref, channel_name, extra_metadata, status
    FROM videos 
    WHERE status IN ('pending', 'image_generation', 'video_assembly', 'uploading')
    ORDER BY schedule_time ASC
    """)
    
    columns = [description[0] for description in cursor.description]
    videos = []
    
    for row in cursor.fetchall():
        video_dict = dict(zip(columns, row))
        videos.append(video_dict)
    
    conn.close()
    return videos

def update_video_status(video_id: int, status: str):
    """Update the status of a video."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE videos 
    SET status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (status, video_id))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated video {video_id} status to: {status}")

def get_video_by_id(video_id: int):
    """Get a specific video by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, title, description, genre, expected_length, schedule_time, 
           platforms, video_type, music_pref, channel_name, extra_metadata, status
    FROM videos 
    WHERE id = ?
    """, (video_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = ['id', 'title', 'description', 'genre', 'expected_length', 'schedule_time', 
                  'platforms', 'video_type', 'music_pref', 'channel_name', 'extra_metadata', 'status']
        return dict(zip(columns, row))
    
    return None

def get_all_videos():
    """Get all videos from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, title, description, genre, expected_length, schedule_time, 
           platforms, video_type, music_pref, channel_name, extra_metadata, status,
           created_at, updated_at
    FROM videos 
    ORDER BY created_at DESC
    """)
    
    columns = [description[0] for description in cursor.description]
    videos = []
    
    for row in cursor.fetchall():
        video_dict = dict(zip(columns, row))
        videos.append(video_dict)
    
    conn.close()
    return videos

def delete_video(video_id: int):
    """Delete a video from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        print(f"✅ Deleted video {video_id}")
        return True
    else:
        conn.close()
        print(f"❌ Video {video_id} not found")
        return False

def update_video(video_id: int, data: dict):
    """Update video data in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build dynamic UPDATE query
    update_fields = []
    values = []
    
    for key, value in data.items():
        if key in ['title', 'description', 'genre', 'expected_length', 'schedule_time', 
                   'platforms', 'video_type', 'music_pref', 'channel_name', 'extra_metadata']:
            update_fields.append(f"{key} = ?")
            if key in ['tags', 'platforms'] and isinstance(value, list):
                values.append(",".join(value))
            elif key == 'extra_metadata':
                values.append(json.dumps(value))
            else:
                values.append(value)
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(video_id)
        
        query = f"UPDATE videos SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        print(f"✅ Updated video {video_id}")
        return True
    else:
        conn.close()
        print(f"❌ No valid fields to update for video {video_id}")
        return False

def get_scheduled_videos():
    """Get all videos that are scheduled for processing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, title, description, genre, expected_length, schedule_time, 
           platforms, video_type, music_pref, channel_name, extra_metadata, status,
           created_at, updated_at
    FROM videos 
    WHERE status = 'pending' 
    AND schedule_time IS NOT NULL 
    AND schedule_time <= datetime('now', '+1 hour')
    ORDER BY schedule_time ASC
    """)
    
    columns = [description[0] for description in cursor.description]
    videos = []
    
    for row in cursor.fetchall():
        video_dict = dict(zip(columns, row))
        # Parse schedule_time string to datetime
        if video_dict['schedule_time']:
            try:
                video_dict['schedule_time'] = datetime.fromisoformat(video_dict['schedule_time'])
            except:
                video_dict['schedule_time'] = None
        videos.append(video_dict)
    
    conn.close()
    return videos

def get_videos_ready_for_processing():
    """Get videos that are ready to be processed (scheduled time has passed)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, title, description, genre, expected_length, schedule_time, 
           platforms, video_type, music_pref, channel_name, extra_metadata, status,
           created_at, updated_at
    FROM videos 
    WHERE status = 'pending' 
    AND schedule_time IS NOT NULL 
    AND schedule_time <= datetime('now')
    ORDER BY schedule_time ASC
    """)
    
    columns = [description[0] for description in cursor.description]
    videos = []
    
    for row in cursor.fetchall():
        video_dict = dict(zip(columns, row))
        # Parse schedule_time string to datetime
        if video_dict['schedule_time']:
            try:
                video_dict['schedule_time'] = datetime.fromisoformat(video_dict['schedule_time'])
            except:
                video_dict['schedule_time'] = None
        videos.append(video_dict)
    
    conn.close()
    return videos

def get_video_processing_stats():
    """Get statistics about video processing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        status,
        COUNT(*) as count
    FROM videos 
    GROUP BY status
    """)
    
    stats = {}
    for row in cursor.fetchall():
        status, count = row
        stats[status] = count
    
    conn.close()
    return stats
