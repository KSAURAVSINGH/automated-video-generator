"""
Text-to-Speech integration using Coqui TTS for video generation.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from TTS.api import TTS
import torch

from ..config.settings import TTS_MODEL, TEMP_DIR
from ..database.db_init import get_db
from ..database.crud import GenerationLogCRUD

logger = logging.getLogger(__name__)

class TextToSpeechEngine:
    """Text-to-Speech engine using Coqui TTS."""
    
    def __init__(self):
        self.tts = None
        self.model_name = TTS_MODEL
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize the TTS engine."""
        try:
            # Check if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            # Initialize TTS with the specified model
            self.tts = TTS(model_name=self.model_name, progress_bar=False)
            
            # Move to appropriate device
            if device == "cuda":
                self.tts.cuda()
            
            logger.info(f"TTS engine initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
    
    def generate_speech(self, text: str, output_path: Optional[str] = None, 
                       voice: Optional[str] = None, speed: float = 1.0) -> str:
        """
        Generate speech from text.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file (optional)
            voice: Voice to use (optional, depends on model)
            speed: Speech speed multiplier (default: 1.0)
        
        Returns:
            Path to the generated audio file
        """
        try:
            if not self.tts:
                raise RuntimeError("TTS engine not initialized")
            
            # Generate output path if not provided
            if not output_path:
                output_path = self._generate_output_path()
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Generate speech
            logger.info(f"Generating speech for text: {text[:50]}...")
            
            # TTS generation with parameters
            self.tts.tts_to_file(
                text=text,
                file_path=output_path,
                voice=voice,
                speed=speed
            )
            
            logger.info(f"Speech generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            raise
    
    def _generate_output_path(self) -> str:
        """Generate a unique output path for the audio file."""
        timestamp = int(os.timestamp())
        filename = f"speech_{timestamp}.wav"
        return str(TEMP_DIR / filename)
    
    def get_available_voices(self) -> list:
        """Get list of available voices for the current model."""
        try:
            if self.tts:
                return self.tts.voices
            return []
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current TTS model."""
        try:
            if self.tts:
                return {
                    'model_name': self.model_name,
                    'available_voices': self.get_available_voices(),
                    'device': 'cuda' if torch.cuda.is_available() else 'cpu',
                    'model_path': self.tts.model_path
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}
    
    def cleanup(self):
        """Clean up TTS resources."""
        try:
            if self.tts:
                del self.tts
                self.tts = None
            logger.info("TTS engine cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup TTS engine: {e}")

class TTSManager:
    """Manager for TTS operations with database logging."""
    
    def __init__(self):
        self.tts_engine = TextToSpeechEngine()
    
    def generate_speech_with_logging(self, video_id: int, text: str, 
                                   output_path: Optional[str] = None,
                                   voice: Optional[str] = None, 
                                   speed: float = 1.0) -> str:
        """
        Generate speech with database logging.
        
        Args:
            video_id: ID of the video being generated
            text: Text to convert to speech
            output_path: Path to save the audio file
            voice: Voice to use
            speed: Speech speed
        
        Returns:
            Path to the generated audio file
        """
        log_id = None
        
        try:
            # Create generation log entry
            with get_db() as db:
                log_entry = GenerationLogCRUD.create(db, 
                    video_id=video_id,
                    step='text_to_speech',
                    status='processing'
                )
                log_id = log_entry.id
            
            # Generate speech
            audio_path = self.tts_engine.generate_speech(
                text=text,
                output_path=output_path,
                voice=voice,
                speed=speed
            )
            
            # Update log entry to completed
            with get_db() as db:
                GenerationLogCRUD.update_status(
                    db, log_id, 'completed', 
                    meta_data=f'{{"output_path": "{audio_path}", "voice": "{voice}", "speed": {speed}}}'
                )
            
            logger.info(f"TTS generation completed for video {video_id}: {audio_path}")
            return audio_path
            
        except Exception as e:
            # Update log entry to failed
            if log_id:
                try:
                    with get_db() as db:
                        GenerationLogCRUD.update_status(
                            db, log_id, 'failed', 
                            error_message=str(e)
                        )
                except Exception as log_error:
                    logger.error(f"Failed to update log entry: {log_error}")
            
            logger.error(f"TTS generation failed for video {video_id}: {e}")
            raise
    
    def batch_generate_speech(self, video_id: int, text_segments: list,
                             voice: Optional[str] = None, speed: float = 1.0) -> list:
        """
        Generate speech for multiple text segments.
        
        Args:
            video_id: ID of the video
            text_segments: List of text segments to convert
            voice: Voice to use
            speed: Speech speed
        
        Returns:
            List of paths to generated audio files
        """
        audio_files = []
        
        try:
            for i, text in enumerate(text_segments):
                output_path = self._generate_segment_path(video_id, i)
                
                audio_path = self.generate_speech_with_logging(
                    video_id=video_id,
                    text=text,
                    output_path=output_path,
                    voice=voice,
                    speed=speed
                )
                
                audio_files.append(audio_path)
                
            logger.info(f"Batch TTS generation completed for video {video_id}: {len(audio_files)} files")
            return audio_files
            
        except Exception as e:
            logger.error(f"Batch TTS generation failed for video {video_id}: {e}")
            raise
    
    def _generate_segment_path(self, video_id: int, segment_index: int) -> str:
        """Generate path for a text segment audio file."""
        timestamp = int(os.timestamp())
        filename = f"video_{video_id}_segment_{segment_index}_{timestamp}.wav"
        return str(TEMP_DIR / filename)
    
    def cleanup(self):
        """Clean up TTS manager resources."""
        self.tts_engine.cleanup()

# Global TTS manager instance
tts_manager = TTSManager()
