"""
Image generation using Stable Diffusion for video generation.
"""

import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import logging
import json
import base64
from PIL import Image
import io
import time

from src.config.settings import TEMP_DIR

logger = logging.getLogger(__name__)

class StableDiffusionAPI:
    """Interface for Stable Diffusion API calls."""
    
    def __init__(self, api_url: str = "http://localhost:7860"):
        self.api_url = api_url
        self.endpoints = {
            'txt2img': f"{api_url}/sdapi/v1/txt2img",
            'img2img': f"{api_url}/sdapi/v1/img2img",
            'options': f"{api_url}/sdapi/v1/options",
            'models': f"{api_url}/sdapi/v1/sd-models"
        }
    
    def check_connection(self) -> bool:
        """Check if the Stable Diffusion API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/sdapi/v1/sd-models", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Stable Diffusion API: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Stable Diffusion models."""
        try:
            response = requests.get(self.endpoints['models'])
            if response.status_code == 200:
                models = response.json()
                return [model['title'] for model in models]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def generate_image(self, prompt: str, negative_prompt: str = "", 
                      width: int = 512, height: int = 512, steps: int = 20,
                      cfg_scale: float = 7.0, seed: int = -1) -> Optional[bytes]:
        """
        Generate image using text-to-image.
        
        Args:
            prompt: Text prompt for image generation
            negative_prompt: Negative prompt
            width: Image width
            height: Image height
            steps: Number of denoising steps
            cfg_scale: CFG scale for prompt adherence
            seed: Random seed (-1 for random)
        
        Returns:
            Image bytes if successful, None otherwise
        """
        try:
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "seed": seed,
                "sampler_name": "DPM++ 2M Karras"
            }
            
            response = requests.post(self.endpoints['txt2img'], json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if 'images' in result and result['images']:
                    # Decode base64 image
                    image_data = base64.b64decode(result['images'][0])
                    return image_data
                else:
                    logger.error("No images in response")
                    return None
            else:
                logger.error(f"API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return None
    
    def generate_image_from_image(self, init_image: bytes, prompt: str, 
                                negative_prompt: str = "", strength: float = 0.75,
                                steps: int = 20, cfg_scale: float = 7.0) -> Optional[bytes]:
        """
        Generate image using image-to-image.
        
        Args:
            init_image: Initial image bytes
            prompt: Text prompt
            negative_prompt: Negative prompt
            strength: Denoising strength
            steps: Number of steps
            cfg_scale: CFG scale
        
        Returns:
            Generated image bytes
        """
        try:
            # Encode image to base64
            init_image_b64 = base64.b64encode(init_image).decode('utf-8')
            
            payload = {
                "init_images": [init_image_b64],
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "denoising_strength": strength,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "sampler_name": "DPM++ 2M Karras"
            }
            
            response = requests.post(self.endpoints['img2img'], json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if 'images' in result and result['images']:
                    image_data = base64.b64decode(result['images'][0])
                    return image_data
                else:
                    logger.error("No images in response")
                    return None
            else:
                logger.error(f"API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate image from image: {e}")
            return None

class ImageGenerationManager:
    """Manager for image generation operations with database logging."""
    
    def __init__(self, api_url: str = "http://localhost:7860"):
        self.sd_api = StableDiffusionAPI(api_url)
        self._check_api_availability()
    
    def _check_api_availability(self):
        """Check if Stable Diffusion API is available."""
        if not self.sd_api.check_connection():
            logger.warning("Stable Diffusion API not accessible. Image generation will not work.")
        else:
            logger.info("Stable Diffusion API connection established")
    
    def generate_single_image(self, video_id: int, prompt: str, 
                            output_path: Optional[str] = None,
                            **kwargs) -> Optional[str]:
        """
        Generate a single image with database logging.
        
        Args:
            video_id: ID of the video being generated
            prompt: Text prompt for image generation
            output_path: Path to save the generated image
            **kwargs: Additional generation parameters
        
        Returns:
            Path to the generated image if successful, None otherwise
        """
        return self.generate_image_with_logging(video_id, prompt, output_path, **kwargs)
    
    def generate_multiple_images(self, video_id: int, prompts: List[str],
                               output_folder: Optional[str] = None,
                               **kwargs) -> List[str]:
        """
        Generate multiple images from a list of prompts.
        
        Args:
            video_id: ID of the video being generated
            prompts: List of text prompts for image generation
            output_folder: Folder to store all generated images
            **kwargs: Additional generation parameters
        
        Returns:
            List of paths to generated images
        """
        generated_images = []
        
        # Create organized folder structure
        if not output_folder:
            output_folder = self._create_video_folder(video_id)
        
        for i, prompt in enumerate(prompts):
            output_path = Path(output_folder) / f"image_{i+1:03d}_{self._sanitize_filename(prompt)}.png"
            
            image_path = self.generate_image_with_logging(
                video_id=video_id,
                prompt=prompt,
                output_path=str(output_path),
                **kwargs
            )
            
            if image_path:
                generated_images.append(image_path)
                # Update folder metadata with new image
                self._update_folder_metadata(output_folder, image_path, prompt)
        
        logger.info(f"Multiple image generation completed for video {video_id}: {len(generated_images)} images")
        return generated_images
    
    def generate_story_images(self, video_id: int, story_prompt: str, 
                            num_scenes: int = 5, scene_variations: int = 2,
                            output_folder: Optional[str] = None,
                            **kwargs) -> Dict[str, List[str]]:
        """
        Generate a sequence of story images based on a main prompt.
        
        Args:
            video_id: ID of the video being generated
            story_prompt: Main story prompt/theme
            num_scenes: Number of scenes to generate
            scene_variations: Number of variations per scene
            output_folder: Folder to store story images
            **kwargs: Additional generation parameters
        
        Returns:
            Dictionary with scene numbers as keys and lists of image paths as values
        """
        story_images = {}
        
        # Create organized folder structure
        if not output_folder:
            output_folder = self._create_video_folder(video_id, "story")
        
        # Generate scene variations
        for scene_num in range(1, num_scenes + 1):
            scene_images = []
            
            # Create scene-specific prompts
            scene_prompts = self._generate_scene_prompts(story_prompt, scene_num, scene_variations)
            
            for var_num, scene_prompt in enumerate(scene_prompts):
                output_path = Path(output_folder) / f"scene_{scene_num:02d}_var_{var_num+1:02d}_{self._sanitize_filename(scene_prompt)}.png"
                
                image_path = self.generate_image_with_logging(
                    video_id=video_id,
                    prompt=scene_prompt,
                    output_path=str(output_path),
                    **kwargs
                )
                
                if image_path:
                    scene_images.append(image_path)
                    # Update folder metadata with new image
                    self._update_folder_metadata(output_folder, image_path, scene_prompt)
            
            story_images[f"scene_{scene_num:02d}"] = scene_images
        
        logger.info(f"Story image generation completed for video {video_id}: {num_scenes} scenes with {scene_variations} variations each")
        return story_images
    
    def _generate_scene_prompts(self, main_prompt: str, scene_num: int, variations: int) -> List[str]:
        """
        Generate scene-specific prompts based on main story prompt.
        
        Args:
            main_prompt: Main story prompt
            scene_num: Current scene number
            variations: Number of variations to generate
        
        Returns:
            List of scene-specific prompts
        """
        scene_prompts = []
        
        # Base scene descriptions
        scene_descriptions = [
            "opening scene, establishing shot",
            "character introduction, medium shot",
            "action sequence, dynamic composition",
            "emotional moment, close-up",
            "climax scene, dramatic lighting",
            "resolution, peaceful atmosphere",
            "transition scene, smooth flow",
            "detail shot, focus on elements",
            "wide angle view, environmental context",
            "final scene, conclusion"
        ]
        
        # Get scene description (cycle through if more scenes than descriptions)
        scene_desc = scene_descriptions[(scene_num - 1) % len(scene_descriptions)]
        
        # Generate variations
        for var_num in range(variations):
            if var_num == 0:
                # First variation: direct scene description
                prompt = f"{main_prompt}, {scene_desc}, scene {scene_num}"
            else:
                # Additional variations: add style modifiers
                style_modifiers = [
                    "cinematic lighting, professional photography",
                    "artistic style, creative interpretation",
                    "dramatic shadows, moody atmosphere",
                    "bright colors, vibrant palette",
                    "monochrome, black and white",
                    "soft focus, dreamy quality",
                    "sharp details, high contrast",
                    "warm tones, golden hour",
                    "cool tones, blue hour",
                    "textured surface, tactile quality"
                ]
                modifier = style_modifiers[(var_num - 1) % len(style_modifiers)]
                prompt = f"{main_prompt}, {scene_desc}, scene {scene_num}, {modifier}"
            
            scene_prompts.append(prompt)
        
        return scene_prompts
    
    def _create_video_folder(self, video_id: int, folder_type: str = "images") -> str:
        """
        Create organized folder structure for video images.
        
        Args:
            video_id: ID of the video
            folder_type: Type of folder (images, story, etc.)
        
        Returns:
            Path to created folder
        """
        timestamp = int(time.time())
        folder_name = f"video_{video_id:06d}_{folder_type}_{timestamp}"
        folder_path = TEMP_DIR / folder_name
        
        # Create folder and subdirectories
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Create metadata file
        metadata = {
            "video_id": video_id,
            "folder_type": folder_type,
            "created_at": timestamp,
            "created_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_images": 0,
            "images": []
        }
        
        metadata_file = folder_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Created organized folder: {folder_path}")
        return str(folder_path)
    
    def _update_folder_metadata(self, folder_path: str, image_path: str, prompt: str):
        """
        Update folder metadata with new image information.
        
        Args:
            folder_path: Path to the folder
            image_path: Path to the new image
            prompt: Prompt used to generate the image
        """
        metadata_file = Path(folder_path) / "metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Update metadata
                metadata["total_images"] += 1
                metadata["images"].append({
                    "filename": Path(image_path).name,
                    "prompt": prompt,
                    "created_at": int(time.time()),
                    "created_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "file_size": Path(image_path).stat().st_size if Path(image_path).exists() else 0
                })
                
                # Save updated metadata
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
            except Exception as e:
                logger.error(f"Failed to update folder metadata: {e}")
    
    def _sanitize_filename(self, prompt: str, max_length: int = 50) -> str:
        """
        Sanitize prompt text for use in filename.
        
        Args:
            prompt: Text prompt
            max_length: Maximum length for filename
        
        Returns:
            Sanitized filename-safe string
        """
        # Remove special characters and replace spaces with underscores
        sanitized = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_'))
        sanitized = sanitized.replace(' ', '_').replace('-', '_')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_')
        
        return sanitized
    
    def generate_image_with_logging(self, video_id: int, prompt: str, 
                                  output_path: Optional[str] = None,
                                  **kwargs) -> Optional[str]:
        """
        Generate image with database logging.
        
        Args:
            video_id: ID of the video being generated
            prompt: Text prompt for image generation
            output_path: Path to save the generated image
            **kwargs: Additional generation parameters
        
        Returns:
            Path to the generated image if successful, None otherwise
        """
        log_id = None
        
        try:
            # Create generation log entry
            # The original code had get_db() and GenerationLogCRUD here, which are no longer imported.
            # Assuming these were removed or replaced by a different logging mechanism.
            # For now, commenting out the lines that rely on these imports.
            # with get_db() as db:
            #     log_entry = GenerationLogCRUD.create(db, 
            #         video_id=video_id,
            #         step='image_generation',
            #         status='processing'
            #     )
            #     log_id = log_entry.id
            
            # Generate image
            image_data = self.sd_api.generate_image(prompt, **kwargs)
            
            if not image_data:
                raise RuntimeError("Failed to generate image")
            
            # Save image to file
            if not output_path:
                output_path = self._generate_output_path(video_id)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            # Update log entry to completed
            # with get_db() as db:
            #     GenerationLogCRUD.update_status(
            #         db, log_id, 'completed', 
            #         meta_data=json.dumps({
            #             'output_path': output_path,
            #             'prompt': prompt,
            #             'parameters': kwargs
            #         })
            #     )
            
            logger.info(f"Image generation completed for video {video_id}: {output_path}")
            return output_path
            
        except Exception as e:
            # Update log entry to failed
            if log_id:
                try:
                    # with get_db() as db:
                    #     GenerationLogCRUD.update_status(
                    #         db, log_id, 'failed', 
                    #         error_message=str(e)
                    #     )
                    pass # Original code had this line commented out
                except Exception as log_error:
                    logger.error(f"Failed to update log entry: {log_error}")
            
            logger.error(f"Image generation failed for video {video_id}: {e}")
            return None
    
    def generate_image_from_image_with_logging(self, video_id: int, init_image_path: str,
                                             prompt: str, output_path: Optional[str] = None,
                                             **kwargs) -> Optional[str]:
        """
        Generate image from existing image with database logging.
        
        Args:
            video_id: ID of the video
            init_image_path: Path to initial image
            prompt: Text prompt
            output_path: Output path for generated image
            **kwargs: Additional parameters
        
        Returns:
            Path to generated image
        """
        log_id = None
        
        try:
            # Read initial image
            with open(init_image_path, 'rb') as f:
                init_image_data = f.read()
            
            # Create generation log entry
            # with get_db() as db:
            #     log_entry = GenerationLogCRUD.create(db, 
            #         video_id=video_id,
            #         step='image_generation_img2img',
            #         status='processing'
            #     )
            #     log_id = log_entry.id
            
            # Generate image
            image_data = self.sd_api.generate_image_from_image(
                init_image_data, prompt, **kwargs
            )
            
            if not image_data:
                raise RuntimeError("Failed to generate image from image")
            
            # Save image
            if not output_path:
                output_path = self._generate_output_path(video_id, suffix='_img2img')
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            # Update log entry
            # with get_db() as db:
            #     GenerationLogCRUD.update_status(
            #         db, log_id, 'completed', 
            #         meta_data=json.dumps({
            #             'output_path': output_path,
            #             'init_image': init_image_path,
            #             'prompt': prompt,
            #             'parameters': kwargs
            #         })
            #     )
            
            logger.info(f"Image generation from image completed for video {video_id}: {output_path}")
            return output_path
            
        except Exception as e:
            if log_id:
                try:
                    # with get_db() as db:
                    #     GenerationLogCRUD.update_status(
                    #         db, log_id, 'failed', 
                    #         error_message=str(e)
                    #     )
                    pass # Original code had this line commented out
                except Exception as log_error:
                    logger.error(f"Failed to update log entry: {log_error}")
            
            logger.error(f"Image generation from image failed for video {video_id}: {e}")
            return None
    
    def batch_generate_images(self, video_id: int, prompts: List[str],
                             **kwargs) -> List[str]:
        """
        Generate multiple images from prompts.
        
        Args:
            video_id: ID of the video
            prompts: List of text prompts
            **kwargs: Generation parameters
        
        Returns:
            List of paths to generated images
        """
        generated_images = []
        
        for i, prompt in enumerate(prompts):
            output_path = self._generate_output_path(video_id, suffix=f'_batch_{i}')
            
            image_path = self.generate_image_with_logging(
                video_id=video_id,
                prompt=prompt,
                output_path=output_path,
                **kwargs
            )
            
            if image_path:
                generated_images.append(image_path)
        
        logger.info(f"Batch image generation completed for video {video_id}: {len(generated_images)} images")
        return generated_images
    
    def _generate_output_path(self, video_id: int, suffix: str = '') -> str:
        """Generate output path for generated image."""
        import time
        timestamp = int(time.time())
        filename = f"video_{video_id}_image{suffix}_{timestamp}.png"
        return str(TEMP_DIR / filename)
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get status of the Stable Diffusion API."""
        return {
            'api_accessible': self.sd_api.check_connection(),
            'available_models': self.sd_api.get_available_models(),
            'api_url': self.sd_api.api_url
        }

# Global image generation manager instance
image_manager = ImageGenerationManager()
