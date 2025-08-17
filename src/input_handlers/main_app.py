# input_handlers/main_app.py

import streamlit as st
import sys
import os
import asyncio
import threading
from urllib.parse import parse_qs, urlparse

# Add the src directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.input_handlers.streamlit_ui import video_input_form
from src.input_handlers.database_viewer import view_database
from src.input_handlers.pyramid_flow_ui import pyramid_flow_ui
from src.input_handlers.scheduler_dashboard import scheduler_dashboard

# Global workflow controller instance
workflow_controller = None
workflow_thread = None

def start_workflow_controller():
    """Start the workflow controller in a background thread"""
    global workflow_controller, workflow_thread
    
    try:
        from src.core.workflow_controller import WorkflowController
        
        if workflow_controller is None:
            workflow_controller = WorkflowController()
            
        if workflow_thread is None or not workflow_thread.is_alive():
            # Start workflow controller in background thread
            def run_workflow():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(workflow_controller.start())
                except Exception as e:
                    st.error(f"❌ Workflow controller error: {e}")
                finally:
                    loop.close()
            
            workflow_thread = threading.Thread(target=run_workflow, daemon=True)
            workflow_thread.start()
            
            st.success("🚀 Workflow Controller started automatically!")
            return True
    except Exception as e:
        st.error(f"❌ Failed to start workflow controller: {e}")
        return False

def stop_workflow_controller():
    """Stop the workflow controller"""
    global workflow_controller, workflow_thread
    
    try:
        if workflow_controller:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(workflow_controller.stop())
            finally:
                loop.close()
            workflow_controller = None
            
        if workflow_thread and workflow_thread.is_alive():
            workflow_thread.join(timeout=5)
            workflow_thread = None
            
        st.success("🛑 Workflow Controller stopped!")
        return True
    except Exception as e:
        st.error(f"❌ Failed to stop workflow controller: {e}")
        return False

def get_page_from_url():
    """Extract page parameter from URL query string"""
    try:
        # Get the current URL using the new stable API
        page = st.query_params.get("page", "🎥 Create Video")
        return page
    except:
        return "🎥 Create Video"

def set_page_url(page_name):
    """Set the URL with page parameter"""
    try:
        # Set query parameters using the new stable API
        st.query_params["page"] = page_name
    except:
        pass

