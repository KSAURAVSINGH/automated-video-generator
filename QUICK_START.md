# 🚀 Quick Start Guide - Automated Video Generator

## ⚡ Get Started in 5 Minutes

### **1. Prerequisites**
- ✅ Python 3.8+ installed
- ✅ YouTube API credentials ready
- ✅ Virtual environment created

### **2. Setup (2 minutes)**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from src.database.db_handler import init_db; init_db()"
```

### **3. Configure YouTube (1 minute)**
- Create `credentials.json` with your OAuth credentials
- Update `src/config/settings.py` with your API keys

### **4. Test Upload (2 minutes)**
```bash
# Upload any video from temp folder
python simple_scheduled_upload.py

# Or upload specific video
python upload_218309_video.py
```

## 🎯 What Happens Next

1. **Video gets scheduled** for 1 minute from now
2. **Scheduler automatically picks up** the task
3. **Video gets uploaded** to YouTube
4. **Check YouTube Studio** for your new video!

## 🔧 Troubleshooting

- **OAuth Error**: Update redirect URIs in Google Cloud Console
- **Database Error**: Run database initialization command
- **Upload Fails**: Check YouTube API quota and credentials

## 📚 Full Documentation

See `PROJECT_DOCUMENTATION.md` for complete details.

---

**🎉 You're ready to automate video uploads!** 🚀
