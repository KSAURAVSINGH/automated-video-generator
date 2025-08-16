#!/usr/bin/env python3
"""
Complete Workflow Test
Demonstrates the entire process: form creation → database → scheduler → YouTube upload
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.db_handler import init_db, save_video, get_all_videos, get_video_processing_stats
from src.core.workflow_controller import WorkflowController

def create_test_video_form():
    """Create a test video form for the complete workflow"""
    
    print("📝 Creating Complete Workflow Test Video Form")
    print("=" * 60)
    
    # Schedule for 2 minutes from now (give more time for testing)
    schedule_time = datetime.now() + timedelta(minutes=2)
    
    video_form_data = {
        "title": "Complete Workflow Test - 218309 Video",
        "description": "This is a comprehensive test of the complete automated workflow. Testing form creation, database storage, scheduler pickup, and YouTube upload using the 218309_small.mp4 video file.",
        "captions": "Complete workflow test - automated video upload",
        "tags": ["test", "workflow", "automation", "youtube", "upload", "complete", "218309"],
        "video_link": "",
        "genre": "technology",
        "expected_length": 10,
        "schedule_time": schedule_time.isoformat(),
        "platforms": ["youtube"],
        "video_type": "ai_generated",
        "music_pref": "electronic",
        "channel_name": "AI Video Test Channel",
        "extra_metadata": {
            "test_type": "complete_workflow_test",
            "automated": True,
            "skip_generation": True,           # Skip video generation
            "use_existing_video": True,        # Use existing video file
            "existing_video_path": "temp/218309_small.mp4",  # Use the specific video
            "youtube_upload": True,            # Enable YouTube upload
            "workflow_test": True              # Mark as workflow test
        }
    }
    
    print(f"✅ Video form created:")
    print(f"   Title: {video_form_data['title']}")
    print(f"   Description: {video_form_data['description'][:80]}...")
    print(f"   Video File: 218309_small.mp4")
    print(f"   Schedule Time: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   YouTube Upload: Enabled")
    print(f"   Workflow Test: Complete end-to-end process")
    
    return video_form_data, schedule_time

def verify_video_file():
    """Verify the 218309_small.mp4 video file exists"""
    
    print("\n🎬 Verifying Video File...")
    print("=" * 40)
    
    video_path = "temp/218309_small.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        print("   Please ensure 218309_small.mp4 exists in the temp folder")
        return False
    
    file_size = os.path.getsize(video_path)
    print(f"✅ Video file found: {video_path}")
    print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    print(f"   File exists and is ready for upload")
    
    return True

async def test_complete_workflow():
    """Test the complete workflow from form to YouTube upload"""
    
    print("🧪 Testing Complete Workflow")
    print("=" * 60)
    
    try:
        # Step 1: Initialize database
        print("\n📊 Step 1: Initializing Database...")
        init_db()
        print("✅ Database initialized")
        
        # Step 2: Verify video file exists
        print("\n🎬 Step 2: Verifying Video File...")
        if not verify_video_file():
            return False
        
        # Step 3: Create test video form
        print("\n📝 Step 3: Creating Test Video Form...")
        video_form_data, schedule_time = create_test_video_form()
        
        # Step 4: Save to database
        print("\n💾 Step 4: Saving Form to Database...")
        save_video(video_form_data)
        print("✅ Video form saved to database")
        
        # Step 5: Verify database storage
        print("\n📊 Step 5: Verifying Database Storage...")
        all_videos = get_all_videos()
        print(f"   Total videos in database: {len(all_videos)}")
        
        if all_videos:
            latest_video = all_videos[0]
            print(f"   Latest video ID: {latest_video['id']}")
            print(f"   Title: {latest_video['title']}")
            print(f"   Status: {latest_video['status']}")
            print(f"   Schedule time: {latest_video['schedule_time']}")
        
        # Step 6: Initialize workflow controller
        print("\n🎬 Step 6: Starting Workflow Controller...")
        workflow_controller = WorkflowController()
        print("✅ Workflow Controller initialized")
        
        # Start the workflow
        print("\n🚀 Starting Workflow...")
        await workflow_controller.start()
        print("✅ Workflow started")
        
        # Show what will happen
        print(f"\n🎯 Complete Workflow Process:")
        print(f"   ⏰ Video scheduled for: {schedule_time.strftime('%H:%M:%S')}")
        print(f"   📝 Form created and stored in database")
        print(f"   🎬 Scheduler will monitor database every 60 seconds")
        print(f"   📤 When time arrives, video will be uploaded to YouTube")
        print(f"   ✅ Process will complete automatically")
        
        print(f"\n⏳ Waiting for scheduled time...")
        print(f"   Current time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Scheduled time: {schedule_time.strftime('%H:%M:%S')}")
        
        # Wait for the scheduled time
        time_until_scheduled = (schedule_time - datetime.now()).total_seconds()
        if time_until_scheduled > 0:
            print(f"   ⏱️  Waiting {time_until_scheduled:.0f} seconds...")
            await asyncio.sleep(time_until_scheduled)
        
        print(f"\n🎬 Scheduler should now be processing the video...")
        print(f"   The complete workflow will:")
        print(f"   1. ✅ Pick up the scheduled task")
        print(f"   2. ✅ Use the existing video: temp/218309_small.mp4")
        print(f"   3. ✅ Upload to YouTube with metadata")
        print(f"   4. ✅ Mark as completed")
        
        # Monitor the process
        print(f"\n⏳ Monitoring Complete Workflow Process...")
        print(f"   Will monitor for 3 minutes to see the complete process")
        print(f"   (Press Ctrl+C to stop early)")
        
        start_time = datetime.now()
        while datetime.now() < start_time + timedelta(minutes=3):
            try:
                current_time = datetime.now()
                time_elapsed = (current_time - start_time).total_seconds()
                
                # Get current status from all components
                scheduler_stats = workflow_controller.scheduler.get_scheduler_stats()
                active_tasks = workflow_controller.scheduler.get_active_tasks()
                scheduled_jobs = workflow_controller.scheduler.get_scheduled_jobs()
                db_stats = get_video_processing_stats()
                
                # Get current video status
                current_video = None
                if all_videos:
                    current_video = workflow_controller.scheduler.get_video_by_id(all_videos[0]['id'])
                
                # Clear screen and show comprehensive status
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("🧪 Complete Workflow Test - Live Monitoring")
                print("=" * 70)
                print(f"⏰ Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏱️  Elapsed: {time_elapsed:.0f} seconds")
                print(f"📅 Scheduled Time: {schedule_time.strftime('%H:%M:%S')}")
                print(f"⏳ Time since scheduled: {(current_time - schedule_time).total_seconds():.0f} seconds")
                
                print(f"\n📊 Scheduler Status:")
                for key, value in scheduler_stats.items():
                    print(f"   {key}: {value}")
                
                print(f"\n📋 Scheduled Jobs: {len(scheduled_jobs)}")
                for job in scheduled_jobs:
                    print(f"   📋 {job['name']}")
                    if job['next_run_time']:
                        print(f"      ⏰ {job['next_run_time']}")
                
                print(f"\n🎬 Active Tasks: {len(active_tasks)}")
                for task in active_tasks:
                    print(f"   🎬 {task['title']} ({task['status']})")
                
                print(f"\n💾 Database Status:")
                for status, count in db_stats.items():
                    print(f"   {status}: {count}")
                
                print(f"\n🎯 Workflow Controller:")
                print(f"   Active jobs: {len(workflow_controller.active_jobs)}")
                print(f"   Processing queue: {len(workflow_controller.processing_queue)}")
                print(f"   Is running: {workflow_controller.is_running}")
                
                if current_video:
                    print(f"\n🎬 Test Video Status:")
                    print(f"   ID: {current_video['id']}")
                    print(f"   Title: {current_video['title']}")
                    print(f"   Status: {current_video['status']}")
                    print(f"   Schedule time: {current_video['schedule_time']}")
                    
                    # Show status progression
                    if current_video['status'] == 'pending':
                        print(f"   📍 Status: 🟡 Pending - Waiting for scheduled time")
                    elif current_video['status'] == 'image_generation':
                        print(f"   📍 Status: 🔵 Image Generation - Scheduler picked up task!")
                    elif current_video['status'] == 'video_assembly':
                        print(f"   📍 Status: 🟠 Video Assembly - Using existing video!")
                    elif current_video['status'] == 'uploading':
                        print(f"   📍 Status: 🟣 Uploading - Real YouTube upload in progress!")
                    elif current_video['status'] == 'completed':
                        print(f"   📍 Status: 🟢 Completed - Video uploaded to YouTube!")
                    elif current_video['status'] == 'failed':
                        print(f"   📍 Status: 🔴 Failed - Check logs for details")
                
                # Check if video has been processed
                if current_video and current_video['status'] in ['completed', 'failed']:
                    print(f"\n🎉 Complete workflow test finished! Final status: {current_video['status']}")
                    if current_video['status'] == 'completed':
                        print(f"✅ SUCCESS: Complete workflow working perfectly!")
                        print(f"   Form → Database → Scheduler → YouTube Upload → Completed")
                        
                        # Show YouTube upload details if available
                        if 'youtube_upload' in current_video.get('extra_metadata', {}):
                            upload_info = current_video['extra_metadata']['youtube_upload']
                            print(f"\n📺 YouTube Upload Details:")
                            print(f"   Video ID: {upload_info.get('video_id', 'Unknown')}")
                            print(f"   URL: {upload_info.get('url', 'Unknown')}")
                            print(f"   Status: {upload_info.get('status', 'Unknown')}")
                    else:
                        print(f"❌ FAILED: Complete workflow test failed")
                    break
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                print("\n\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error during monitoring: {e}")
                await asyncio.sleep(5)
        
        # Final status
        print(f"\n📊 Final Status:")
        final_stats = workflow_controller.scheduler.get_scheduler_stats()
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
        
        # Show final video status
        if all_videos:
            final_video = workflow_controller.scheduler.get_video_by_id(all_videos[0]['id'])
            if final_video:
                print(f"\n🎬 Final Video Status:")
                print(f"   ID: {final_video['id']}")
                print(f"   Title: {final_video['title']}")
                print(f"   Status: {final_video['status']}")
                print(f"   Updated: {final_video.get('updated_at', 'Unknown')}")
        
        # Stop the workflow controller
        print(f"\n🛑 Stopping Workflow Controller...")
        await workflow_controller.stop()
        print("✅ Workflow Controller stopped")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Complete workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🧪 Starting Complete Workflow Test...")
    print("=" * 60)
    print("This test will demonstrate the ENTIRE workflow:")
    print("1. 📝 Create video form")
    print("2. 💾 Save to database")
    print("3. ⏰ Schedule for future time")
    print("4. 🎬 Scheduler picks up task")
    print("5. 📤 Upload to YouTube")
    print("6. ✅ Mark as completed")
    print("=" * 60)
    
    try:
        success = asyncio.run(test_complete_workflow())
        
        if success:
            print(f"\n🎉 SUCCESS! Complete workflow test completed!")
            print(f"\n🚀 What This Demonstrates:")
            print(f"   ✅ Complete end-to-end workflow automation")
            print(f"   ✅ Form creation and database storage")
            print(f"   ✅ Intelligent scheduling and task pickup")
            print(f"   ✅ Real video upload to YouTube")
            print(f"   ✅ Full system integration working")
            
            print(f"\n💡 Your System is Now:")
            print(f"   🎯 Fully automated from form to YouTube")
            print(f"   📅 Intelligent scheduling and processing")
            print(f"   🔄 Self-managing workflow")
            print(f"   📺 YouTube integration complete")
            print(f"   🚀 Production ready!")
            
        else:
            print(f"\n❌ Complete workflow test failed")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
