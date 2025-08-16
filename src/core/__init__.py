"""
Core module for the Automated Video Generator
Contains the main workflow controller and orchestration logic
"""

from .workflow_controller import WorkflowController, start_workflow, stop_workflow, get_workflow_status

__all__ = [
    'WorkflowController',
    'start_workflow', 
    'stop_workflow', 
    'get_workflow_status'
]