def main_app():
    st.set_page_config(
        page_title="AI Video Generator",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state for current page if not exists
    if 'current_page' not in st.session_state:
        st.session_state.current_page = get_page_from_url()
    
    # Initialize workflow controller status
    if 'workflow_started' not in st.session_state:
        st.session_state.workflow_started = False
    
    # Sidebar navigation
    st.sidebar.title("🎬 AI Video Generator")
    st.sidebar.markdown("---")
    
    # Automatic Workflow Controller Section
    st.sidebar.markdown("### 🤖 Automatic Processing")
    
    if not st.session_state.workflow_started:
        if st.sidebar.button("🚀 Start Automatic Processing", type="primary"):
            if start_workflow_controller():
                st.session_state.workflow_started = True
                st.rerun()
    else:
        st.sidebar.success("🟢 Automatic Processing: RUNNING")
        if st.sidebar.button("🛑 Stop Processing", type="secondary"):
            if stop_workflow_controller():
                st.session_state.workflow_started = False
                st.rerun()
    
    # Auto-start workflow controller if not already started
    if not st.session_state.workflow_started:
        if start_workflow_controller():
            st.session_state.workflow_started = True
    
    st.sidebar.markdown("---")
    
    # Navigation menu with page state management
    page_options = ["🎥 Create Video", "🎬 Pyramid Flow", "📅 Scheduler Dashboard", "📊 View Database", "ℹ️ About"]
    
    # Get current page from session state or URL
    current_page = st.session_state.current_page
    
    # Navigation selectbox
    selected_page = st.sidebar.selectbox(
        "Choose a page:",
        page_options,
        index=page_options.index(current_page) if current_page in page_options else 0
    )
    
    # Update page if selection changed
    if selected_page != current_page:
        st.session_state.current_page = selected_page
        set_page_url(selected_page)
        st.rerun()
    
    # Main content area based on current page
    if current_page == "🎥 Create Video":
        st.sidebar.markdown("### 📝 Create New Video")
        st.sidebar.markdown("Fill out the form to create a new video generation request.")
        video_input_form()
        
    elif current_page == "🎬 Pyramid Flow":
        st.sidebar.markdown("### 🎬 Pyramid Flow")
        st.sidebar.markdown("Visualize and manage the pyramid flow of video generation requests.")
        pyramid_flow_ui()
        
    elif current_page == "📅 Scheduler Dashboard":
        st.sidebar.markdown("### 📅 Scheduler Dashboard")
        st.sidebar.markdown("Monitor and control the automated video generation system.")
        scheduler_dashboard()
        
    elif current_page == "📊 View Database":
        st.sidebar.markdown("### 💾 Database Management")
        st.sidebar.markdown("View, edit, and manage saved video data.")
        view_database()
        
    elif current_page == "ℹ️ About":
        st.sidebar.markdown("### ℹ️ About")
        st.sidebar.markdown("Learn more about this application.")
        
        st.title("ℹ️ About AI Video Generator")
        st.markdown("""
        ## 🎬 Automated Video Generation System
        
        This application allows you to create and manage AI-powered video generation requests optimized for production use.
        
        ### ✨ Features:
        - **🎥 Video Creation Form**: Streamlined form for video specifications
        - **🤖 AI Text Enhancement**: Improve titles, descriptions, and tags automatically
        - **💾 Direct Database Storage**: Save data directly without JSON generation
        - **📊 Enhanced Data Management**: View and manage saved video requests with improved organization
        - **🎬 Production Focus**: Optimized for Shorts/Reels and YouTube publishing
        - **📅 Advanced Scheduler Dashboard**: Monitor pending schedules with exact timing and status tracking
        - **🔗 Persistent Page Navigation**: Maintains page state across refreshes
        - **🤖 Automatic Processing**: Videos are processed automatically when ready
        
        ### 🏗️ Architecture:
        - **Frontend**: Streamlit web interface with URL-based routing
        - **Backend**: Python with SQLAlchemy ORM
        - **Database**: SQLite with custom schema
        - **AI Enhancement**: Google Gemini API for content improvement
        - **Scheduler**: Enhanced dashboard with real-time status monitoring
        - **Navigation**: Session state and URL parameter management
        - **Integration**: Automated workflow controller for video processing
        
        ### 🚀 How to Use:
        1. **Create Video**: Fill out the form with your video requirements
        2. **AI Enhancement**: Use AI to improve titles, descriptions, and tags
        3. **Save to Database**: Store your video request directly for processing
        4. **Automatic Processing**: Videos are processed automatically when ready
        5. **Monitor Progress**: Use the enhanced scheduler dashboard to track status
        6. **View Data**: Check saved requests and manage them efficiently
        7. **Navigate Freely**: Switch between pages without losing your place
        
        ### 🎯 Production Features:
        - **Video Type**: Hardcoded to Shorts/Reels for consistency
        - **Platform**: YouTube-only publishing (using account credentials)
        - **Thumbnail**: Upload-only (AI generation disabled)
        - **Privacy**: Hardcoded to Private for safety (prevents accidental public uploads)
        - **Simplified UI**: Removed unused features for production focus
        - **Page Persistence**: Maintains current page across browser refreshes
        - **Automatic Processing**: No manual intervention required
        
        ### 📅 Enhanced Scheduler Dashboard:
        - **⏰ Pending Schedules**: View upcoming videos with exact processing times
        - **🔄 Processing Status**: Monitor videos currently being generated
        - **✅ Completion Tracking**: Separate sections for completed, failed, and cancelled videos
        - **📊 Real-time Updates**: Auto-refresh functionality for live monitoring
        - **🎛️ System Controls**: Start/stop workflow controller and health checks
        - **🤖 Automatic Processing**: Videos move through stages automatically
        
        ### 🔗 Navigation Features:
        - **URL Parameters**: Each page has a unique URL endpoint
        - **Session Persistence**: Maintains page state across refreshes
        - **Deep Linking**: Direct links to specific pages work correctly
        - **State Management**: Preserves user's current location
        
        ### 🤖 Automatic Processing Features:
        - **Background Processing**: Workflow controller runs automatically
        - **Video Detection**: Automatically detects videos ready for processing
        - **Status Updates**: Videos move through stages automatically
        - **No Manual Intervention**: Fully automated workflow
        - **Real-time Monitoring**: Live status updates in dashboard
        
        ### 🔮 Future Features:
        - Video generation pipeline integration
        - Automated scheduling and processing
        - Multi-platform upload management
        - Analytics and performance tracking
        - Advanced URL routing and deep linking
        
        ---
        **Version**: 3.0.0 (Automatic Processing & Gemini API Integration)  
        **Built with**: Streamlit, SQLAlchemy, Python 3.13, Google Gemini API, Enhanced Dashboard, URL Routing, Automatic Processing
        """)

def main():
    """Main function for standalone execution"""
    main_app()

if __name__ == "__main__":
    main()
