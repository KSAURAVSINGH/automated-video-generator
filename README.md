# 🎬 Automated Video Generator

> **Automate your video uploads to YouTube with intelligent scheduling and workflow management**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](https://github.com/yourusername/automated-video-generator)

## 🚀 Quick Start

**Get started in 5 minutes!** See [QUICK_START.md](QUICK_START.md) for immediate setup instructions.

## ✨ Features

- **🎯 Automated Scheduling**: Set videos to be processed at specific times
- **📤 Real YouTube Upload**: Direct upload to your YouTube channel
- **🔄 Intelligent Workflow**: Automatic task pickup and processing
- **💾 Database Management**: Persistent storage of video metadata
- **📊 Progress Tracking**: Real-time status updates throughout the process
- **⚡ Minimal Setup**: Configure once, automate forever

## 🏗️ Architecture

```
User Input → Database → Scheduler → Workflow Controller → YouTube Uploader → YouTube
```

## 📋 Requirements

- Python 3.8+
- YouTube API credentials (OAuth 2.0)
- Virtual environment

## 🔧 Installation

1. **Clone & Setup**
   ```bash
   git clone <repository-url>
   cd automated-video-generator
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure YouTube API**
   - Create `credentials.json` with your OAuth credentials
   - Update `src/config/settings.py` with your API keys

3. **Initialize Database**
   ```bash
   python -c "from src.database.db_handler import init_db; init_db()"
   ```

## 🎯 Usage

### **Method 1: Simple Scheduled Upload (Recommended)**
```bash
python simple_scheduled_upload.py
```
- Finds existing videos in temp folder
- Schedules them for 1 minute from now
- Automatically processes and uploads to YouTube

### **Method 2: Upload Specific Video**
```bash
python upload_218309_video.py
```
- Uploads a specific video file
- Uses the complete automated workflow
- Provides real-time progress updates

### **Method 3: Streamlit UI**
```bash
streamlit run src/input_handlers/main_app.py --server.port 8502
```
- Web interface for video management
- Access at `http://localhost:8502`

## 🔄 How It Works

1. **📝 User Input**: Create video form with title, description, tags, schedule time
2. **💾 Database Storage**: Save metadata to SQLite database
3. **⏰ Scheduler Detection**: Monitor database every 60 seconds for ready videos
4. **🎬 Processing**: Workflow controller processes videos automatically
5. **📤 YouTube Upload**: Authenticate and upload with progress tracking
6. **✅ Completion**: Mark as completed and store YouTube video ID

## 📁 Project Structure

```
automated-video-generator/
├── 📚 PROJECT_DOCUMENTATION.md    # Complete system documentation
├── 🚀 QUICK_START.md              # 5-minute setup guide
├── 📦 requirements.txt             # Python dependencies
├── 🎬 simple_scheduled_upload.py  # Main upload script
├── 🎥 upload_218309_video.py      # Specific video upload
├── 📁 src/                        # Source code
│   ├── 🔧 config/                 # Configuration & settings
│   ├── 💾 database/               # Database operations
│   ├── ⏰ scheduler/               # Task scheduling
│   ├── 🎬 core/                   # Workflow controller
│   ├── 📤 uploaders/              # YouTube integration
│   └── 🖥️ input_handlers/         # User interface
├── 📁 temp/                       # Video files directory
└── 🗄️ videos.db                  # SQLite database
```

## 🔑 Configuration

### **YouTube API Setup**
```python
# src/config/settings.py
YOUTUBE_CLIENT_ID = "your_client_id"
YOUTUBE_CLIENT_SECRET = "your_client_secret"
YOUTUBE_API_KEY = "your_api_key"
```

### **Workflow Configuration**
```python
extra_metadata = {
    "skip_generation": True,           # Use existing video
    "use_existing_video": True,        # Specify video path
    "existing_video_path": "temp/video.mp4",
    "youtube_upload": True             # Enable upload
}
```

## 📊 Database Schema

### **videos Table**
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT,
    genre TEXT,
    schedule_time TEXT,
    status TEXT DEFAULT 'pending',
    extra_metadata TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 🚨 Troubleshooting

### **Common Issues**

1. **OAuth Error**: Update redirect URIs in Google Cloud Console
2. **Database Error**: Run database initialization command
3. **Upload Fails**: Check YouTube API quota and credentials

### **Debug Mode**
```python
# src/config/settings.py
LOG_LEVEL = "DEBUG"
```

## 📚 Documentation

- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)**: Complete system documentation
- **[QUICK_START.md](QUICK_START.md)**: 5-minute setup guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **YouTube Data API v3**: For video upload capabilities
- **APScheduler**: For intelligent task scheduling
- **SQLite**: For lightweight database management
- **Streamlit**: For the web interface

---

## 🎉 What's Next?

Your system is now **production-ready** with:
- ✅ **Automated video scheduling**
- ✅ **Real YouTube uploads**
- ✅ **Complete workflow automation**
- ✅ **Progress tracking**
- ✅ **Error handling**

**Start automating your video uploads today!** 🚀

---

*Last Updated: August 2024* | *Version: 1.0.0*
