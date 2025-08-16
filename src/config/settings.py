"""
Configuration and settings for the Automated Video Generator
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = BASE_DIR / "src"
TEMP_DIR = BASE_DIR / "temp"
LOG_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure directories exist
TEMP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///videos.db")
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite or postgresql

# API configurations
STABLE_DIFFUSION_API_URL = os.getenv("STABLE_DIFFUSION_API_URL", "http://localhost:7860")
STABLE_DIFFUSION_API_KEY = os.getenv("STABLE_DIFFUSION_API_KEY", "")

# Pyramid Flow API configuration
PYRAMID_FLOW_API_URL = os.getenv("PYRAMID_FLOW_API_URL", "https://pyramid-flow.hf.space")
PYRAMID_FLOW_API_KEY = os.getenv("PYRAMID_FLOW_API_KEY", "")
PYRAMID_FLOW_ENABLED = os.getenv("PYRAMID_FLOW_ENABLED", "true").lower() == "true"

# YouTube API configuration
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CREDENTIALS_PATH = os.getenv("YOUTUBE_CREDENTIALS_PATH", "credentials.json")

# Google Sheets API configuration
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "google_credentials.json")
GOOGLE_SHEETS_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Video generation settings
DEFAULT_VIDEO_RESOLUTION = (1920, 1080)  # 1080p
DEFAULT_VIDEO_FPS = 24
DEFAULT_VIDEO_BITRATE = "5000k"
DEFAULT_AUDIO_BITRATE = "128k"

# Image generation settings
DEFAULT_IMAGE_WIDTH = 512
DEFAULT_IMAGE_HEIGHT = 512
DEFAULT_IMAGE_STEPS = 20
DEFAULT_IMAGE_CFG_SCALE = 7.0
DEFAULT_IMAGE_SEED = -1  # Random seed

# Scheduler settings
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "UTC")
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "3"))
JOB_CHECK_INTERVAL = int(os.getenv("JOB_CHECK_INTERVAL", "30"))  # seconds

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOG_DIR / "app.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Email notification settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# Notification recipients
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
NOTIFICATION_EMAILS = os.getenv("NOTIFICATION_EMAILS", "").split(",") if os.getenv("NOTIFICATION_EMAILS") else []

# File upload settings
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
ALLOWED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
ALLOWED_AUDIO_FORMATS = ['.mp3', '.wav', '.aac', '.ogg', '.m4a']

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Development settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
TESTING = os.getenv("TESTING", "false").lower() == "true"

# Performance settings
WORKER_PROCESSES = int(os.getenv("WORKER_PROCESSES", "1"))
WORKER_THREADS = int(os.getenv("WORKER_THREADS", "4"))
MAX_MEMORY_USAGE = int(os.getenv("MAX_MEMORY_USAGE", "2048"))  # MB

# Retry settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "60"))  # seconds
RETRY_BACKOFF_MULTIPLIER = float(os.getenv("RETRY_BACKOFF_MULTIPLIER", "2.0"))

# Cleanup settings
TEMP_FILE_RETENTION_HOURS = int(os.getenv("TEMP_FILE_RETENTION_HOURS", "24"))
LOG_FILE_RETENTION_DAYS = int(os.getenv("LOG_FILE_RETENTION_DAYS", "30"))

# Feature flags
ENABLE_IMAGE_GENERATION = os.getenv("ENABLE_IMAGE_GENERATION", "true").lower() == "true"
ENABLE_VIDEO_GENERATION = os.getenv("ENABLE_VIDEO_GENERATION", "true").lower() == "true"
ENABLE_YOUTUBE_UPLOAD = os.getenv("ENABLE_YOUTUBE_UPLOAD", "true").lower() == "true"
ENABLE_EMAIL_NOTIFICATIONS = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"
ENABLE_GOOGLE_SHEETS = os.getenv("ENABLE_GOOGLE_SHEETS", "false").lower() == "true"

# API rate limiting
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "100"))  # requests per hour
API_RATE_LIMIT_WINDOW = int(os.getenv("API_RATE_LIMIT_WINDOW", "3600"))  # seconds

# Monitoring and health check
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))  # seconds
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "false").lower() == "true"

# Default values for video generation
DEFAULT_VIDEO_DURATION = 60  # seconds
DEFAULT_SCENE_COUNT = 5
DEFAULT_SCENE_VARIATIONS = 2
DEFAULT_TRANSITION_DURATION = 1.0  # seconds

# Text-to-speech settings
TTS_ENGINE = os.getenv("TTS_ENGINE", "coqui")  # coqui, gtts, or pyttsx3
TTS_VOICE = os.getenv("TTS_VOICE", "en")
TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0"))

# Video template settings
VIDEO_TEMPLATES_DIR = ASSETS_DIR / "templates"
DEFAULT_TEMPLATE = "standard"

# Output quality settings
VIDEO_QUALITY_PRESETS = {
    "low": {"resolution": (854, 480), "bitrate": "1000k", "fps": 24},
    "medium": {"resolution": (1280, 720), "bitrate": "2500k", "fps": 30},
    "high": {"resolution": (1920, 1080), "bitrate": "5000k", "fps": 30},
    "ultra": {"resolution": (2560, 1440), "bitrate": "8000k", "fps": 60}
}

# Error handling
IGNORE_MINOR_ERRORS = os.getenv("IGNORE_MINOR_ERRORS", "true").lower() == "true"
CONTINUE_ON_FAILURE = os.getenv("CONTINUE_ON_FAILURE", "false").lower() == "true"

# Backup and recovery
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "false").lower() == "true"
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))

# Export settings
EXPORT_FORMATS = ["mp4", "avi", "mov", "gif"]
DEFAULT_EXPORT_FORMAT = "mp4"

# Cache settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "100"))  # items

# Validation settings
VALIDATE_VIDEO_BEFORE_UPLOAD = os.getenv("VALIDATE_VIDEO_BEFORE_UPLOAD", "true").lower() == "true"
VALIDATE_IMAGE_BEFORE_PROCESSING = os.getenv("VALIDATE_IMAGE_BEFORE_PROCESSING", "true").lower() == "true"

# Timeout settings
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "300"))  # seconds
UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", "3600"))  # seconds
GENERATION_TIMEOUT = int(os.getenv("GENERATION_TIMEOUT", "1800"))  # seconds

# Resource limits
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "10"))  # MB
MAX_VIDEO_SIZE = int(os.getenv("MAX_VIDEO_SIZE", "500"))  # MB
MAX_AUDIO_SIZE = int(os.getenv("MAX_AUDIO_SIZE", "50"))  # MB

# Queue settings
QUEUE_MAX_SIZE = int(os.getenv("QUEUE_MAX_SIZE", "1000"))
QUEUE_TIMEOUT = int(os.getenv("QUEUE_TIMEOUT", "300"))  # seconds

# Load balancing
ENABLE_LOAD_BALANCING = os.getenv("ENABLE_LOAD_BALANCING", "false").lower() == "true"
WORKER_NODE_ID = os.getenv("WORKER_NODE_ID", "primary")

# External service endpoints
EXTERNAL_SERVICES = {
    "image_generation": STABLE_DIFFUSION_API_URL,
    "video_processing": "http://localhost:8000",
    "text_to_speech": "http://localhost:8001",
    "analytics": "http://localhost:8002"
}

# Service health check endpoints
HEALTH_CHECK_ENDPOINTS = {
    "image_generation": f"{STABLE_DIFFUSION_API_URL}/health",
    "database": "database://health",
    "scheduler": "scheduler://health"
}

# Default configuration for new videos
DEFAULT_VIDEO_CONFIG = {
    "resolution": DEFAULT_VIDEO_RESOLUTION,
    "fps": DEFAULT_VIDEO_FPS,
    "duration": DEFAULT_VIDEO_DURATION,
    "scene_count": DEFAULT_SCENE_COUNT,
    "scene_variations": DEFAULT_SCENE_VARIATIONS,
    "transition_duration": DEFAULT_TRANSITION_DURATION,
    "quality": "medium",
    "format": DEFAULT_EXPORT_FORMAT
}

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    DEBUG = False
    LOG_LEVEL = "WARNING"
    MAX_CONCURRENT_JOBS = 5
    WORKER_PROCESSES = 2
    WORKER_THREADS = 8
    ENABLE_LOAD_BALANCING = True
elif os.getenv("ENVIRONMENT") == "development":
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    MAX_CONCURRENT_JOBS = 1
    WORKER_PROCESSES = 1
    WORKER_THREADS = 2
elif os.getenv("ENVIRONMENT") == "testing":
    TESTING = True
    DEBUG = False
    LOG_LEVEL = "DEBUG"
    TEMP_DIR = BASE_DIR / "test_temp"
    LOG_DIR = BASE_DIR / "test_logs"
    DATABASE_URL = "sqlite:///test_videos.db"

# Ensure test directories exist
if TESTING:
    TEMP_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
