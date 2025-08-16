# input_handlers/main_app.py

import streamlit as st
import sys
import os

# Add the src directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.input_handlers.streamlit_ui import video_input_form
from src.input_handlers.database_viewer import view_database
from src.input_handlers.pyramid_flow_ui import pyramid_flow_ui
from src.input_handlers.scheduler_dashboard import scheduler_dashboard

def main_app():
    st.set_page_config(
        page_title="AI Video Generator",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar navigation
    st.sidebar.title("🎬 AI Video Generator")
    st.sidebar.markdown("---")
    
    # Navigation menu
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🎥 Create Video", "🎬 Pyramid Flow", "📅 Scheduler Dashboard", "📊 View Database", "ℹ️ About"]
    )
    
    # Main content area
    if page == "🎥 Create Video":
        st.sidebar.markdown("### 📝 Create New Video")
        st.sidebar.markdown("Fill out the form to create a new video generation request.")
        video_input_form()
        
    elif page == "🎬 Pyramid Flow":
        st.sidebar.markdown("### 🎬 Pyramid Flow")
        st.sidebar.markdown("Visualize and manage the pyramid flow of video generation requests.")
        pyramid_flow_ui()
        
    elif page == "📅 Scheduler Dashboard":
        st.sidebar.markdown("### 📅 Scheduler Dashboard")
        st.sidebar.markdown("Monitor and control the automated video generation system.")
        scheduler_dashboard()
        
    elif page == "📊 View Database":
        st.sidebar.markdown("### 💾 Database Management")
        st.sidebar.markdown("View, edit, and manage saved video data.")
        view_database()
        
    elif page == "ℹ️ About":
        st.sidebar.markdown("### ℹ️ About")
        st.sidebar.markdown("Learn more about this application.")
        
        st.title("ℹ️ About AI Video Generator")
        st.markdown("""
        ## 🎬 Automated Video Generation System
        
        This application allows you to create and manage AI-powered video generation requests.
        
        ### ✨ Features:
        - **🎥 Video Creation Form**: Comprehensive form for video specifications
        - **💾 Database Storage**: SQLite database for persistent data storage
        - **📊 Data Management**: View and manage saved video requests
        - **🔧 Advanced Settings**: Detailed production and publishing options
        
        ### 🏗️ Architecture:
        - **Frontend**: Streamlit web interface
        - **Backend**: Python with SQLAlchemy ORM
        - **Database**: SQLite with custom schema
        - **Integration**: Ready for video generation pipeline
        
        ### 🚀 How to Use:
        1. **Create Video**: Fill out the form with your video requirements
        2. **Generate JSON**: Create structured configuration data
        3. **Save to Database**: Store your video request for processing
        4. **View Data**: Check saved requests and manage them
        
        ### 🔮 Future Features:
        - Video generation pipeline integration
        - Automated scheduling and processing
        - Multi-platform upload management
        - Analytics and performance tracking
        
        ---
        **Version**: 1.0.0  
        **Built with**: Streamlit, SQLAlchemy, Python 3.13
        """)

if __name__ == "__main__":
    main_app()
