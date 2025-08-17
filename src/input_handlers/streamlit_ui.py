# input_handlers/streamlit_ui.py

import streamlit as st
import json
from datetime import datetime, timedelta
import sys
import os
import time
from pathlib import Path

# Add the src directory to the path to import database modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.db_handler import save_video, init_db, delete_all_videos
from src.database.db_init import init_database

def video_input_form():
    st.title("🎬 AI Video Creation Form")
    
    # Initialize session state for form persistence
    if 'form_last_save' not in st.session_state:
        st.session_state.form_last_save = None
    
    if 'form_auto_save' not in st.session_state:
        st.session_state.form_auto_save = True
    
    if 'form_draft_data' not in st.session_state:
        st.session_state.form_draft_data = {}
    
    # Initialize database if needed
    try:
        init_db()
        st.success("✅ Database connected successfully!")
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return

    # --- 1️⃣ Content Details ---
    st.header("1️⃣ Content Details")
    
    # Form state management
    with st.expander("⚙️ Form State Management", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Auto-save toggle
            auto_save = st.checkbox(
                "Auto-save form data", 
                value=st.session_state.form_auto_save,
                key="form_auto_save_toggle"
            )
            
            if auto_save != st.session_state.form_auto_save:
                st.session_state.form_auto_save = auto_save
                st.rerun()
        
        with col2:
            # Manual save draft
            if st.button("💾 Save Draft"):
                # Save current form data to session state
                current_form_data = {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'genre': genre,
                    'tone': tone,
                    'language': language,
                    'voice_pref': voice_pref,
                    'storyboard': storyboard
                }
                st.session_state.form_draft_data = current_form_data
                st.session_state.form_last_save = datetime.now()
                st.success("✅ Draft saved!")
        
        with col3:
            # Load draft
            if st.button("📂 Load Draft") and st.session_state.form_draft_data:
                st.session_state.load_draft = True
                st.rerun()
            
            if st.session_state.form_last_save:
                st.info(f"Last save: {st.session_state.form_last_save.strftime('%H:%M:%S')}")
    
    # Load draft data if requested
    if st.session_state.get('load_draft', False) and st.session_state.form_draft_data:
        draft_data = st.session_state.form_draft_data
        title = draft_data.get('title', title)
        description = draft_data.get('description', description)
        tags = draft_data.get('tags', tags)
        genre = draft_data.get('genre', genre)
        tone = draft_data.get('tone', tone)
        language = draft_data.get('language', language)
        voice_pref = draft_data.get('voice_pref', voice_pref)
        storyboard = draft_data.get('storyboard', storyboard)
        
        # Clear the load flag
        del st.session_state.load_draft
        st.success("✅ Draft loaded successfully!")
    
    title = st.text_input("Video Title", placeholder="Enter your video title", value=title if 'title' in locals() else "")
    description = st.text_area("Description / Body", placeholder="Detailed description or script", value=description if 'description' in locals() else "")
    tags = st.text_input("Tags / Keywords (comma separated)", value=tags if 'tags' in locals() else "")
    genre = st.selectbox("Genre / Category", ["Kids", "Education", "Gaming", "Comedy", "Music", "Other"], index=["Kids", "Education", "Gaming", "Comedy", "Music", "Other"].index(genre) if 'genre' in locals() and genre in ["Kids", "Education", "Gaming", "Comedy", "Music", "Other"] else 0)
    
    # Video Input Section
    st.markdown("### 🎬 Video Input")
    
    # Check for existing video files in temp folder
    import glob
    existing_videos = glob.glob("temp/*.mp4")
    existing_video_path = None
    
    if existing_videos:
        # Find the largest video file (most likely the real video)
        existing_videos.sort(key=lambda x: os.path.getsize(x), reverse=True)
        largest_video = existing_videos[0]
        file_size = os.path.getsize(largest_video)
        
        if file_size > 1000:  # More than 1KB indicates real video
            existing_video_path = largest_video
            st.success(f"✅ Found existing video: {os.path.basename(largest_video)} ({file_size/1024/1024:.2f} MB)")
            st.info(f"📁 Path: {largest_video}")
            
            # Store in session state
            st.session_state.existing_video_path = existing_video_path
    
    # File upload for video (optional if existing video found)
    if existing_video_path:
        st.info("💡 You can upload a different video or use the existing one above")
    
    uploaded_video = st.file_uploader(
        "Upload Video File (MP4, MOV, AVI) - Optional if existing video found", 
        type=['mp4', 'mov', 'avi', 'mkv'],
        help="Upload your video file. If no file is uploaded, the system will use the existing video found above."
    )
    
    if uploaded_video is not None:
        # Save uploaded video to temp directory
        import tempfile
        import os
        
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        video_path = f"temp/uploaded_video_{int(time.time())}.mp4"
        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())
        
        st.success(f"✅ Video uploaded successfully: {uploaded_video.name}")
        st.info(f"📁 Saved to: {video_path}")
        
        # Store video path in session state
        st.session_state.uploaded_video_path = video_path
    else:
        # Check if we have a previously uploaded video
        if 'uploaded_video_path' in st.session_state and os.path.exists(st.session_state.uploaded_video_path):
            st.info(f"📁 Using previously uploaded video: {st.session_state.uploaded_video_path}")
        elif existing_video_path:
            st.info(f"📁 Will use existing video: {existing_video_path}")
        else:
            st.warning("⚠️ No video file found. Please upload a video or ensure there's a video in the temp folder.")
    
    # Legacy text input for video link (hidden by default, can be shown in advanced mode)
    with st.expander("🔗 Advanced: External Video Link (Optional)"):
        video_link = st.text_input(
            "External Video Link", 
            value=st.session_state.get('video_link', ''),
            help="Provide a direct link to an external video file (optional)"
        )
        if video_link:
            st.session_state.video_link = video_link
    
    storyboard = st.text_area("Storyboard / Script (Optional)", value=storyboard if 'storyboard' in locals() else "")
    tone = st.selectbox("Tone / Style", ["Funny", "Serious", "Educational", "Cinematic", "Other"], index=["Funny", "Serious", "Educational", "Cinematic", "Other"].index(tone) if 'tone' in locals() and tone in ["Funny", "Serious", "Educational", "Cinematic", "Other"] else 0)
    language = st.selectbox("Language", ["English", "Hindi", "Spanish", "French", "Other"], index=["English", "Hindi", "Spanish", "French", "Other"].index(language) if 'language' in locals() and language in ["English", "Hindi", "Spanish", "French", "Other"] else 0)
    voice_pref = st.selectbox("Voice Preference", ["Male", "Female", "Robotic", "Celebrity mimic", "No Voice"], index=["Male", "Female", "Robotic", "Celebrity mimic", "No Voice"].index(voice_pref) if 'voice_pref' in locals() and voice_pref in ["Male", "Female", "Robotic", "Celebrity mimic", "No Voice"] else 0)
    image_refs = st.file_uploader("Image/Video References", type=["jpg", "png", "mp4"], accept_multiple_files=True)

    # AI Text Improvement Section
    st.subheader("🤖 AI Text Enhancement")
    
    # Gemini API Key Configuration
    with st.expander("🔑 Gemini API Configuration", expanded=False):
        st.info("💡 Configure Google Gemini API for enhanced AI text improvement")
        
        # Try to load API key from environment configuration first
        try:
            from src.config.env_config import env_config
            env_gemini_key = env_config.get_gemini_api_key()
            
            if env_gemini_key:
                st.success("✅ Gemini API key loaded from environment configuration")
                st.info("🔒 API key is securely stored in config.env file")
                
                # Show API key status
                if hasattr(st.session_state, 'text_improver'):
                    status = st.session_state.text_improver.get_status()
                    if status.get('gemini_configured'):
                        st.success("🤖 Gemini API is active and ready to use")
                    else:
                        st.warning("⚠️ Gemini API not yet active")
                else:
                    st.success("🤖 Environment configuration ready")
                
                # Allow manual override if needed
                st.info("💡 You can manually override the environment key below if needed")
                
        except ImportError:
            st.warning("⚠️ Environment configuration not available")
            env_gemini_key = None
        
        # Check if API key is already set in session state
        if 'gemini_api_key' not in st.session_state:
            st.session_state.gemini_api_key = env_gemini_key or ""
        
        gemini_api_key = st.text_input(
            "Google Gemini API Key (Optional - Override Environment)", 
            value=st.session_state.gemini_api_key,
            type="password",
            placeholder="Enter your Gemini API key here to override environment",
            help="Get your API key from https://makersuite.google.com/app/apikey. Leave empty to use environment configuration."
        )
        
        if gemini_api_key != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = gemini_api_key
            # Update the text improver with new API key
            if hasattr(st.session_state, 'text_improver'):
                st.session_state.text_improver.set_gemini_api_key(gemini_api_key)
        
        # Show current API key source
        if env_gemini_key and not gemini_api_key:
            st.success("✅ Using environment configuration (recommended)")
        elif gemini_api_key:
            st.success("✅ Using manual API key override")
        else:
            st.warning("⚠️ No Gemini API key available - using fallback methods")
    
    # Initialize text improver with API key
    if 'text_improver' not in st.session_state:
        from src.utils.text_improver import TextImprover
        # Use environment key if available, otherwise use session state
        api_key = env_gemini_key if 'env_gemini_key' in locals() else st.session_state.get('gemini_api_key', '')
        st.session_state.text_improver = TextImprover(gemini_api_key=api_key)
    elif st.session_state.get('gemini_api_key') != st.session_state.text_improver.gemini_api_key:
        # Update API key if changed
        st.session_state.text_improver.set_gemini_api_key(st.session_state.get('gemini_api_key', ''))
    
    # Get text improver instance
    text_improver = st.session_state.text_improver
    
    # Show improvement options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✨ Improve Title", type="secondary"):
            if title:
                with st.spinner("🤖 Improving title with AI..."):
                    improved_title = text_improver.improve_title(title, genre, tone)
                    st.session_state.improved_title = improved_title
                    st.success(f"✅ Title improved: {improved_title}")
            else:
                st.warning("⚠️ Please enter a title first")
        
        if st.button("✨ Improve Description", type="secondary"):
            if description:
                with st.spinner("🤖 Improving description with AI..."):
                    improved_desc = text_improver.improve_description(description, genre, tone)
                    st.session_state.improved_description = improved_desc
                    st.success(f"✅ Description improved: {improved_desc[:100]}...")
            else:
                st.warning("⚠️ Please enter a description first")
    
    with col2:
        if st.button("✨ Improve Tags", type="secondary"):
            if tags:
                with st.spinner("🤖 Improving tags with AI..."):
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                    improved_tags = text_improver.improve_tags(tag_list, title, description, genre, tone)
                    st.session_state.improved_tags = improved_tags
                    st.success(f"✅ Tags improved: {len(improved_tags)} tags generated")
            else:
                st.warning("⚠️ Please enter tags first")
        
        if st.button("✨ Improve All Content", type="secondary"):
            if title and description and tags:
                with st.spinner("🤖 Improving all content with AI..."):
                    improved_content = text_improver.improve_all_content(title, description, [t.strip() for t in tags.split(",") if t.strip()], genre, tone)
                    st.session_state.improved_title = improved_content['title']
                    st.session_state.improved_description = improved_content['description']
                    st.session_state.improved_tags = improved_content['tags']
                    st.success("✅ All content improved successfully!")
            else:
                st.warning("⚠️ Please fill in title, description, and tags first")
    
    # Display improved content if available
    if 'improved_title' in st.session_state or 'improved_description' in st.session_state or 'improved_tags' in st.session_state:
        with st.expander("✨ AI Improved Content", expanded=True):
            if 'improved_title' in st.session_state:
                st.write(f"**Improved Title:** {st.session_state.improved_title}")
            if 'improved_description' in st.session_state:
                st.write(f"**Improved Description:** {st.session_state.improved_description}")
            if 'improved_tags' in st.session_state:
                st.write(f"**Improved Tags:** {', '.join(st.session_state.improved_tags)}")
            
            # Show which AI method was used
            if hasattr(text_improver, 'gemini_api_key') and text_improver.gemini_api_key:
                st.success("🤖 Content improved using Google Gemini API")
            else:
                st.info("📝 Content improved using fallback methods")

    # --- 2️⃣ Production Settings ---
    st.header("2️⃣ Production Settings")
    # Hardcoded to Shorts/Reels only as requested
    video_type = "Shorts/Reels"
    st.info(f"🎬 Video Type: {video_type} (Hardcoded for production)")
    
    expected_length = st.number_input("Expected Length (seconds)", min_value=5, max_value=600, value=60)
    resolution = st.selectbox("Resolution", ["720p", "1080p", "4K"])
    aspect_ratio = st.selectbox("Aspect Ratio", ["9:16"])  # Only 9:16 for shorts/reels
    bg_music_toggle = st.checkbox("Add Background Music?")
    bg_music_source = None
    if bg_music_toggle:
        bg_music_source = st.radio("Background Music Source", ["AI-generate", "Upload"])
        if bg_music_source == "Upload":
            st.file_uploader("Upload Music File", type=["mp3", "wav"])
    captions_toggle = st.checkbox("Add Subtitles / Captions?")
    watermark_toggle = st.checkbox("Add Watermark / Branding?")
    if watermark_toggle:
        st.file_uploader("Upload Watermark", type=["png"])
    intro_toggle = st.checkbox("Add Intro?")
    outro_toggle = st.checkbox("Add Outro?")
    effects_style = st.selectbox("Transitions / Effects Style", ["Smooth", "Fast cuts", "Flashy", "Minimal"])

    # --- 3️⃣ Publishing Settings ---
    st.header("3️⃣ Publishing Settings")
    # Hardcoded to YouTube only as requested
    platforms = ["YouTube"]
    st.info(f"📺 Publishing Platform: {', '.join(platforms)} (Hardcoded for production)")
    
    # Removed channel name as requested - using credentials directly
    schedule = st.date_input("Schedule Date", min_value=datetime.today())
    
    # Enhanced schedule time with 5-minute intervals
    st.subheader("⏰ Schedule Time Options")
    
    # Quick time presets with 5-minute intervals
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Quick Schedule (5-min intervals):**")
        if st.button("🕐 Now + 5 min", key="schedule_5min"):
            st.session_state.quick_schedule = "5min"
            st.rerun()
        if st.button("🕐 Now + 10 min", key="schedule_10min"):
            st.session_state.quick_schedule = "10min"
            st.rerun()
        if st.button("🕐 Now + 15 min", key="schedule_15min"):
            st.session_state.quick_schedule = "15min"
            st.rerun()
    
    with col2:
        st.write("**Quick Schedule (5-min intervals):**")
        if st.button("🕐 Now + 20 min", key="schedule_20min"):
            st.session_state.quick_schedule = "20min"
            st.rerun()
        if st.button("🕐 Now + 25 min", key="schedule_25min"):
            st.session_state.quick_schedule = "25min"
            st.rerun()
        if st.button("🕐 Now + 30 min", key="schedule_30min"):
            st.session_state.quick_schedule = "30min"
            st.rerun()
    
    with col3:
        st.write("**Custom Schedule:**")
        if st.button("🕐 Now + 1 hour", key="schedule_1hour"):
            st.session_state.quick_schedule = "1hour"
            st.rerun()
        if st.button("🕐 Now + 2 hours", key="schedule_2hours"):
            st.session_state.quick_schedule = "2hours"
            st.rerun()
        if st.button("🕐 Custom Time", key="schedule_custom"):
            st.session_state.quick_schedule = "custom"
            st.rerun()
    
    # Handle quick schedule selection
    if 'quick_schedule' in st.session_state:
        quick_schedule = st.session_state.quick_schedule
        
        if quick_schedule == "5min":
            schedule_time = (datetime.now() + timedelta(minutes=5)).time()
            st.success("✅ Scheduled for 5 minutes from now")
        elif quick_schedule == "10min":
            schedule_time = (datetime.now() + timedelta(minutes=10)).time()
            st.success("✅ Scheduled for 10 minutes from now")
        elif quick_schedule == "15min":
            schedule_time = (datetime.now() + timedelta(minutes=15)).time()
            st.success("✅ Scheduled for 15 minutes from now")
        elif quick_schedule == "20min":
            schedule_time = (datetime.now() + timedelta(minutes=20)).time()
            st.success("✅ Scheduled for 20 minutes from now")
        elif quick_schedule == "25min":
            schedule_time = (datetime.now() + timedelta(minutes=25)).time()
            st.success("✅ Scheduled for 25 minutes from now")
        elif quick_schedule == "30min":
            schedule_time = (datetime.now() + timedelta(minutes=30)).time()
            st.success("✅ Scheduled for 30 minutes from now")
        elif quick_schedule == "1hour":
            schedule_time = (datetime.now() + timedelta(hours=1)).time()
            st.success("✅ Scheduled for 1 hour from now")
        elif quick_schedule == "2hours":
            schedule_time = (datetime.now() + timedelta(hours=2)).time()
            st.success("✅ Scheduled for 2 hours from now")
        elif quick_schedule == "custom":
            schedule_time = st.time_input("Custom Schedule Time")
            st.info("⏰ Set your custom schedule time")
        
        # Clear quick schedule after use
        del st.session_state.quick_schedule
    else:
        # Default time input
        schedule_time = st.time_input("Schedule Time")
    
    # Show selected schedule
    if 'schedule_time' in locals():
        selected_datetime = datetime.combine(schedule, schedule_time)
        time_until = selected_datetime - datetime.now()
        
        if time_until.total_seconds() > 0:
            if time_until.total_seconds() < 3600:  # Less than 1 hour
                minutes = int(time_until.total_seconds() // 60)
                st.info(f"⏰ Video will be processed in {minutes} minutes")
            else:
                hours = int(time_until.total_seconds() // 3600)
                minutes = int((time_until.total_seconds() % 3600) // 60)
                st.info(f"⏰ Video will be processed in {hours} hours and {minutes} minutes")
        else:
            st.warning("⚠️ Selected time is in the past. Video will be processed immediately.")
            schedule_time = datetime.now().time()
            schedule = datetime.now().date()
    
    # Hardcoded to Private as requested - can't upload public videos directly
    privacy = "Private"
    st.info(f"🔒 Privacy Setting: {privacy} (Hardcoded for production - public uploads not supported)")
    
    # Removed monetization, audience, cross posting, and notify subscribers as requested
    thumbnail_option = "Upload"  # Hardcoded to upload only as requested
    st.info("🖼️ Thumbnail: Upload only (AI generation disabled)")
    if thumbnail_option == "Upload":
        st.file_uploader("Upload Thumbnail", type=["jpg", "png"])
    pinned_comment = st.text_area("Pinned Comment (YouTube only)")

    # Action Buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save to Database", type="primary"):
            # Determine which video path to use
            video_path_to_use = None
            
            if st.session_state.get('uploaded_video_path') and os.path.exists(st.session_state.uploaded_video_path):
                # Use newly uploaded video
                video_path_to_use = st.session_state.uploaded_video_path
                st.info(f"📁 Using newly uploaded video: {video_path_to_use}")
            elif st.session_state.get('existing_video_path') and os.path.exists(st.session_state.existing_video_path):
                # Use existing video found in temp folder
                video_path_to_use = st.session_state.existing_video_path
                st.info(f"📁 Using existing video: {video_path_to_use}")
            elif st.session_state.get('video_link'):
                # Use external video link
                video_path_to_use = st.session_state.video_link
                st.info(f"🔗 Using external video link: {video_path_to_use}")
            else:
                st.error("❌ No video file available. Please upload a video or ensure there's a video in the temp folder.")
                return
            
            # Validate required fields
            if not title or not description or not genre:
                st.error("❌ Please fill in all required fields!")
                return
            
            try:
                # Prepare data for database saving
                db_data = {
                    "title": title,
                    "description": description,
                    "genre": genre,
                    "expected_length": expected_length,
                    "schedule_time": f"{schedule} {schedule_time}",
                    "platforms": platforms,
                    "video_type": video_type,
                    "music_pref": "Yes" if bg_music_toggle else "No",
                    "channel_name": "YouTube Account",  # Placeholder since we're using credentials
                    "video_link": video_path_to_use,  # Use the determined video path
                    "extra_metadata": {
                        "tone": tone,
                        "language": language,
                        "voice_preference": voice_pref,
                        "storyboard": storyboard,
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio,
                        "watermark_enabled": watermark_toggle,
                        "intro_enabled": intro_toggle,
                        "outro_enabled": outro_toggle,
                        "effects_style": effects_style,
                        "privacy": privacy,
                        "thumbnail_option": thumbnail_option,
                        "pinned_comment": pinned_comment,
                        "background_music_source": bg_music_source,
                        "image_references": [f.name for f in image_refs] if image_refs else [],
                        "tags": [t.strip() for t in tags.split(",") if t.strip()],
                        "captions": "Yes" if captions_toggle else "No"
                    }
                }
                
                # Save to database
                save_video(db_data)
                st.success("✅ Video data saved to database successfully!")
                
                # Show saved data summary
                st.subheader("📊 Saved Data Summary")
                st.write(f"**Title:** {db_data['title']}")
                st.write(f"**Genre:** {db_data['genre']}")
                st.write(f"**Length:** {db_data['expected_length']} seconds")
                st.write(f"**Platform:** {', '.join(db_data['platforms'])}")
                st.write(f"**Video Type:** {db_data['video_type']}")
                
                # Clear session state after successful save
                if 'improved_title' in st.session_state:
                    del st.session_state.improved_title
                if 'improved_description' in st.session_state:
                    del st.session_state.improved_description
                if 'improved_tags' in st.session_state:
                    del st.session_state.improved_tags
                
            except Exception as e:
                st.error(f"❌ Failed to save to database: {e}")
    
    with col2:
        if st.button("🔄 Clear Form", type="secondary"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Delete All Records", type="secondary"):
            if st.button("⚠️ Confirm Delete All", key="confirm_delete_all"):
                try:
                    deleted_count = delete_all_videos()
                    st.success(f"✅ {deleted_count} database records deleted successfully!")
                    
                    # Set session state to trigger UI updates everywhere
                    st.session_state.records_deleted = True
                    st.session_state.deleted_count = deleted_count
                    
                    # Clear any existing form data
                    if 'improved_title' in st.session_state:
                        del st.session_state.improved_title
                    if 'improved_description' in st.session_state:
                        del st.session_state.improved_description
                    if 'improved_tags' in st.session_state:
                        del st.session_state.improved_tags
                    
                    # Rerun to update all UI components
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to delete all records: {e}")

    # Show deletion notification if records were deleted
    if st.session_state.get('records_deleted', False):
        st.success(f"🎉 Successfully deleted {st.session_state.get('deleted_count', 0)} records from database!")
        st.info("💡 The UI has been refreshed to reflect the changes. All views will show the updated data.")
        
        # Clear the notification after showing
        del st.session_state.records_deleted
        del st.session_state.deleted_count

    # Display current form data
    with st.expander("📋 Current Form Data"):
        form_data = {
            "title": st.session_state.get('improved_title', title),
            "description": st.session_state.get('improved_description', description),
            "tags": st.session_state.get('improved_tags', [t.strip() for t in tags.split(",") if t.strip()] if tags else []),
            "genre": genre,
            "video_type": video_type,
            "expected_length": expected_length,
            "platforms": platforms
        }
        st.json(form_data)

if __name__ == "__main__":
    video_input_form()
