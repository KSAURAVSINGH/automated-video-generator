"""
File utility functions for the Automated Video Generator.
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import logging
import mimetypes
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """
        Ensure a directory exists, create if it doesn't.
        
        Args:
            path: Directory path
        
        Returns:
            True if successful, False otherwise
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Dictionary with file information
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            file_info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': mimetypes.guess_type(file_path)[0] or 'unknown',
                'extension': Path(file_path).suffix.lower()
            }
            
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    @staticmethod
    def get_directory_contents(directory_path: str, recursive: bool = False,
                            file_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get contents of a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to search recursively
            file_types: List of file extensions to include (e.g., ['.mp4', '.jpg'])
        
        Returns:
            List of file information dictionaries
        """
        try:
            if not os.path.exists(directory_path):
                return []
            
            contents = []
            path_obj = Path(directory_path)
            
            if recursive:
                files = path_obj.rglob('*')
            else:
                files = path_obj.iterdir()
            
            for file_path in files:
                if file_path.is_file():
                    # Filter by file type if specified
                    if file_types and file_path.suffix.lower() not in file_types:
                        continue
                    
                    file_info = FileUtils.get_file_info(str(file_path))
                    if file_info:
                        contents.append(file_info)
            
            return contents
            
        except Exception as e:
            logger.error(f"Failed to get directory contents for {directory_path}: {e}")
            return []
    
    @staticmethod
    def copy_file(source_path: str, destination_path: str, 
                  overwrite: bool = False) -> bool:
        """
        Copy a file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing files
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file does not exist: {source_path}")
                return False
            
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination_path)
            if not FileUtils.ensure_directory(dest_dir):
                return False
            
            # Check if destination exists
            if os.path.exists(destination_path) and not overwrite:
                logger.warning(f"Destination file exists and overwrite is False: {destination_path}")
                return False
            
            shutil.copy2(source_path, destination_path)
            logger.info(f"File copied successfully: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy file {source_path} to {destination_path}: {e}")
            return False
    
    @staticmethod
    def move_file(source_path: str, destination_path: str, 
                  overwrite: bool = False) -> bool:
        """
        Move a file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing files
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file does not exist: {source_path}")
                return False
            
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination_path)
            if not FileUtils.ensure_directory(dest_dir):
                return False
            
            # Check if destination exists
            if os.path.exists(destination_path) and not overwrite:
                logger.warning(f"Destination file exists and overwrite is False: {destination_path}")
                return False
            
            shutil.move(source_path, destination_path)
            logger.info(f"File moved successfully: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file {source_path} to {destination_path}: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return True
            
            os.remove(file_path)
            logger.info(f"File deleted successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    @staticmethod
    def delete_directory(directory_path: str, recursive: bool = True) -> bool:
        """
        Delete a directory.
        
        Args:
            directory_path: Path to the directory to delete
            recursive: Whether to delete recursively
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(directory_path):
                logger.warning(f"Directory does not exist: {directory_path}")
                return True
            
            if recursive:
                shutil.rmtree(directory_path)
            else:
                os.rmdir(directory_path)
            
            logger.info(f"Directory deleted successfully: {directory_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete directory {directory_path}: {e}")
            return False
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm (md5, sha1, sha256)
        
        Returns:
            Hexadecimal hash string if successful, None otherwise
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def get_file_size_formatted(file_path: str) -> str:
        """
        Get file size in human-readable format.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        try:
            if not os.path.exists(file_path):
                return "0 B"
            
            size_bytes = os.path.getsize(file_path)
            
            # Convert to appropriate unit
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            
            return f"{size_bytes:.1f} PB"
            
        except Exception as e:
            logger.error(f"Failed to get file size for {file_path}: {e}")
            return "0 B"
    
    @staticmethod
    def find_files_by_pattern(directory_path: str, pattern: str,
                            recursive: bool = True) -> List[str]:
        """
        Find files matching a pattern.
        
        Args:
            directory_path: Directory to search in
            pattern: File pattern (e.g., "*.mp4", "video_*")
            recursive: Whether to search recursively
        
        Returns:
            List of matching file paths
        """
        try:
            if not os.path.exists(directory_path):
                return []
            
            path_obj = Path(directory_path)
            
            if recursive:
                files = path_obj.rglob(pattern)
            else:
                files = path_obj.glob(pattern)
            
            return [str(f) for f in files if f.is_file()]
            
        except Exception as e:
            logger.error(f"Failed to find files by pattern in {directory_path}: {e}")
            return []
    
    @staticmethod
    def cleanup_temp_files(directory_path: str, max_age_hours: int = 24,
                          file_types: List[str] = None) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            directory_path: Directory to clean up
            max_age_hours: Maximum age of files in hours
            file_types: List of file extensions to clean up
        
        Returns:
            Number of files deleted
        """
        try:
            if not os.path.exists(directory_path):
                return 0
            
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            deleted_count = 0
            
            for file_info in FileUtils.get_directory_contents(directory_path, recursive=True):
                file_path = file_info['path']
                
                # Check file type
                if file_types and file_info['extension'] not in file_types:
                    continue
                
                # Check file age
                file_time = datetime.fromisoformat(file_info['modified']).timestamp()
                if file_time < cutoff_time:
                    if FileUtils.delete_file(file_path):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} temporary files from {directory_path}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files in {directory_path}: {e}")
            return 0
    
    @staticmethod
    def save_json(data: Any, file_path: str, indent: int = 2) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            data: Data to save
            file_path: Path to the JSON file
            indent: JSON indentation
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            dest_dir = os.path.dirname(file_path)
            if dest_dir and not FileUtils.ensure_directory(dest_dir):
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
            
            logger.info(f"JSON data saved successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON data to {file_path}: {e}")
            return False
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Any]:
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to the JSON file
        
        Returns:
            Loaded data if successful, None otherwise
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"JSON data loaded successfully: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load JSON data from {file_path}: {e}")
            return None

# Global file utils instance
file_utils = FileUtils()
