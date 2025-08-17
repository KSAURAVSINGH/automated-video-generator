"""Environment Configuration Manager"""
import os
import json
from pathlib import Path
from typing import Optional

class EnvironmentConfig:
    def __init__(self, credentials_file: str = "credentials.json", config_file: str = "config.env"):
        self.credentials_file = credentials_file
        self.config_file = config_file
        self.credentials_loaded = False
        self.config_loaded = False
        self._load_credentials()
        self._load_config()
    
    def _load_credentials(self):
        """Load API keys and credentials from credentials.json"""
        try:
            credentials_path = Path(self.credentials_file)
            if credentials_path.exists():
                with open(credentials_path, 'r') as f:
                    credentials = json.load(f)
                
                # Set environment variables from credentials
                if credentials.get('gemini_api_key'):
                    os.environ['GEMINI_API_KEY'] = credentials['gemini_api_key']
                
                if credentials.get('youtube_api_key'):
                    os.environ['YOUTUBE_API_KEY'] = credentials['youtube_api_key']
                
                if credentials.get('youtube_client_id'):
                    os.environ['YOUTUBE_CLIENT_ID'] = credentials['youtube_client_id']
                
                if credentials.get('youtube_client_secret'):
                    os.environ['YOUTUBE_CLIENT_SECRET'] = credentials['youtube_client_secret']
                
                if credentials.get('youtube_redirect_uri'):
                    os.environ['YOUTUBE_REDIRECT_URI'] = credentials['youtube_redirect_uri']
                
                self.credentials_loaded = True
                print(f"✅ Credentials loaded from {self.credentials_file}")
            else:
                print(f"⚠️ Credentials file {self.credentials_file} not found")
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
    
    def _load_config(self):
        """Load additional configuration from config.env"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                
                self.config_loaded = True
                print(f"✅ Configuration loaded from {self.config_file}")
            else:
                print(f"⚠️ Configuration file {self.config_file} not found")
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
    
    def get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from environment variables"""
        return os.environ.get('GEMINI_API_KEY')
    
    def get_youtube_api_key(self) -> Optional[str]:
        """Get YouTube API key from environment variables"""
        return os.environ.get('YOUTUBE_API_KEY')
    
    def get_youtube_client_id(self) -> Optional[str]:
        """Get YouTube client ID from environment variables"""
        return os.environ.get('YOUTUBE_CLIENT_ID')
    
    def get_youtube_client_secret(self) -> Optional[str]:
        """Get YouTube client secret from environment variables"""
        return os.environ.get('YOUTUBE_CLIENT_SECRET')
    
    def get_youtube_redirect_uri(self) -> Optional[str]:
        """Get YouTube redirect URI from environment variables"""
        return os.environ.get('YOUTUBE_REDIRECT_URI')
    
    def reload_credentials(self):
        """Reload credentials from file"""
        self._load_credentials()
    
    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()

# Global instance
env_config = EnvironmentConfig()
