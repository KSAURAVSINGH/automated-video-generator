# input_handlers/streamlit_ui.py

import streamlit as st
import json
from datetime import datetime
import sys
import os

# Add the src directory to the path to import database modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.db_handler import save_video, init_db
from src.database.db_init import init_database

def video_input_form():
    st.title("🎬 AI Video Creation Form")
    
    # Initialize database if needed
    try:
        init_db()
        st.success("✅ Database connected successfully!")
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return

    # --- 1️⃣ Content Details ---
    st.header("1️⃣ Content Details")
    title = st.text_input("Video Title", placeholder="Enter your video title")
    description = st.text_area("Description / Body", placeholder="Detailed description or script")
    tags = st.text_input("Tags / Keywords (comma separated)")
    genre = st.selectbox("Genre / Category", ["Kids", "Education", "Gaming", "Comedy", "Music", "Other"])
    video_link = st.text_input("Existing Video Link (Optional)")
    storyboard = st.text_area("Storyboard / Script (Optional)")
    tone = st.selectbox("Tone / Style", ["Funny", "Serious", "Educational", "Cinematic", "Other"])
    language = st.selectbox("Language", ["English", "Hindi", "Spanish", "French", "Other"])
    voice_pref = st.selectbox("Voice Preference", ["Male", "Female", "Robotic", "Celebrity mimic", "No Voice"])
    image_refs = st.file_uploader("Image/Video References", type=["jpg", "png", "mp4"], accept_multiple_files=True)

    # --- 2️⃣ Production Settings ---
    st.header("2️⃣ Production Settings")
    video_type = st.selectbox("Video Type", ["Shorts/Reels", "Full-length", "Carousel"])
    expected_length = st.number_input("Expected Length (seconds)", min_value=5, max_value=600, value=60)
    resolution = st.selectbox("Resolution", ["720p", "1080p", "4K"])
    aspect_ratio = st.selectbox("Aspect Ratio", ["16:9", "9:16", "1:1"])
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
    platforms = st.multiselect("Publishing Platforms", ["YouTube", "Instagram", "TikTok", "Facebook", "Other"])
    channel = st.text_input("Channel / Account Name")
    schedule = st.date_input("Schedule Date", min_value=datetime.today())
    schedule_time = st.time_input("Schedule Time")
    privacy = st.selectbox("Privacy Setting", ["Public", "Unlisted", "Private"])
    monetization = st.checkbox("Enable Monetization?")
    audience = st.selectbox("Audience", ["Made for kids", "Not made for kids"])
    thumbnail_option = st.radio("Thumbnail", ["Upload", "AI-generate"])
    if thumbnail_option == "Upload":
        st.file_uploader("Upload Thumbnail", type=["jpg", "png"])
    pinned_comment = st.text_area("Pinned Comment (YouTube only)")
    cross_posting = st.checkbox("Cross-Post to Linked Platforms?")
    notify_subs = st.checkbox("Notify Subscribers? (YouTube only)")

    # Action Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Generate JSON", type="primary"):
            data = {
                "content_details": {
                    "title": title,
                    "description": description,
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "genre": genre,
                    "video_link": video_link,
                    "storyboard": storyboard,
                    "tone": tone,
                    "language": language,
                    "voice_preference": voice_pref,
                    "image_references": [f.name for f in image_refs] if image_refs else []
                },
                "production_settings": {
                    "video_type": video_type,
                    "expected_length_seconds": expected_length,
                    "resolution": resolution,
                    "aspect_ratio": aspect_ratio,
                    "background_music": {"enabled": bg_music_toggle, "source": bg_music_source},
                    "captions_enabled": captions_toggle,
                    "watermark_enabled": watermark_toggle,
                    "intro_enabled": intro_toggle,
                    "outro_enabled": outro_toggle,
                    "effects_style": effects_style
                },
                "publishing_settings": {
                    "platforms": platforms,
                    "channel": channel,
                    "schedule": str(schedule),
                    "schedule_time": str(schedule_time),
                    "privacy": privacy,
                    "monetization_enabled": monetization,
                    "audience": audience,
                    "thumbnail_option": thumbnail_option,
                    "pinned_comment": pinned_comment,
                    "cross_posting_enabled": cross_posting,
                    "notify_subscribers": notify_subs
                }
            }

            st.subheader("Generated JSON")
            st.code(json.dumps(data, indent=4))
            
            # Store the generated data in session state for saving
            st.session_state.generated_data = data
            st.success("✅ JSON generated successfully! Now you can save it to the database.")
    
    with col2:
        if st.button("💾 Save to Database", type="secondary"):
            if 'generated_data' in st.session_state:
                try:
                    # Prepare data for database saving (matching db_handler.py structure)
                    db_data = {
                        "title": st.session_state.generated_data["content_details"]["title"],
                        "description": st.session_state.generated_data["content_details"]["description"],
                        "captions": "Yes" if st.session_state.generated_data["production_settings"]["captions_enabled"] else "No",
                        "tags": st.session_state.generated_data["content_details"]["tags"],
                        "video_url": st.session_state.generated_data["content_details"]["video_link"],
                        "genre": st.session_state.generated_data["content_details"]["genre"],
                        "expected_length": st.session_state.generated_data["production_settings"]["expected_length_seconds"],
                        "schedule_time": f"{st.session_state.generated_data['publishing_settings']['schedule']} {st.session_state.generated_data['publishing_settings']['schedule_time']}",
                        "platforms": st.session_state.generated_data["publishing_settings"]["platforms"],
                        "video_type": st.session_state.generated_data["production_settings"]["video_type"],
                        "music_pref": "Yes" if st.session_state.generated_data["production_settings"]["background_music"]["enabled"] else "No",
                        "channel_name": st.session_state.generated_data["publishing_settings"]["channel"],
                        "extra_metadata": {
                            "tone": st.session_state.generated_data["content_details"]["tone"],
                            "language": st.session_state.generated_data["content_details"]["language"],
                            "voice_preference": st.session_state.generated_data["content_details"]["voice_preference"],
                            "storyboard": st.session_state.generated_data["content_details"]["storyboard"],
                            "resolution": st.session_state.generated_data["production_settings"]["resolution"],
                            "aspect_ratio": st.session_state.generated_data["production_settings"]["aspect_ratio"],
                            "watermark_enabled": st.session_state.generated_data["production_settings"]["watermark_enabled"],
                            "intro_enabled": st.session_state.generated_data["production_settings"]["intro_enabled"],
                            "outro_enabled": st.session_state.generated_data["production_settings"]["outro_enabled"],
                            "effects_style": st.session_state.generated_data["production_settings"]["effects_style"],
                            "privacy": st.session_state.generated_data["publishing_settings"]["privacy"],
                            "monetization_enabled": st.session_state.generated_data["publishing_settings"]["monetization_enabled"],
                            "audience": st.session_state.generated_data["publishing_settings"]["audience"],
                            "thumbnail_option": st.session_state.generated_data["publishing_settings"]["thumbnail_option"],
                            "pinned_comment": st.session_state.generated_data["publishing_settings"]["pinned_comment"],
                            "cross_posting_enabled": st.session_state.generated_data["publishing_settings"]["cross_posting_enabled"],
                            "notify_subscribers": st.session_state.generated_data["publishing_settings"]["notify_subscribers"]
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
                    st.write(f"**Platforms:** {', '.join(db_data['platforms']) if db_data['platforms'] else 'None'}")
                    st.write(f"**Channel:** {db_data['channel_name']}")
                    
                except Exception as e:
                    st.error(f"❌ Failed to save to database: {e}")
            else:
                st.warning("⚠️ Please generate JSON first before saving to database.")

    # Display current session data if available
    if 'generated_data' in st.session_state:
        with st.expander("📋 Current Form Data"):
            st.json(st.session_state.generated_data)

if __name__ == "__main__":
    video_input_form()
