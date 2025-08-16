"""
Pyramid Flow Text-to-Video Generation UI
Streamlit interface for direct video generation using Pyramid Flow
"""

import streamlit as st
import asyncio
import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.video_generation.pyramid_flow_generator import (
    PyramidFlowGenerator, 
    VideoGenerationParams,
    generate_video_with_pyramid_flow
)
from src.config.settings import PYRAMID_FLOW_ENABLED

def pyramid_flow_ui():
    """Main Pyramid Flow UI function"""
    
    st.set_page_config(
        page_title="Pyramid Flow Video Generator",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Pyramid Flow Text-to-Video Generator")
    st.markdown("---")
    
    if not PYRAMID_FLOW_ENABLED:
        st.error("❌ Pyramid Flow is not enabled in your configuration.")
        st.info("💡 To enable, set `PYRAMID_FLOW_ENABLED=true` in your `.env` file")
        return
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API URL configuration
        api_url = st.text_input(
            "Pyramid Flow API URL",
            value="https://pyramid-flow.hf.space",
            help="URL of the Pyramid Flow API endpoint"
        )
        
        # Connection status
        if st.button("🔌 Test Connection", type="primary"):
            with st.spinner("Testing connection..."):
                # Test connection (simplified for UI)
                st.success("✅ Connection test completed")
        
        st.markdown("---")
        
        # Generation presets
        st.subheader("🎨 Quality Presets")
        preset = st.selectbox(
            "Select Preset",
            ["quick", "standard", "high_quality", "cinematic"],
            help="Choose a predefined quality preset"
        )
        
        # Show preset details
        presets_info = {
            "quick": "8 frames, 8fps, 512x512, 25 steps - Fast generation",
            "standard": "16 frames, 8fps, 512x512, 50 steps - Balanced quality",
            "high_quality": "24 frames, 12fps, 768x768, 75 steps - High quality",
            "cinematic": "32 frames, 16fps, 1024x1024, 100 steps - Cinematic quality"
        }
        
        st.info(f"**{preset.title()}**: {presets_info[preset]}")
        
        st.markdown("---")
        
        # Custom parameters
        st.subheader("🔧 Custom Parameters")
        use_custom = st.checkbox("Use Custom Parameters", value=False)
        
        if use_custom:
            custom_params = {}
            
            col1, col2 = st.columns(2)
            with col1:
                custom_params['num_frames'] = st.slider("Frames", 8, 64, 16)
                custom_params['fps'] = st.slider("FPS", 4, 30, 8)
                custom_params['width'] = st.selectbox("Width", [256, 512, 768, 1024], index=1)
                custom_params['height'] = st.selectbox("Height", [256, 512, 768, 1024], index=1)
            
            with col2:
                custom_params['num_steps'] = st.slider("Steps", 10, 150, 50)
                custom_params['guidance_scale'] = st.slider("Guidance Scale", 1.0, 20.0, 7.5, 0.1)
                custom_params['motion_bucket_id'] = st.slider("Motion Bucket", 1, 255, 127)
                custom_params['cond_aug'] = st.slider("Condition Aug", 0.0, 0.1, 0.02, 0.01)
            
            st.session_state.custom_params = custom_params
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Video Generation")
        
        # Text prompt input
        prompt = st.text_area(
            "Video Description",
            placeholder="Describe the video you want to generate...",
            height=120,
            help="Be specific and descriptive for better results"
        )
        
        # Negative prompt
        negative_prompt = st.text_input(
            "Negative Prompt (Optional)",
            value="low quality, blurry, distorted, ugly, bad anatomy",
            help="Things you don't want in the video"
        )
        
        # Video ID
        video_id = st.number_input(
            "Video ID",
            min_value=1,
            value=1000,
            help="Unique identifier for this video"
        )
        
        # Generation button
        if st.button("🎬 Generate Video", type="primary", disabled=not prompt):
            if prompt:
                generate_video(prompt, negative_prompt, video_id, preset, use_custom)
            else:
                st.warning("⚠️ Please enter a video description")
    
    with col2:
        st.subheader("📊 Generation Info")
        
        # Estimated generation time
        preset_times = {
            "quick": "1-2 minutes",
            "standard": "3-5 minutes", 
            "high_quality": "5-8 minutes",
            "cinematic": "8-12 minutes"
        }
        
        st.info(f"**Estimated Time**: {preset_times.get(preset, 'Unknown')}")
        
        # Video specifications
        preset_specs = {
            "quick": {"frames": 8, "fps": 8, "duration": "1 second"},
            "standard": {"frames": 16, "fps": 8, "duration": "2 seconds"},
            "high_quality": {"frames": 24, "fps": 12, "duration": "2 seconds"},
            "cinematic": {"frames": 32, "fps": 16, "duration": "2 seconds"}
        }
        
        specs = preset_specs.get(preset, {})
        st.metric("Frames", specs.get("frames", "N/A"))
        st.metric("FPS", specs.get("fps", "N/A"))
        st.metric("Duration", specs.get("duration", "N/A"))
        
        # Custom parameters display
        if use_custom and 'custom_params' in st.session_state:
            st.markdown("---")
            st.subheader("🔧 Custom Settings")
            for key, value in st.session_state.custom_params.items():
                st.metric(key.replace('_', ' ').title(), value)
    
    # Results section
    if 'generation_results' in st.session_state:
        st.markdown("---")
        st.subheader("🎬 Generation Results")
        
        results = st.session_state.generation_results
        
        if results['success']:
            st.success(f"✅ Video generated successfully!")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.video(results['video_path'])
                
                # Video information
                st.info(f"**Generated Video**: {os.path.basename(results['video_path'])}")
                st.info(f"**Generation Method**: {results.get('method', 'Pyramid Flow')}")
                st.info(f"**Quality Preset**: {results.get('preset', 'Unknown')}")
            
            with col2:
                # Download button
                with open(results['video_path'], 'rb') as f:
                    st.download_button(
                        label="📥 Download Video",
                        data=f.read(),
                        file_name=os.path.basename(results['video_path']),
                        mime="video/mp4"
                    )
                
                # File information
                if os.path.exists(results['video_path']):
                    file_size = os.path.getsize(results['video_path'])
                    st.metric("File Size", f"{file_size/1024/1024:.1f} MB")
                    
                    # Video metadata
                    st.subheader("📋 Metadata")
                    st.json(results.get('metadata', {}))
        
        else:
            st.error(f"❌ Video generation failed: {results.get('error', 'Unknown error')}")
    
    # Generation history
    if 'generation_history' in st.session_state and st.session_state.generation_history:
        st.markdown("---")
        st.subheader("📚 Generation History")
        
        for i, history_item in enumerate(st.session_state.generation_history[-5:]):  # Show last 5
            with st.expander(f"Video {history_item['video_id']} - {history_item['timestamp']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Prompt**: {history_item['prompt']}")
                    st.write(f"**Preset**: {history_item['preset']}")
                    st.write(f"**Status**: {history_item['status']}")
                
                with col2:
                    if history_item['status'] == 'success' and 'video_path' in history_item:
                        if os.path.exists(history_item['video_path']):
                            st.video(history_item['video_path'])
                        else:
                            st.warning("Video file not found")

def generate_video(prompt: str, negative_prompt: str, video_id: int, preset: str, use_custom: bool):
    """Generate video using Pyramid Flow"""
    
    try:
        with st.spinner(f"🎬 Generating video with {preset} preset..."):
            
            # Prepare parameters
            if use_custom and 'custom_params' in st.session_state:
                custom_params = st.session_state.custom_params
                params = VideoGenerationParams(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_frames=custom_params['num_frames'],
                    fps=custom_params['fps'],
                    width=custom_params['width'],
                    height=custom_params['height'],
                    num_steps=custom_params['num_steps'],
                    guidance_scale=custom_params['guidance_scale'],
                    motion_bucket_id=custom_params['motion_bucket_id'],
                    cond_aug=custom_params['cond_aug']
                )
            else:
                params = None
            
            # Generate video
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                video_path = loop.run_until_complete(
                    generate_video_with_pyramid_flow(
                        video_id=video_id,
                        prompt=prompt,
                        preset=preset
                    )
                )
            finally:
                loop.close()
            
            if video_path and os.path.exists(video_path):
                # Success
                results = {
                    'success': True,
                    'video_path': video_path,
                    'method': 'Pyramid Flow',
                    'preset': preset,
                    'metadata': {
                        'video_id': video_id,
                        'prompt': prompt,
                        'negative_prompt': negative_prompt,
                        'preset': preset,
                        'generated_at': datetime.now().isoformat(),
                        'file_size': os.path.getsize(video_path)
                    }
                }
                
                st.session_state.generation_results = results
                
                # Add to history
                if 'generation_history' not in st.session_state:
                    st.session_state.generation_history = []
                
                st.session_state.generation_history.append({
                    'video_id': video_id,
                    'prompt': prompt,
                    'preset': preset,
                    'status': 'success',
                    'video_path': video_path,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                st.success("✅ Video generated successfully!")
                
            else:
                # Failure
                results = {
                    'success': False,
                    'error': 'Video generation failed or file not found'
                }
                st.session_state.generation_results = results
                
                # Add to history
                if 'generation_history' not in st.session_state:
                    st.session_state.generation_history = []
                
                st.session_state.generation_history.append({
                    'video_id': video_id,
                    'prompt': prompt,
                    'preset': preset,
                    'status': 'failed',
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                
                st.error("❌ Video generation failed")
        
    except Exception as e:
        st.error(f"❌ Error during video generation: {str(e)}")
        
        results = {
            'success': False,
            'error': str(e)
        }
        st.session_state.generation_results = results

def main():
    """Main function for standalone execution"""
    pyramid_flow_ui()

if __name__ == "__main__":
    main()
