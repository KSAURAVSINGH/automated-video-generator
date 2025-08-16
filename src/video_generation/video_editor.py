"""
Video Editor for Automated Video Generation
Assembles videos from generated images using MoviePy
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy import concatenate_videoclips
from moviepy.audio.io import AudioFileClip
from moviepy.video.fx import FadeIn, FadeOut
import json
import time

from src.config.settings import TEMP_DIR

logger = logging.getLogger(__name__)

class VideoEditor:
    """
    Handles video assembly from generated images
    """
    
    def __init__(self):
        self.temp_dir = TEMP_DIR
        self.supported_formats = ['.png', '.jpg', '.jpeg']
        
        logger.info("🎬 Video Editor initialized")
    
    def create_video_from_images(self, video_id: int, image_paths: Dict[str, List[str]], 
                                duration: int, title: str, description: str,
                                fps: int = 24, transition_duration: float = 1.0) -> str:
        """
        Create a video from generated images
        
        Args:
            video_id: Unique video identifier
            image_paths: Dictionary of scene images {scene_name: [image_paths]}
            duration: Target video duration in seconds
            title: Video title
            description: Video description
            fps: Frames per second
            transition_duration: Duration of transitions between scenes
            
        Returns:
            Path to the generated video file
        """
        try:
            logger.info(f"🎬 Creating video for video {video_id}: {title}")
            
            # Create output directory
            output_dir = self.temp_dir / f"video_{video_id:06d}_output_{int(time.time())}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Calculate scene durations
            total_scenes = len(image_paths)
            scene_duration = (duration - (total_scenes - 1) * transition_duration) / total_scenes
            
            logger.info(f"📊 Video breakdown: {total_scenes} scenes, {scene_duration:.1f}s per scene")
            
            # Process each scene
            scene_clips = []
            for scene_name, images in image_paths.items():
                if images:
                    scene_clip = self._create_scene_clip(
                        images, scene_duration, fps, transition_duration
                    )
                    scene_clips.append(scene_clip)
                    logger.info(f"✅ Created scene: {scene_name} with {len(images)} images")
            
            if not scene_clips:
                raise ValueError("No valid scenes created")
            
            # Concatenate all scenes
            final_video = concatenate_videoclips(scene_clips, method="compose")
            
            # Add title and description overlay
            final_video = self._add_text_overlays(final_video, title, description)
            
            # Generate output filename
            output_filename = f"video_{video_id:06d}_{int(time.time())}.mp4"
            output_path = output_dir / output_filename
            
            # Write video file
            final_video.write_videofile(
                str(output_path),
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=str(output_dir / "temp-audio.m4a"),
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Clean up
            final_video.close()
            for clip in scene_clips:
                clip.close()
            
            # Save metadata
            self._save_video_metadata(output_dir, video_id, title, description, image_paths)
            
            logger.info(f"✅ Video created successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to create video: {e}")
            raise
    
    def _create_scene_clip(self, images: List[str], duration: float, fps: int, 
                           transition_duration: float) -> ImageClip:
        """
        Create a scene clip from multiple images with transitions
        """
        try:
            if len(images) == 1:
                # Single image - show for full duration
                clip = ImageClip(images[0]).set_duration(duration)
            else:
                # Multiple images - create slideshow with transitions
                image_duration = (duration - (len(images) - 1) * transition_duration) / len(images)
                
                image_clips = []
                for i, image_path in enumerate(images):
                    img_clip = ImageClip(image_path).set_duration(image_duration)
                    
                    # Add fade in/out effects
                    if i == 0:  # First image
                        img_clip = img_clip.fadein(transition_duration)
                    elif i == len(images) - 1:  # Last image
                        img_clip = img_clip.fadeout(transition_duration)
                    else:  # Middle images
                        img_clip = img_clip.fadein(transition_duration/2).fadeout(transition_duration/2)
                    
                    image_clips.append(img_clip)
                
                # Concatenate images with crossfade transitions
                clip = concatenate_videoclips(image_clips, method="compose")
            
            # Resize to standard dimensions (16:9 aspect ratio)
            clip = clip.resize(width=1920, height=1080)
            
            return clip
            
        except Exception as e:
            logger.error(f"❌ Error creating scene clip: {e}")
            raise
    
    def _add_text_overlays(self, video_clip, title: str, description: str) -> CompositeVideoClip:
        """
        Add title and description text overlays to the video
        """
        try:
            from moviepy.video.tools.drawing import color_gradient
            
            # Create title text clip
            title_clip = self._create_text_clip(
                title, 
                fontsize=60, 
                color='white',
                stroke_color='black',
                stroke_width=2
            ).set_position(('center', 100)).set_duration(video_clip.duration)
            
            # Create description text clip (smaller, at bottom)
            desc_clip = self._create_text_clip(
                description[:100] + "..." if len(description) > 100 else description,
                fontsize=30,
                color='white',
                stroke_color='black',
                stroke_width=1
            ).set_position(('center', 'bottom')).set_duration(video_clip.duration)
            
            # Composite video with text overlays
            final_video = CompositeVideoClip([video_clip, title_clip, desc_clip])
            
            return final_video
            
        except Exception as e:
            logger.error(f"❌ Error adding text overlays: {e}")
            # Return original video if text overlay fails
            return video_clip
    
    def _create_text_clip(self, text: str, fontsize: int = 40, color: str = 'white',
                          stroke_color: str = 'black', stroke_width: int = 1) -> ImageClip:
        """
        Create a text clip with specified styling
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            # Create a blank image for text
            img_width, img_height = 1920, 200
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", fontsize)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontsize)
                except:
                    font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center text
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
            
            # Draw stroke (outline)
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx*dx + dy*dy <= stroke_width*stroke_width:
                        draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
            
            # Draw main text
            draw.text((x, y), text, font=font, fill=color)
            
            # Convert PIL image to numpy array
            img_array = np.array(img)
            
            # Create MoviePy clip from numpy array
            text_clip = ImageClip(img_array).set_duration(3)  # Show for 3 seconds
            
            return text_clip
            
        except Exception as e:
            logger.error(f"❌ Error creating text clip: {e}")
            # Return a simple colored rectangle as fallback
            from moviepy.video.VideoClip import ColorClip
            return ColorClip(size=(1920, 100), color=(0, 0, 0)).set_duration(3)
    
    def _save_video_metadata(self, output_dir: Path, video_id: int, title: str, 
                             description: str, image_paths: Dict[str, List[str]]):
        """
        Save metadata about the generated video
        """
        try:
            metadata = {
                'video_id': video_id,
                'title': title,
                'description': description,
                'created_at': time.time(),
                'created_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_scenes': len(image_paths),
                'scenes': {}
            }
            
            # Add scene information
            for scene_name, images in image_paths.items():
                metadata['scenes'][scene_name] = {
                    'image_count': len(images),
                    'image_paths': images
                }
            
            # Save metadata file
            metadata_file = output_dir / 'video_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"📋 Video metadata saved: {metadata_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving video metadata: {e}")
    
    def create_video_with_audio(self, video_path: str, audio_path: str, 
                                output_path: Optional[str] = None) -> str:
        """
        Add audio to an existing video
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Optional output path
            
        Returns:
            Path to the final video with audio
        """
        try:
            logger.info(f"🎵 Adding audio to video: {video_path}")
            
            # Load video and audio
            video_clip = ImageClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Set audio duration to match video
            if audio_clip.duration > video_clip.duration:
                audio_clip = audio_clip.subclip(0, video_clip.duration)
            elif audio_clip.duration < video_clip.duration:
                # Loop audio if it's shorter than video
                loops_needed = int(video_clip.duration / audio_clip.duration) + 1
                audio_clip = concatenate_videoclips([audio_clip] * loops_needed)
                audio_clip = audio_clip.subclip(0, video_clip.duration)
            
            # Combine video and audio
            final_video = video_clip.set_audio(audio_clip)
            
            # Generate output path if not provided
            if not output_path:
                video_file = Path(video_path)
                output_path = str(video_file.parent / f"{video_file.stem}_with_audio{video_file.suffix}")
            
            # Write final video
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Clean up
            video_clip.close()
            audio_clip.close()
            final_video.close()
            
            logger.info(f"✅ Video with audio created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error adding audio to video: {e}")
            raise
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get information about a video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(video_path)
            
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': clip.size,
                'aspect_ratio': clip.size[0] / clip.size[1],
                'file_size': Path(video_path).stat().st_size,
                'file_size_mb': Path(video_path).stat().st_size / (1024 * 1024)
            }
            
            clip.close()
            return info
            
        except Exception as e:
            logger.error(f"❌ Error getting video info: {e}")
            return {}
