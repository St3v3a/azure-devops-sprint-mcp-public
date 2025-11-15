"""
Data models for Azure DevOps Sprint MCP Server
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class WorkItem:
    """Represents an Azure DevOps work item"""
    id: int
    title: str
    state: str
    work_item_type: str
    assigned_to: Optional[str] = None
    priority: Optional[int] = None
    remaining_work: Optional[float] = None
    iteration_path: Optional[str] = None
    description: Optional[str] = None
    created_date: Optional[datetime] = None
    changed_date: Optional[datetime] = None
    url: Optional[str] = None


@dataclass
class Sprint:
    """Represents a sprint/iteration"""
    id: str
    name: str
    path: str
    start_date: Optional[datetime] = None
    finish_date: Optional[datetime] = None
    time_frame: Optional[str] = None


@dataclass
class WorkItemUpdate:
    """Represents a work item update operation"""
    work_item_id: int
    fields: Dict[str, Any]
    comment: Optional[str] = None


@dataclass
class SprintSummary:
    """Represents a sprint summary with statistics"""
    sprint_name: str
    iteration_path: str
    total_items: int
    completed_items: int
    in_progress_items: int
    not_started_items: int
    completion_percentage: float
    work_items: List[WorkItem]
