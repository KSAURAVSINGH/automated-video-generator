"""
Google Sheets integration for content ingestion.
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

from ..config.settings import GOOGLE_SHEETS_CREDENTIALS_FILE
from ..database.db_init import get_db
from ..database.crud import ContentSourceCRUD
from ..database.models import ContentSource

logger = logging.getLogger(__name__)

class GoogleSheetsHandler:
    """Handles Google Sheets integration for content ingestion."""
    
    def __init__(self):
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            if not GOOGLE_SHEETS_CREDENTIALS_FILE:
                raise ValueError("Google Sheets credentials file not configured")
            
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Authenticate
            credentials = Credentials.from_service_account_file(
                GOOGLE_SHEETS_CREDENTIALS_FILE, 
                scopes=scope
            )
            
            self.client = gspread.authorize(credentials)
            logger.info("Google Sheets authentication successful")
            
        except Exception as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            raise
    
    def get_spreadsheet_data(self, spreadsheet_id: str, worksheet_name: str = None) -> List[Dict[str, Any]]:
        """
        Get data from a Google Spreadsheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            worksheet_name: Name of the worksheet (defaults to first sheet)
        
        Returns:
            List of dictionaries representing rows
        """
        try:
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Get the worksheet
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(0)
            
            # Get all values
            all_values = worksheet.get_all_records()
            
            logger.info(f"Retrieved {len(all_values)} rows from Google Sheets")
            return all_values
            
        except Exception as e:
            logger.error(f"Failed to get spreadsheet data: {e}")
            raise
    
    def get_content_for_video(self, spreadsheet_id: str, worksheet_name: str = None) -> Dict[str, Any]:
        """
        Get content specifically formatted for video generation.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            worksheet_name: Name of the worksheet
        
        Returns:
            Dictionary with video content structure
        """
        try:
            raw_data = self.get_spreadsheet_data(spreadsheet_id, worksheet_name)
            
            if not raw_data:
                return {}
            
            # Assume first row contains headers
            headers = list(raw_data[0].keys()) if raw_data else []
            
            # Look for common content fields
            content_fields = {
                'title': self._find_field(headers, ['title', 'video_title', 'name']),
                'description': self._find_field(headers, ['description', 'desc', 'content']),
                'script': self._find_field(headers, ['script', 'text', 'transcript']),
                'keywords': self._find_field(headers, ['keywords', 'tags', 'hashtags']),
                'duration': self._find_field(headers, ['duration', 'length', 'time']),
                'style': self._find_field(headers, ['style', 'theme', 'mood']),
                'background_music': self._find_field(headers, ['music', 'background_music', 'audio']),
                'images': self._find_field(headers, ['images', 'image_urls', 'visuals'])
            }
            
            # Build content structure
            video_content = {}
            for key, field_name in content_fields.items():
                if field_name and raw_data[0].get(field_name):
                    video_content[key] = raw_data[0][field_name]
            
            # Add metadata
            video_content['source'] = 'google_sheets'
            video_content['spreadsheet_id'] = spreadsheet_id
            video_content['worksheet'] = worksheet_name or 'Sheet1'
            video_content['retrieved_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Processed video content from Google Sheets: {video_content.get('title', 'Untitled')}")
            return video_content
            
        except Exception as e:
            logger.error(f"Failed to get content for video: {e}")
            raise
    
    def _find_field(self, headers: List[str], possible_names: List[str]) -> Optional[str]:
        """Find a field name from possible variations."""
        for name in possible_names:
            if name in headers:
                return name
        return None
    
    def update_content_source(self, name: str, spreadsheet_id: str, 
                            worksheet_name: str = None, config: Dict[str, Any] = None):
        """Update or create a content source record."""
        try:
            with get_db() as db:
                # Check if source already exists
                existing_sources = db.query(ContentSource).filter(
                    ContentSource.name == name
                ).all()
                
                if existing_sources:
                    # Update existing source
                    source = existing_sources[0]
                    source.config = json.dumps({
                        'spreadsheet_id': spreadsheet_id,
                        'worksheet_name': worksheet_name,
                        **(config or {})
                    })
                    source.updated_at = datetime.utcnow()
                else:
                    # Create new source
                    ContentSourceCRUD.create(db, 
                        name=name,
                        source_type='google_sheets',
                        config=json.dumps({
                            'spreadsheet_id': spreadsheet_id,
                            'worksheet_name': worksheet_name,
                            **(config or {})
                        })
                    )
                
                logger.info(f"Content source updated: {name}")
                
        except Exception as e:
            logger.error(f"Failed to update content source: {e}")
            raise
    
    def test_connection(self, spreadsheet_id: str) -> bool:
        """Test if we can access a specific spreadsheet."""
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.get_worksheet(0)
            worksheet.get_all_values()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_available_worksheets(self, spreadsheet_id: str) -> List[str]:
        """Get list of available worksheets in a spreadsheet."""
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheets = spreadsheet.worksheets()
            return [ws.title for ws in worksheets]
        except Exception as e:
            logger.error(f"Failed to get worksheets: {e}")
            return []
