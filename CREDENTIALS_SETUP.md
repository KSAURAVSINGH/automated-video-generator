# 🔐 Credentials Setup Guide

## Overview
This guide explains how to securely set up API keys and credentials for the automated video generation system.

## 🚨 **IMPORTANT: Security First!**

### ❌ **Never Do This:**
- Commit API keys to version control
- Share credentials in public repositories
- Hardcode keys in source code
- Include keys in documentation

### ✅ **Always Do This:**
- Use `credentials.json` for sensitive data
- Keep `credentials.json` in `.gitignore`
- Use `credentials.json.example` as a template
- Rotate API keys regularly

## 📁 **File Structure**

```
automated-video-generator/
├── credentials.json          # 🔒 YOUR ACTUAL KEYS (ignored by git)
├── credentials.json.example  # 📋 TEMPLATE (safe to commit)
├── config.env               # ⚙️ Non-sensitive configuration
├── .gitignore              # 🛡️ Git exclusion rules
└── src/
    └── config/
        └── env_config.py   # 🔧 Configuration loader
```

## 🔑 **Required API Keys**

### 1. **Google Gemini API Key**
- **Purpose**: AI-powered text improvement
- **Get it from**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Format**: `AIzaSy...` (39 characters)

### 2. **YouTube API Credentials** (Optional)
- **Purpose**: Enhanced YouTube integration
- **Get it from**: [Google Cloud Console](https://console.cloud.google.com/)
- **Files needed**: `credentials.json` for OAuth2

## 🚀 **Quick Setup**

### Step 1: Copy Template
```bash
cp credentials.json.example credentials.json
```

### Step 2: Edit Credentials
```bash
nano credentials.json  # or use your preferred editor
```

### Step 3: Add Your Keys
```json
{
  "gemini_api_key": "AIzaSyYourActualKeyHere",
  "youtube_api_key": "your_youtube_api_key_here",
  "youtube_client_id": "your_client_id_here",
  "youtube_client_secret": "your_client_secret_here",
  "youtube_redirect_uri": "your_redirect_uri_here"
}
```

### Step 4: Verify Setup
```bash
python -c "from src.config.env_config import env_config; print('✅ Credentials loaded:', env_config.credentials_loaded)"
```

## 🔧 **Advanced Configuration**

### Environment Variables
The system automatically sets these environment variables:
```bash
export GEMINI_API_KEY="your_key_here"
export YOUTUBE_API_KEY="your_key_here"
export YOUTUBE_CLIENT_ID="your_client_id"
export YOUTUBE_CLIENT_SECRET="your_secret"
export YOUTUBE_REDIRECT_URI="your_uri"
```

### Custom Credentials Path
```python
from src.config.env_config import EnvironmentConfig

# Load from custom location
config = EnvironmentConfig(
    credentials_file="path/to/your/credentials.json",
    config_file="path/to/your/config.env"
)
```

## 🧪 **Testing Your Setup**

### Test Script
```bash
python test_environment_config.py
```

### Expected Output
```
✅ Credentials loaded from credentials.json
✅ Configuration loaded from config.env
✅ Gemini API key: AIzaSy... (first 10 chars)
✅ YouTube API key: your_key... (first 10 chars)
```

## 🔒 **Security Best Practices**

### 1. **File Permissions**
```bash
chmod 600 credentials.json  # Owner read/write only
```

### 2. **Environment Separation**
```bash
# Development
cp credentials.json.example credentials-dev.json

# Production  
cp credentials.json.example credentials-prod.json

# Staging
cp credentials.json.example credentials-staging.json
```

### 3. **Key Rotation**
- Rotate API keys every 90 days
- Use different keys for different environments
- Monitor API usage for suspicious activity

### 4. **Access Control**
- Limit who has access to credentials files
- Use environment variables in production
- Consider using a secrets management service

## 🚨 **Troubleshooting**

### Common Issues

#### 1. **"Credentials file not found"**
```bash
# Check if file exists
ls -la credentials.json

# Copy template if missing
cp credentials.json.example credentials.json
```

#### 2. **"API key not found"**
```bash
# Check credentials file format
cat credentials.json | python -m json.tool

# Verify key is not empty
grep -v '""' credentials.json
```

#### 3. **"Permission denied"**
```bash
# Fix file permissions
chmod 600 credentials.json
chown $USER:$USER credentials.json
```

#### 4. **"Invalid API key format"**
- Gemini API keys should be 39 characters
- Start with `AIzaSy`
- No spaces or special characters

## 📚 **Additional Resources**

### Documentation
- [Google AI Studio](https://makersuite.google.com/app/apikey)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Google Cloud Console](https://console.cloud.google.com/)

### Support
- Check the logs in `logs/` directory
- Run test scripts to verify configuration
- Review error messages for specific issues

## 🎯 **Next Steps**

1. **✅ Set up credentials** using this guide
2. **🧪 Test your configuration** with test scripts
3. **🚀 Start the application** and verify functionality
4. **🔒 Review security** and access controls
5. **📈 Monitor usage** and rotate keys regularly

## 🎉 **You're All Set!**

With proper credentials setup, your automated video generation system will:
- ✅ **Automatically load API keys** on startup
- ✅ **Provide AI-powered text improvement** via Gemini
- ✅ **Enable enhanced YouTube integration** (if configured)
- ✅ **Maintain security** with no exposed credentials
- ✅ **Support team collaboration** with template files

**Happy video generating! 🎬✨**
