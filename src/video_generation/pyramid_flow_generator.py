"""
Pyramid Flow Text-to-Video Generator
Uses Pyramid Flow model via Gradio client for high-quality video generation
"""

import os
import logging
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import requests
from gradio_client import Client
from PIL import Image
import numpy as np

from src.config.settings import TEMP_DIR, PYRAMID_FLOW_API_URL

logger = logging.getLogger(__name__)

@dataclass
class VideoGenerationParams:
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
    motion_bucket_id: int = 127
    cond_aug: float = 0.02

class PyramidFlowGenerator:
    """
    Text-to-video generation using Pyramid Flow model
    """
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or PYRAMID_FLOW_API_URL
        self.client = None
        self.is_connected = False
        
        # Default Pyramid Flow parameters
        self.default_params = VideoGenerationParams(
            prompt="",
            negative_prompt="low quality, blurry, distorted",
            num_frames=16,
            fps=8,
            width=512,
            height=512,
            num_steps=50,
            guidance_scale=7.5,
            seed=-1,
            motion_bucket_id=127,
            cond_aug=0.02
        )
        
        # Ensure temp directory exists
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info("🎬 Pyramid Flow Generator initialized")
    
    async def connect(self) -> bool:
        """
        Connect to Pyramid Flow API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"🔌 Connecting to Pyramid Flow API: {self.api_url}")
            
            # Try to connect using Gradio client
            try:
                self.client = Client(self.api_url)
                # Test connection
                result = await self._test_connection()
                if result:
                    self.is_connected = True
                    logger.info("✅ Connected to Pyramid Flow API successfully")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Gradio client connection failed: {e}")
            
            # Fallback to direct HTTP connection
            if await self._test_http_connection():
                self.is_connected = True
                logger.info("✅ Connected to Pyramid Flow API via HTTP")
                return True
            
            logger.error("❌ Failed to connect to Pyramid Flow API")
            return False
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test Gradio client connection"""
        try:
            if self.client:
                # Try to get API info
                info = self.client.view_api()
                logger.info(f"📋 API Info: {info}")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Gradio client test failed: {e}")
        return False
    
    async def _test_http_connection(self) -> bool:
        """Test HTTP connection to API"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ HTTP connection test failed: {e}")
            return False
    
    async def generate_video(self, 
                            video_id: int,
                            prompt: str,
                            params: Optional[VideoGenerationParams] = None,
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
            if not self.is_connected:
                if not await self.connect():
                    raise RuntimeError("Not connected to Pyramid Flow API")
            
            logger.info(f"🎬 Generating video for video {video_id}: {prompt}")
            
            # Use provided params or defaults
            if params is None:
                params = VideoGenerationParams(prompt=prompt)
            else:
                params.prompt = prompt
            
            # Generate output path
            if not output_path:
                output_path = self._generate_output_path(video_id, prompt)
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate video using appropriate method
            if self.client:
                video_path = await self._generate_with_gradio(video_id, params, output_path)
            else:
                video_path = await self._generate_with_http(video_id, params, output_path)
            
            if video_path and os.path.exists(video_path):
                # Save generation metadata
                self._save_generation_metadata(output_dir, video_id, prompt, params, video_path)
                
                logger.info(f"✅ Video generated successfully: {video_path}")
                return video_path
            else:
                logger.error("❌ Video generation failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ Video generation error: {e}")
            return None
    
    async def _generate_with_gradio(self, video_id: int, params: VideoGenerationParams, output_path: str) -> Optional[str]:
        """Generate video using Gradio client"""
        try:
            logger.info("🎬 Using Gradio client for video generation")
            
            # Prepare parameters for Gradio API
            gradio_params = [
                params.prompt,                    # prompt
                params.negative_prompt,           # negative_prompt
                params.num_frames,                # num_frames
                params.fps,                       # fps
                params.width,                     # width
                params.height,                    # height
                params.num_steps,                 # num_steps
                params.guidance_scale,            # guidance_scale
                params.seed,                      # seed
                params.motion_bucket_id,          # motion_bucket_id
                params.cond_aug                   # cond_aug
            ]
            
            # Call the Gradio API
            result = self.client.predict(
                *gradio_params,
                api_name="/generate_video"  # Adjust based on actual API endpoint
            )
            
            # Process result
            if result and hasattr(result, 'data'):
                # Download the generated video
                video_path = await self._download_video(result.data, output_path)
                return video_path
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Gradio generation failed: {e}")
            return None
    
    async def _generate_with_http(self, video_id: int, params: VideoGenerationParams, output_path: str) -> Optional[str]:
        """Generate video using direct HTTP API calls"""
        try:
            logger.info("🎬 Using HTTP API for video generation")
            
            # Prepare request payload
            payload = {
                "prompt": params.prompt,
                "negative_prompt": params.negative_prompt,
                "num_frames": params.num_frames,
                "fps": params.fps,
                "width": params.width,
                "height": params.height,
                "num_steps": params.num_steps,
                "guidance_scale": params.guidance_scale,
                "seed": params.seed,
                "motion_bucket_id": params.motion_bucket_id,
                "cond_aug": params.cond_aug
            }
            
            # Make API request
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Download the generated video
                if 'video_url' in result:
                    video_path = await self._download_video(result['video_url'], output_path)
                    return video_path
                elif 'video_data' in result:
                    # Save base64 video data
                    video_path = self._save_base64_video(result['video_data'], output_path)
                    return video_path
            
            logger.error(f"❌ HTTP API failed: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"❌ HTTP generation failed: {e}")
            return None
    
    async def _download_video(self, video_url: str, output_path: str) -> Optional[str]:
        """Download video from URL"""
        try:
            logger.info(f"📥 Downloading video from: {video_url}")
            
            response = requests.get(video_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Video downloaded: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Video download failed: {e}")
            return None
    
    def _save_base64_video(self, video_data: str, output_path: str) -> Optional[str]:
        """Save base64 encoded video data"""
        try:
            import base64
            
            # Decode base64 data
            video_bytes = base64.b64decode(video_data)
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(video_bytes)
            
            logger.info(f"✅ Base64 video saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Base64 video save failed: {e}")
            return None
    
    def _generate_output_path(self, video_id: int, prompt: str) -> str:
        """Generate output file path"""
        timestamp = int(time.time())
        sanitized_prompt = self._sanitize_filename(prompt, max_length=50)
        filename = f"video_{video_id:06d}_{sanitized_prompt}_{timestamp}.mp4"
        return str(TEMP_DIR / f"pyramid_flow_{video_id:06d}_{timestamp}" / filename)
    
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
                                 params: VideoGenerationParams, video_path: str):
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
                    "seed": params.seed,
                    "motion_bucket_id": params.motion_bucket_id,
                    "cond_aug": params.cond_aug
                },
                "output_path": video_path,
                "generated_at": time.time(),
                "generated_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
                "model": "pyramid_flow"
            }
            
            metadata_file = output_dir / "generation_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"📋 Generation metadata saved: {metadata_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save metadata: {e}")
    
    async def generate_video_sequence(self, video_id: int, prompts: List[str], 
                                    params: Optional[VideoGenerationParams] = None,
                                    output_dir: Optional[str] = None) -> List[str]:
        """
        Generate multiple videos from a sequence of prompts
        
        Args:
            video_id: Unique video identifier
            prompts: List of text prompts
            params: Generation parameters (optional)
            output_dir: Custom output directory (optional)
            
        Returns:
            List of generated video paths
        """
        try:
            logger.info(f"🎬 Generating video sequence for video {video_id}: {len(prompts)} prompts")
            
            if not output_dir:
                timestamp = int(time.time())
                output_dir = str(TEMP_DIR / f"pyramid_flow_sequence_{video_id:06d}_{timestamp}")
            
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            generated_videos = []
            
            for i, prompt in enumerate(prompts):
                logger.info(f"🎬 Generating video {i+1}/{len(prompts)}: {prompt}")
                
                # Generate individual video
                video_path = await self.generate_video(
                    video_id=video_id,
                    prompt=prompt,
                    params=params,
                    output_path=os.path.join(output_dir, f"sequence_{i+1:02d}.mp4")
                )
                
                if video_path:
                    generated_videos.append(video_path)
                    logger.info(f"✅ Sequence video {i+1} generated: {video_path}")
                else:
                    logger.warning(f"⚠️ Failed to generate sequence video {i+1}")
                
                # Small delay between generations
                await asyncio.sleep(1)
            
            # Save sequence metadata
            self._save_sequence_metadata(output_dir, video_id, prompts, generated_videos, params)
            
            logger.info(f"✅ Video sequence completed: {len(generated_videos)}/{len(prompts)} videos generated")
            return generated_videos
            
        except Exception as e:
            logger.error(f"❌ Video sequence generation failed: {e}")
            return []
    
    def _save_sequence_metadata(self, output_dir: str, video_id: int, prompts: List[str], 
                               generated_videos: List[str], params: Optional[VideoGenerationParams]):
        """Save metadata about the video sequence"""
        try:
            metadata = {
                "video_id": video_id,
                "total_prompts": len(prompts),
                "successful_generations": len(generated_videos),
                "prompts": prompts,
                "generated_videos": generated_videos,
                "generation_params": {
                    "num_frames": params.num_frames if params else self.default_params.num_frames,
                    "fps": params.fps if params else self.default_params.fps,
                    "width": params.width if params else self.default_params.width,
                    "height": params.height if params else self.default_params.height,
                    "num_steps": params.num_steps if params else self.default_params.num_steps,
                    "guidance_scale": params.guidance_scale if params else self.default_params.guidance_scale,
                    "seed": params.seed if params else self.default_params.seed,
                    "motion_bucket_id": params.motion_bucket_id if params else self.default_params.motion_bucket_id,
                    "cond_aug": params.cond_aug if params else self.default_params.cond_aug
                },
                "generated_at": time.time(),
                "generated_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": "pyramid_flow"
            }
            
            metadata_file = Path(output_dir) / "sequence_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"📋 Sequence metadata saved: {metadata_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save sequence metadata: {e}")
    
    def get_generation_presets(self) -> Dict[str, VideoGenerationParams]:
        """Get predefined generation presets"""
        return {
            "quick": VideoGenerationParams(
                prompt="",
                num_frames=8,
                fps=8,
                width=512,
                height=512,
                num_steps=25,
                guidance_scale=7.5
            ),
            "standard": VideoGenerationParams(
                prompt="",
                num_frames=16,
                fps=8,
                width=512,
                height=512,
                num_steps=50,
                guidance_scale=7.5
            ),
            "high_quality": VideoGenerationParams(
                prompt="",
                num_frames=24,
                fps=12,
                width=768,
                height=768,
                num_steps=75,
                guidance_scale=8.0
            ),
            "cinematic": VideoGenerationParams(
                prompt="",
                num_frames=32,
                fps=16,
                width=1024,
                height=1024,
                num_steps=100,
                guidance_scale=8.5
            )
        }
    
    def create_custom_preset(self, name: str, **kwargs) -> VideoGenerationParams:
        """Create a custom generation preset"""
        base_params = VideoGenerationParams(prompt="")
        
        for key, value in kwargs.items():
            if hasattr(base_params, key):
                setattr(base_params, key, value)
        
        # Store custom preset
        if not hasattr(self, '_custom_presets'):
            self._custom_presets = {}
        
        self._custom_presets[name] = base_params
        logger.info(f"🎨 Custom preset '{name}' created")
        
        return base_params
    
    def get_status(self) -> Dict[str, Any]:
        """Get current generator status"""
        return {
            "is_connected": self.is_connected,
            "api_url": self.api_url,
            "client_available": self.client is not None,
            "available_presets": list(self.get_generation_presets().keys()),
            "custom_presets": list(getattr(self, '_custom_presets', {}).keys())
        }

# Global instance
pyramid_flow_generator = PyramidFlowGenerator()

async def generate_video_with_pyramid_flow(video_id: int, prompt: str, 
                                         preset: str = "standard") -> Optional[str]:
    """Convenience function for video generation"""
    try:
        generator = PyramidFlowGenerator()
        await generator.connect()
        
        presets = generator.get_generation_presets()
        if preset in presets:
            params = presets[preset]
            params.prompt = prompt
        else:
            params = VideoGenerationParams(prompt=prompt)
        
        return await generator.generate_video(video_id, prompt, params)
        
    except Exception as e:
        logger.error(f"❌ Video generation failed: {e}")
        return None
