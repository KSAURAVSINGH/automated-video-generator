"""
Working Local Video Generator
Uses available models for text-to-video generation
"""

import os
import logging
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video
import numpy as np

from src.config.settings import TEMP_DIR

logger = logging.getLogger(__name__)

@dataclass
class VideoParams:
    """Parameters for video generation"""
    prompt: str
    negative_prompt: str = ""
    num_frames: int = 16
    fps: int = 8
    width: int = 512
    height: int = 512
    num_steps: int = 50
    guidance_scale: float = 7.5
    seed: int = -1

class WorkingVideoGenerator:
    """
    Working local text-to-video generation
    """
    
    def __init__(self):
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False
        self.model_id = None
        
        # Available models (in order of preference)
        self.available_models = [
            "damo-vilab/text-to-video-ms-1.7b",
            "cerspense/zeroscope_v2_XL",
            "stabilityai/stable-video-diffusion-img2vid-xt",
            "runwayml/stable-video-diffusion-img2vid-xt-1-1"
        ]
        
        # Default parameters
        self.default_params = VideoParams(
            prompt="",
            negative_prompt="low quality, blurry, distorted, ugly, bad anatomy",
            num_frames=16,
            fps=8,
            width=512,
            height=512,
            num_steps=50,
            guidance_scale=7.5,
            seed=-1
        )
        
        # Ensure temp directory exists
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🎬 Working Video Generator initialized for device: {self.device}")
    
    async def find_working_model(self) -> Optional[str]:
        """Find a working model from the available list"""
        logger.info("🔍 Searching for working text-to-video model...")
        
        for model_id in self.available_models:
            try:
                logger.info(f"   Testing model: {model_id}")
                
                # Try to load the model
                pipeline = DiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32,  # Use float32 for CPU compatibility
                    cache_dir="./models"  # Cache models locally
                )
                
                # Test if we can access the model
                if hasattr(pipeline, 'scheduler'):
                    logger.info(f"✅ Found working model: {model_id}")
                    return model_id
                    
            except Exception as e:
                logger.warning(f"   ❌ Model {model_id} failed: {e}")
                continue
        
        logger.error("❌ No working models found")
        return None
    
    async def load_model(self, model_id: str = None) -> bool:
        """
        Load a text-to-video model
        
        Args:
            model_id: Specific model to load (optional)
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if model_id is None:
                model_id = await self.find_working_model()
                if model_id is None:
                    return False
            
            self.model_id = model_id
            logger.info(f"📦 Loading model: {self.model_id}")
            
            # Load the pipeline
            self.pipeline = DiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float32,  # Use float32 for CPU compatibility
                cache_dir="./models"  # Cache models locally
            )
            
            # Move to device
            self.pipeline = self.pipeline.to(self.device)
            
            # Set scheduler
            if hasattr(self.pipeline, 'scheduler'):
                self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                    self.pipeline.scheduler.config
                )
            
            # Enable memory efficient features if available
            if hasattr(self.pipeline, 'enable_attention_slicing'):
                self.pipeline.enable_attention_slicing()
            
            if hasattr(self.pipeline, 'enable_vae_slicing'):
                self.pipeline.enable_vae_slicing()
            
            self.is_loaded = True
            logger.info("✅ Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False
    
    async def generate_video(self, 
                            video_id: int,
                            prompt: str,
                            params: Optional[VideoParams] = None,
                            output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate video from text prompt
        
        Args:
            video_id: Unique video identifier
            prompt: Text description for video generation
            params: Generation parameters (optional)
            output_path: Custom output path (optional)
            
        Returns:
            Path to generated video file, or None if failed
        """
        try:
            if not self.is_loaded:
                if not await self.load_model():
                    raise RuntimeError("Failed to load any working model")
            
            logger.info(f"🎬 Generating video for video {video_id}: {prompt}")
            
            # Use provided params or defaults
            if params is None:
                params = VideoParams(prompt=prompt)
            else:
                params.prompt = prompt
            
            # Generate output path
            if not output_path:
                output_path = self._generate_output_path(video_id, prompt)
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Set seed if specified
            if params.seed != -1:
                torch.manual_seed(params.seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(params.seed)
            
            # Generate video
            logger.info("🎬 Running video generation...")
            
            with torch.no_grad():
                # Generate video using the pipeline
                result = self.pipeline(
                    prompt=params.prompt,
                    negative_prompt=params.negative_prompt,
                    num_inference_steps=params.num_steps,
                    guidance_scale=params.guidance_scale,
                    width=params.width,
                    height=params.height,
                    num_frames=params.num_frames
                )
                
                # Extract video frames from result
                if hasattr(result, 'frames') and result.frames is not None and len(result.frames) > 0:
                    video_frames = result.frames[0]
                elif hasattr(result, 'images') and result.images is not None and len(result.images) > 0:
                    video_frames = result.images[0]
                else:
                    # Try to get frames from the result object
                    video_frames = result[0] if isinstance(result, (list, tuple)) else result
                
                # Ensure we have the right format
                if isinstance(video_frames, torch.Tensor):
                    video_frames = video_frames.cpu().numpy()
                elif not isinstance(video_frames, np.ndarray):
                    raise ValueError(f"Unexpected video frames format: {type(video_frames)}")
                
                # Ensure correct shape (frames, height, width, channels)
                if len(video_frames.shape) == 4:
                    # Shape is already correct (frames, height, width, channels)
                    pass
                elif len(video_frames.shape) == 3:
                    # Add frame dimension if missing
                    video_frames = np.expand_dims(video_frames, axis=0)
                else:
                    raise ValueError(f"Unexpected video frames shape: {video_frames.shape}")
                
                # Debug info
                logger.info(f"Video frames shape: {video_frames.shape}")
                logger.info(f"Video frames dtype: {video_frames.dtype}")
                logger.info(f"Video frames range: {float(video_frames.min()):.3f} to {float(video_frames.max()):.3f}")
                
                # Export to video
                logger.info("💾 Exporting video...")
                export_to_video(
                    video_frames,
                    output_path,
                    fps=params.fps
                )
                
                if os.path.exists(output_path):
                    # Save generation metadata
                    self._save_generation_metadata(output_dir, video_id, prompt, params, output_path)
                    
                    logger.info(f"✅ Video generated successfully: {output_path}")
                    return output_path
                else:
                    logger.error("❌ Video generation failed")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Video generation error: {e}")
            return None
    
    def _generate_output_path(self, video_id: int, prompt: str) -> str:
        """Generate output file path"""
        timestamp = int(time.time())
        sanitized_prompt = self._sanitize_filename(prompt, max_length=50)
        filename = f"working_video_{video_id:06d}_{sanitized_prompt}_{timestamp}.mp4"
        return str(TEMP_DIR / f"working_video_{video_id:06d}_{timestamp}" / filename)
    
    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """Sanitize text for use in filename"""
        # Remove special characters and replace spaces
        sanitized = "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).rstrip()
        sanitized = sanitized.replace(' ', '_')
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_')
        
        return sanitized
    
    def _save_generation_metadata(self, output_dir: Path, video_id: int, prompt: str, 
                                 params: VideoParams, video_path: str):
        """Save metadata about the generation"""
        try:
            metadata = {
                "video_id": video_id,
                "prompt": prompt,
                "generation_params": {
                    "num_frames": params.num_frames,
                    "fps": params.fps,
                    "width": params.width,
                    "height": params.height,
                    "num_steps": params.num_steps,
                    "guidance_scale": params.guidance_scale,
                    "seed": params.seed
                },
                "output_path": video_path,
                "generated_at": time.time(),
                "generated_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
                "model": self.model_id,
                "device": self.device
            }
            
            metadata_file = output_dir / "generation_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"📋 Generation metadata saved: {metadata_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save metadata: {e}")
    
    def get_generation_presets(self) -> Dict[str, VideoParams]:
        """Get predefined generation presets"""
        return {
            "quick": VideoParams(
                prompt="",
                num_frames=8,
                fps=8,
                width=512,
                height=512,
                num_steps=25,
                guidance_scale=7.5
            ),
            "standard": VideoParams(
                prompt="",
                num_frames=16,
                fps=8,
                width=512,
                height=512,
                num_steps=50,
                guidance_scale=7.5
            ),
            "high_quality": VideoParams(
                prompt="",
                num_frames=24,
                fps=12,
                width=768,
                height=768,
                num_steps=75,
                guidance_scale=8.0
            )
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current generator status"""
        return {
            "model_loaded": self.is_loaded,
            "model_id": self.model_id,
            "device": self.device,
            "available_presets": list(self.get_generation_presets().keys()),
            "cuda_available": torch.cuda.is_available(),
            "available_models": self.available_models
        }

# Global instance
working_video_generator = WorkingVideoGenerator()

async def generate_video_working(video_id: int, prompt: str, 
                               preset: str = "standard") -> Optional[str]:
    """Convenience function for working video generation"""
    try:
        generator = WorkingVideoGenerator()
        
        presets = generator.get_generation_presets()
        if preset in presets:
            params = presets[preset]
            params.prompt = prompt
        else:
            params = VideoParams(prompt=prompt)
        
        return await generator.generate_video(video_id, prompt, params)
        
    except Exception as e:
        logger.error(f"❌ Working video generation failed: {e}")
        return None
