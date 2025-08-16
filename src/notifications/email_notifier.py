"""
Email notification system using SMTP for the Automated Video Generator.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import json

from ..config.settings import (
    SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    ENABLE_EMAIL_NOTIFICATIONS
)

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Email notification system using SMTP."""
    
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.enabled = ENABLE_EMAIL_NOTIFICATIONS
        
        if not self.enabled:
            logger.info("Email notifications are disabled")
            return
        
        # Validate configuration
        if not all([self.smtp_server, self.smtp_port, self.username, self.password]):
            logger.warning("Email configuration incomplete. Email notifications will not work.")
            self.enabled = False
        else:
            logger.info("Email notifier initialized successfully")
    
    def send_email(self, to_emails: List[str], subject: str, body: str,
                  html_body: Optional[str] = None, attachments: List[str] = None) -> bool:
        """
        Send an email notification.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            attachments: List of file paths to attach (optional)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Email notifications are disabled")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add plain text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    self._add_attachment(msg, attachment_path)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(to_emails)} recipients: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add a file attachment to the email."""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.split("/")[-1]}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {file_path}: {e}")
    
    def send_video_generation_notification(self, to_emails: List[str], video_title: str,
                                         status: str, video_id: int, 
                                         error_message: Optional[str] = None) -> bool:
        """
        Send notification about video generation status.
        
        Args:
            to_emails: List of recipient email addresses
            video_title: Title of the video
            status: Generation status (completed, failed, etc.)
            video_id: Database video ID
            error_message: Error message if failed
        
        Returns:
            True if successful, False otherwise
        """
        subject = f"Video Generation {status.title()}: {video_title}"
        
        if status == 'completed':
            body = f"""
Video generation completed successfully!

Title: {video_title}
Video ID: {video_id}
Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your video is ready for review and upload.
"""
            html_body = f"""
<h2>Video Generation Completed Successfully!</h2>
<p><strong>Title:</strong> {video_title}</p>
<p><strong>Video ID:</strong> {video_id}</p>
<p><strong>Completed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<br>
<p>Your video is ready for review and upload.</p>
"""
        elif status == 'failed':
            body = f"""
Video generation failed!

Title: {video_title}
Video ID: {video_id}
Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {error_message or 'Unknown error'}

Please check the logs and try again.
"""
            html_body = f"""
<h2>Video Generation Failed!</h2>
<p><strong>Title:</strong> {video_title}</p>
<p><strong>Video ID:</strong> {video_id}</p>
<p><strong>Failed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Error:</strong> {error_message or 'Unknown error'}</p>
<br>
<p>Please check the logs and try again.</p>
"""
        else:
            body = f"""
Video generation status update:

Title: {video_title}
Video ID: {video_id}
Status: {status}
Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            html_body = f"""
<h2>Video Generation Status Update</h2>
<p><strong>Title:</strong> {video_title}</p>
<p><strong>Video ID:</strong> {video_id}</p>
<p><strong>Status:</strong> {status}</p>
<p><strong>Updated at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        
        return self.send_email(to_emails, subject, body, html_body)
    
    def send_upload_notification(self, to_emails: List[str], video_title: str,
                               platform: str, status: str, video_id: int,
                               platform_video_id: Optional[str] = None,
                               error_message: Optional[str] = None) -> bool:
        """
        Send notification about video upload status.
        
        Args:
            to_emails: List of recipient email addresses
            video_title: Title of the video
            platform: Upload platform (YouTube, Instagram, etc.)
            status: Upload status (completed, failed, etc.)
            video_id: Database video ID
            platform_video_id: Platform-specific video ID if successful
            error_message: Error message if failed
        
        Returns:
            True if successful, False otherwise
        """
        subject = f"Video Upload {status.title()} to {platform}: {video_title}"
        
        if status == 'completed':
            body = f"""
Video upload completed successfully!

Title: {video_title}
Platform: {platform}
Video ID: {video_id}
Platform Video ID: {platform_video_id or 'N/A'}
Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your video is now live on {platform}!
"""
            html_body = f"""
<h2>Video Upload Completed Successfully!</h2>
<p><strong>Title:</strong> {video_title}</p>
<p><strong>Platform:</strong> {platform}</p>
<p><strong>Video ID:</strong> {video_id}</p>
<p><strong>Platform Video ID:</strong> {platform_video_id or 'N/A'}</p>
<p><strong>Completed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<br>
<p>Your video is now live on {platform}!</p>
"""
        elif status == 'failed':
            body = f"""
Video upload failed!

Title: {video_title}
Platform: {platform}
Video ID: {video_id}
Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {error_message or 'Unknown error'}

Please check the logs and try again.
"""
            html_body = f"""
<h2>Video Upload Failed!</h2>
<p><strong>Title:</strong> {video_title}</p>
<p><strong>Platform:</strong> {platform}</p>
<p><strong>Video ID:</strong> {video_id}</p>
<p><strong>Failed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Error:</strong> {error_message or 'Unknown error'}</p>
<br>
<p>Please check the logs and try again.</p>
"""
        else:
            body = f"""
Video upload status update:

Title: {video_title}
Platform: {platform}
Video ID: {video_id}
Status: {status}
Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            html_body = f"""
<h2>Video Upload Status Update</h2>
<p><strong>Title:</strong> {video_title}</p>
<p><strong>Platform:</strong> {platform}</p>
<p><strong>Video ID:</strong> {video_id}</p>
<p><strong>Status:</strong> {status}</p>
<p><strong>Updated at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        
        return self.send_email(to_emails, subject, body, html_body)
    
    def send_system_notification(self, to_emails: List[str], subject: str,
                               message: str, notification_type: str = 'info') -> bool:
        """
        Send a general system notification.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            message: Notification message
            notification_type: Type of notification (info, warning, error)
        
        Returns:
            True if successful, False otherwise
        """
        # Add notification type to subject
        subject = f"[{notification_type.upper()}] {subject}"
        
        body = f"""
System Notification

Type: {notification_type.title()}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}
"""
        
        html_body = f"""
<h2>System Notification</h2>
<p><strong>Type:</strong> {notification_type.title()}</p>
<p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<br>
<p>{message}</p>
"""
        
        return self.send_email(to_emails, subject, body, html_body)
    
    def send_daily_summary(self, to_emails: List[str], summary_data: Dict[str, Any]) -> bool:
        """
        Send a daily summary of video generation and upload activities.
        
        Args:
            to_emails: List of recipient email addresses
            summary_data: Dictionary containing summary information
        
        Returns:
            True if successful, False otherwise
        """
        subject = f"Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Build summary text
        body = f"""
Daily Summary Report

Date: {datetime.now().strftime('%Y-%m-%d')}

Video Generation:
- Total videos: {summary_data.get('total_videos', 0)}
- Completed: {summary_data.get('completed_videos', 0)}
- Failed: {summary_data.get('failed_videos', 0)}
- Pending: {summary_data.get('pending_videos', 0)}

Uploads:
- Total uploads: {summary_data.get('total_uploads', 0)}
- Successful: {summary_data.get('successful_uploads', 0)}
- Failed: {summary_data.get('failed_uploads', 0)}

System Status:
- Active jobs: {summary_data.get('active_jobs', 0)}
- Errors: {summary_data.get('error_count', 0)}
"""
        
        # Build HTML summary
        html_body = f"""
<h2>Daily Summary Report</h2>
<p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
<br>
<h3>Video Generation</h3>
<ul>
<li>Total videos: {summary_data.get('total_videos', 0)}</li>
<li>Completed: {summary_data.get('completed_videos', 0)}</li>
<li>Failed: {summary_data.get('failed_videos', 0)}</li>
<li>Pending: {summary_data.get('pending_videos', 0)}</li>
</ul>
<br>
<h3>Uploads</h3>
<ul>
<li>Total uploads: {summary_data.get('total_uploads', 0)}</li>
<li>Successful: {summary_data.get('successful_uploads', 0)}</li>
<li>Failed: {summary_data.get('failed_uploads', 0)}</li>
</ul>
<br>
<h3>System Status</h3>
<ul>
<li>Active jobs: {summary_data.get('active_jobs', 0)}</li>
<li>Errors: {summary_data.get('error_count', 0)}</li>
</ul>
"""
        
        return self.send_email(to_emails, subject, body, html_body)
    
    def test_connection(self) -> bool:
        """Test SMTP connection and authentication."""
        if not self.enabled:
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False

# Global email notifier instance
email_notifier = EmailNotifier()
