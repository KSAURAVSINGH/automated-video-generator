# 🎬 Automated Video Generator - Complete Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Workflow & Data Flow](#workflow--data-flow)
5. [Installation & Setup](#installation--setup)
6. [How to Use](#how-to-use)
7. [Scheduler System](#scheduler-system)
8. [YouTube Integration](#youtube-integration)
9. [Database Schema](#database-schema)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)
12. [API Reference](#api-reference)

---

## 🎯 Project Overview

The **Automated Video Generator** is a comprehensive system that automates the entire process of video creation, scheduling, and YouTube upload. It's designed to work with minimal human intervention once configured.

### ✨ Key Features
- **Automated Video Scheduling**: Set videos to be processed at specific times
- **Real Video Upload**: Upload existing video files to YouTube
- **Intelligent Workflow**: Automatic task pickup and processing
- **YouTube Integration**: Direct upload to your YouTube channel
- **Database Management**: Persistent storage of video metadata
- **Progress Tracking**: Real-time status updates throughout the process

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │   Database      │    │   Scheduler     │
│   (Streamlit)   │───▶│   (SQLite)      │───▶│   (APScheduler) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │ Workflow        │
         │                       │              │ Controller      │
         │                       │              └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │ YouTube         │
         │                       │              │ Uploader        │
         │                       │              └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │   YouTube       │
         │                       │              │   Platform      │
         │                       │              └─────────────────┘
```

---

## 🔧 Core Components

### 1. **Workflow Controller** (`src/core/workflow_controller.py`)
- **Purpose**: Central orchestrator for the entire video processing pipeline
- **Responsibilities**:
  - Manages video job lifecycle
  - Coordinates between scheduler and uploader
  - Handles error recovery and retries
  - Tracks job progress and status

### 2. **Enhanced Scheduler** (`src/scheduler/enhanced_scheduler.py`)
- **Purpose**: Monitors database for scheduled videos and triggers processing
- **Features**:
  - Database monitoring every 60 seconds
  - Automatic task pickup based on schedule time
  - Concurrent task management (max 3 simultaneous)
  - Integration with workflow controller

### 3. **YouTube Uploader** (`src/uploaders/youtube_uploader.py`)
- **Purpose**: Handles authentication and video upload to YouTube
- **Capabilities**:
  - OAuth 2.0 authentication
  - Progress tracking during upload
  - Metadata management (title, description, tags)
  - Error handling and retry logic

### 4. **Database Handler** (`src/database/db_handler.py`)
- **Purpose**: Manages all database operations
- **Functions**:
  - Video metadata storage
  - Status tracking
  - Query operations
  - Database initialization

---

## 🔄 Workflow & Data Flow

### **Complete Workflow Process**

```
1. User Input → 2. Database Storage → 3. Scheduler Detection → 4. Processing → 5. YouTube Upload → 6. Completion
```

#### **Step-by-Step Breakdown**

1. **User Input** 📝
   - User creates video form via Streamlit UI
   - Specifies title, description, tags, schedule time
   - Option to use existing video or generate new one

2. **Database Storage** 💾
   - Video metadata saved to SQLite database
   - Status set to "pending"
   - Schedule time recorded

3. **Scheduler Detection** ⏰
   - Enhanced Scheduler monitors database every 60 seconds
   - Detects videos with passed schedule time
   - Adds ready videos to processing queue

4. **Processing** 🎬
   - Workflow Controller picks up jobs from queue
   - Processes video based on configuration:
     - Use existing video file
     - Generate mock video
     - Create new video (if enabled)

5. **YouTube Upload** 📤
   - Authenticates with YouTube API
   - Uploads video with metadata
   - Tracks upload progress
   - Stores YouTube video ID

6. **Completion** ✅
   - Status updated to "completed"
   - YouTube upload details stored
   - Job marked as successful

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.8+
- pip package manager
- YouTube API credentials

### **Installation Steps**

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd automated-video-generator
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure YouTube API**
   - Create `credentials.json` with your OAuth credentials
   - Update `src/config/settings.py` with your API keys

5. **Initialize Database**
   ```bash
   python -c "from src.database.db_handler import init_db; init_db()"
   ```

---

## 📖 How to Use

### **Method 1: Simple Scheduled Upload (Recommended)**

```bash
python simple_scheduled_upload.py
```

This script:
- Finds existing videos in temp folder
- Schedules them for 1 minute from now
- Automatically processes and uploads to YouTube

### **Method 2: Upload Specific Video**

```bash
python upload_218309_video.py
```

This script:
- Uploads a specific video file (218309_small.mp4)
- Uses the complete automated workflow
- Provides real-time progress updates

### **Method 3: Streamlit UI**

```bash
streamlit run src/input_handlers/main_app.py --server.port 8502
```

Access the web interface at `http://localhost:8502`

---

## ⏰ Scheduler System

### **How the Scheduler Works**

The **Enhanced Scheduler** is the brain of the automation system:

#### **Core Functions**
1. **Database Monitoring**: Checks database every 60 seconds
2. **Task Detection**: Identifies videos ready for processing
3. **Queue Management**: Adds tasks to processing queue
4. **Concurrency Control**: Limits to 3 simultaneous tasks

#### **Scheduling Logic**
```python
# Scheduler checks for videos where:
schedule_time <= current_time AND status == 'pending'

# Then adds them to processing queue
workflow_controller.processing_queue.append(video_job)
```

#### **Task Lifecycle**
```
Pending → Queued → Processing → Uploading → Completed
   ↓         ↓         ↓          ↓          ↓
Scheduled  Picked   Working   YouTube   Success
   Time     Up      on Video   Upload    Status
```

### **Scheduler Configuration**
- **Check Interval**: 60 seconds
- **Max Concurrent Tasks**: 3
- **Database Monitoring**: Continuous
- **Error Handling**: Automatic retry with exponential backoff

---

## 📺 YouTube Integration

### **Authentication Flow**
1. **OAuth 2.0 Setup**: Uses `credentials.json` file
2. **Token Management**: Automatic refresh and persistence
3. **Scope**: `https://www.googleapis.com/auth/youtube.upload`

### **Upload Process**
1. **Video Validation**: Checks file existence and size
2. **Metadata Preparation**: Title, description, tags, category
3. **Chunked Upload**: 1MB chunks with progress tracking
4. **Response Handling**: Stores YouTube video ID and URL

### **Category Mapping**
```python
genre_to_category = {
    "technology": "28",      # Science & Technology
    "entertainment": "24",   # Entertainment
    "education": "27",       # Education
    "gaming": "20",          # Gaming
    "music": "10",           # Music
    # ... more categories
}
```

---

## 🗄️ Database Schema

### **Main Tables**

#### **videos**
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    captions TEXT,
    tags TEXT,
    video_link TEXT,
    genre TEXT,
    expected_length INTEGER,
    schedule_time TEXT,
    platforms TEXT,
    video_type TEXT,
    music_pref TEXT,
    channel_name TEXT,
    extra_metadata TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### **Key Fields**
- `status`: Video processing status (pending, processing, completed, failed)
- `schedule_time`: When the video should be processed
- `extra_metadata`: JSON string containing workflow configuration
- `updated_at`: Last status update timestamp

---

## ⚙️ Configuration

### **Environment Variables** (`src/config/settings.py`)

```python
# YouTube API Configuration
YOUTUBE_CLIENT_ID = "your_client_id"
YOUTUBW_CLIENT_SECRET = "your_client_secret"
YOUTUBE_API_KEY = "your_api_key"

# Database Configuration
DATABASE_URL = "sqlite:///videos.db"

# Scheduler Configuration
MAX_CONCURRENT_TASKS = 3
SCHEDULER_CHECK_INTERVAL = 60  # seconds
```

### **Workflow Configuration**
```python
extra_metadata = {
    "test_type": "real_video_upload",
    "automated": True,
    "skip_generation": True,           # Skip video generation
    "use_existing_video": True,        # Use existing video file
    "existing_video_path": "path/to/video.mp4",
    "youtube_upload": True             # Enable YouTube upload
}
```

---

## 🔍 Troubleshooting

### **Common Issues & Solutions**

#### **1. YouTube Authentication Error**
```
Error: redirect_uri_mismatch
```
**Solution**: Update redirect URIs in Google Cloud Console:
- `urn:ietf:wg:oauth:2.0:oob`
- `http://localhost`
- `http://localhost:8080`

#### **2. Category ID Error**
```
Error: invalid category ID
```
**Solution**: The system now automatically maps genres to valid YouTube category IDs.

#### **3. Database Connection Issues**
```
Error: Database not initialized
```
**Solution**: Run database initialization:
```bash
python -c "from src.database.db_handler import init_db; init_db()"
```

#### **4. Scheduler Not Working**
```
Error: Scheduler not picking up tasks
```
**Solution**: Check if workflow controller is running and database has pending videos.

### **Debug Mode**
Enable detailed logging by setting log level in `src/config/settings.py`:
```python
LOG_LEVEL = "DEBUG"
```

---

## 📚 API Reference

### **Core Classes**

#### **WorkflowController**
```python
class WorkflowController:
    async def start() -> None           # Start the workflow system
    async def stop() -> None            # Stop the workflow system
    async def _process_job(job: VideoJob) -> None  # Process a single job
    def get_status() -> Dict[str, Any] # Get system status
```

#### **EnhancedScheduler**
```python
class EnhancedScheduler:
    async def start() -> None           # Start database monitoring
    async def stop() -> None            # Stop monitoring
    def get_scheduler_stats() -> Dict[str, Any]  # Get scheduler status
    def get_active_tasks() -> List[Dict] # Get currently processing tasks
```

#### **YouTubeUploader**
```python
class YouTubeUploader:
    async def authenticate() -> bool    # Authenticate with YouTube
    async def upload_video(...) -> Dict[str, Any]  # Upload video
    def get_upload_progress() -> int   # Get upload progress percentage
```

---

## 🎯 Best Practices

### **1. Video Scheduling**
- Schedule videos at least 2-3 minutes in the future
- Avoid scheduling during peak system usage
- Use descriptive titles and tags for better discoverability

### **2. File Management**
- Keep video files in the `temp/` directory
- Use meaningful filenames
- Ensure video files are valid MP4 format

### **3. Error Handling**
- Monitor system logs for errors
- Check YouTube Studio for upload status
- Use the status tracking system to monitor progress

### **4. Performance**
- Limit concurrent uploads to 3
- Use existing videos when possible
- Monitor database performance for large datasets

---

## 🚀 Future Enhancements

### **Planned Features**
1. **Multiple Platform Support**: Instagram, TikTok, LinkedIn
2. **Advanced Scheduling**: Recurring uploads, time zones
3. **Video Templates**: Pre-defined video structures
4. **Analytics Dashboard**: Upload performance metrics
5. **Batch Processing**: Multiple video uploads
6. **API Endpoints**: REST API for external integrations

### **Scalability Improvements**
1. **Database Optimization**: Indexing, query optimization
2. **Async Processing**: Better concurrency handling
3. **Caching Layer**: Redis integration for performance
4. **Load Balancing**: Multiple worker instances

---

## 📞 Support & Maintenance

### **System Monitoring**
- Check scheduler status regularly
- Monitor database size and performance
- Review YouTube API quota usage

### **Regular Maintenance**
- Clean up old video files
- Archive completed video records
- Update YouTube API credentials when needed

### **Troubleshooting Steps**
1. Check system logs
2. Verify database connectivity
3. Test YouTube API authentication
4. Restart workflow controller if needed

---

## 📄 License & Credits

This project is built with:
- **Python 3.8+**: Core programming language
- **SQLite**: Database management
- **APScheduler**: Task scheduling
- **Google API Client**: YouTube integration
- **Streamlit**: Web interface
- **MoviePy**: Video processing (when enabled)

---

*Last Updated: August 2024*
*Version: 1.0.0*
