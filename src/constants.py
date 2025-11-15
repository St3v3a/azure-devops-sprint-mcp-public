"""
Constants and field definitions for Azure DevOps operations.

Defines field sets for optimal query performance and consistent field access.
"""

from typing import List


# ============================================================================
# Field Reference Names
# ============================================================================

class FieldNames:
    """Azure DevOps field reference names."""

    # System fields
    ID = "System.Id"
    REV = "System.Rev"
    AREA_PATH = "System.AreaPath"
    TEAM_PROJECT = "System.TeamProject"
    ITERATION_PATH = "System.IterationPath"
    WORK_ITEM_TYPE = "System.WorkItemType"
    STATE = "System.State"
    REASON = "System.Reason"
    ASSIGNED_TO = "System.AssignedTo"
    CREATED_DATE = "System.CreatedDate"
    CREATED_BY = "System.CreatedBy"
    CHANGED_DATE = "System.ChangedDate"
    CHANGED_BY = "System.ChangedBy"
    COMMENT_COUNT = "System.CommentCount"
    TITLE = "System.Title"
    BOARD_COLUMN = "System.BoardColumn"
    BOARD_COLUMN_DONE = "System.BoardColumnDone"
    DESCRIPTION = "System.Description"
    TAGS = "System.Tags"
    HISTORY = "System.History"
    RELATED_LINK_COUNT = "System.RelatedLinkCount"
    ATTACHED_FILE_COUNT = "System.AttachedFileCount"
    HYPERLINK_COUNT = "System.HyperLinkCount"
    EXTERNAL_LINK_COUNT = "System.ExternalLinkCount"
    REMOTE_LINK_COUNT = "System.RemoteLinkCount"

    # Microsoft.VSTS.Common fields
    STATE_CHANGE_DATE = "Microsoft.VSTS.Common.StateChangeDate"
    ACTIVATED_DATE = "Microsoft.VSTS.Common.ActivatedDate"
    ACTIVATED_BY = "Microsoft.VSTS.Common.ActivatedBy"
    RESOLVED_DATE = "Microsoft.VSTS.Common.ResolvedDate"
    RESOLVED_BY = "Microsoft.VSTS.Common.ResolvedBy"
    RESOLVED_REASON = "Microsoft.VSTS.Common.ResolvedReason"
    CLOSED_DATE = "Microsoft.VSTS.Common.ClosedDate"
    CLOSED_BY = "Microsoft.VSTS.Common.ClosedBy"
    PRIORITY = "Microsoft.VSTS.Common.Priority"
    SEVERITY = "Microsoft.VSTS.Common.Severity"
    VALUE_AREA = "Microsoft.VSTS.Common.ValueArea"
    RISK = "Microsoft.VSTS.Common.Risk"
    STACK_RANK = "Microsoft.VSTS.Common.StackRank"
    TRIAGE = "Microsoft.VSTS.Common.Triage"
    ACCEPTANCE_CRITERIA = "Microsoft.VSTS.Common.AcceptanceCriteria"
    BACKLOG_PRIORITY = "Microsoft.VSTS.Common.BacklogPriority"
    BUSINESS_VALUE = "Microsoft.VSTS.Common.BusinessValue"
    TIME_CRITICALITY = "Microsoft.VSTS.Common.TimeCriticality"
    ACTIVITY = "Microsoft.VSTS.Common.Activity"

    # Microsoft.VSTS.Scheduling fields
    REMAINING_WORK = "Microsoft.VSTS.Scheduling.RemainingWork"
    COMPLETED_WORK = "Microsoft.VSTS.Scheduling.CompletedWork"
    ORIGINAL_ESTIMATE = "Microsoft.VSTS.Scheduling.OriginalEstimate"
    STORY_POINTS = "Microsoft.VSTS.Scheduling.StoryPoints"
    EFFORT = "Microsoft.VSTS.Scheduling.Effort"
    SIZE = "Microsoft.VSTS.Scheduling.Size"
    START_DATE = "Microsoft.VSTS.Scheduling.StartDate"
    FINISH_DATE = "Microsoft.VSTS.Scheduling.FinishDate"
    TARGET_DATE = "Microsoft.VSTS.Scheduling.TargetDate"
    DUE_DATE = "Microsoft.VSTS.Scheduling.DueDate"

    # Microsoft.VSTS.Build fields
    INTEGRATION_BUILD = "Microsoft.VSTS.Build.IntegrationBuild"
    FOUND_IN = "Microsoft.VSTS.Build.FoundIn"

    # Microsoft.VSTS.TCM (Test Case Management) fields
    REPRO_STEPS = "Microsoft.VSTS.TCM.ReproSteps"
    SYSTEM_INFO = "Microsoft.VSTS.TCM.SystemInfo"


# ============================================================================
# Field Sets for Different Query Types
# ============================================================================

# Basic fields for lightweight list queries
BASIC_FIELDS: List[str] = [
    FieldNames.ID,
    FieldNames.TITLE,
    FieldNames.STATE,
    FieldNames.WORK_ITEM_TYPE,
    FieldNames.ASSIGNED_TO,
]

# Detailed fields for individual work item views
DETAILED_FIELDS: List[str] = [
    # Basic fields
    *BASIC_FIELDS,

    # Metadata
    FieldNames.REV,
    FieldNames.CREATED_DATE,
    FieldNames.CREATED_BY,
    FieldNames.CHANGED_DATE,
    FieldNames.CHANGED_BY,
    FieldNames.REASON,

    # Organization
    FieldNames.AREA_PATH,
    FieldNames.ITERATION_PATH,
    FieldNames.TAGS,

    # Content
    FieldNames.DESCRIPTION,

    # Scheduling
    FieldNames.PRIORITY,
    FieldNames.REMAINING_WORK,
    FieldNames.STORY_POINTS,

    # Links
    FieldNames.COMMENT_COUNT,
    FieldNames.RELATED_LINK_COUNT,
    FieldNames.ATTACHED_FILE_COUNT,
]

# Sprint/iteration specific fields
SPRINT_FIELDS: List[str] = [
    # Basic identification
    FieldNames.ID,
    FieldNames.TITLE,
    FieldNames.STATE,
    FieldNames.WORK_ITEM_TYPE,
    FieldNames.ASSIGNED_TO,

    # Sprint tracking
    FieldNames.ITERATION_PATH,
    FieldNames.PRIORITY,
    FieldNames.STACK_RANK,

    # Effort tracking
    FieldNames.REMAINING_WORK,
    FieldNames.COMPLETED_WORK,
    FieldNames.ORIGINAL_ESTIMATE,
    FieldNames.STORY_POINTS,

    # Status dates
    FieldNames.STATE_CHANGE_DATE,
    FieldNames.ACTIVATED_DATE,
    FieldNames.CLOSED_DATE,
]

# Bug-specific fields
BUG_FIELDS: List[str] = [
    # Basic fields
    *BASIC_FIELDS,

    # Bug specific
    FieldNames.SEVERITY,
    FieldNames.PRIORITY,
    FieldNames.FOUND_IN,
    FieldNames.INTEGRATION_BUILD,
    FieldNames.REPRO_STEPS,
    FieldNames.SYSTEM_INFO,

    # Tracking
    FieldNames.ITERATION_PATH,
    FieldNames.AREA_PATH,
    FieldNames.RESOLVED_DATE,
    FieldNames.RESOLVED_BY,
    FieldNames.RESOLVED_REASON,
    FieldNames.CLOSED_DATE,
    FieldNames.CLOSED_BY,
]

# User Story specific fields
USER_STORY_FIELDS: List[str] = [
    # Basic fields
    *BASIC_FIELDS,

    # Story specific
    FieldNames.STORY_POINTS,
    FieldNames.PRIORITY,
    FieldNames.VALUE_AREA,
    FieldNames.RISK,
    FieldNames.BUSINESS_VALUE,
    FieldNames.TIME_CRITICALITY,
    FieldNames.ACCEPTANCE_CRITERIA,

    # Tracking
    FieldNames.ITERATION_PATH,
    FieldNames.AREA_PATH,
    FieldNames.STACK_RANK,
]

# Task specific fields
TASK_FIELDS: List[str] = [
    # Basic fields
    *BASIC_FIELDS,

    # Task specific
    FieldNames.REMAINING_WORK,
    FieldNames.COMPLETED_WORK,
    FieldNames.ORIGINAL_ESTIMATE,
    FieldNames.PRIORITY,

    # Tracking
    FieldNames.ITERATION_PATH,
    FieldNames.AREA_PATH,
    FieldNames.ACTIVITY,
]

# Fields for "my work items" queries
MY_WORK_ITEMS_FIELDS: List[str] = [
    FieldNames.ID,
    FieldNames.TITLE,
    FieldNames.STATE,
    FieldNames.WORK_ITEM_TYPE,
    FieldNames.ASSIGNED_TO,
    FieldNames.ITERATION_PATH,
    FieldNames.PRIORITY,
    FieldNames.CHANGED_DATE,
    FieldNames.REMAINING_WORK,
]


# ============================================================================
# Query Limits
# ============================================================================

class QueryLimits:
    """Default limits for different query types."""

    # General queries
    DEFAULT_LIMIT = 100

    # Sprint queries (can be larger)
    SPRINT_LIMIT = 500

    # Maximum allowed by Azure DevOps API
    MAX_LIMIT = 20000

    # Batch size for work item retrieval
    BATCH_SIZE = 200


# ============================================================================
# Expand Options
# ============================================================================

class ExpandOptions:
    """Work item expand options for Azure DevOps API."""

    NONE = "None"
    RELATIONS = "Relations"
    FIELDS = "Fields"
    LINKS = "Links"
    ALL = "All"


# ============================================================================
# Common States
# ============================================================================

class WorkItemStates:
    """Common work item states across different process templates."""

    # Universal states
    NEW = "New"
    ACTIVE = "Active"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REMOVED = "Removed"

    # Agile/Scrum states
    DONE = "Done"
    IN_PROGRESS = "In Progress"
    COMMITTED = "Committed"
    IN_REVIEW = "In Review"
    COMPLETED = "Completed"

    # CMMI states
    PROPOSED = "Proposed"
    APPROVED = "Approved"

    # Completed states (for sprint calculations)
    COMPLETED_STATES = {DONE, CLOSED, RESOLVED, COMPLETED}

    # In progress states (for sprint calculations)
    IN_PROGRESS_STATES = {ACTIVE, IN_PROGRESS, COMMITTED, IN_REVIEW}


# ============================================================================
# Link Types
# ============================================================================

class LinkTypes:
    """Work item link types."""

    # Hierarchy
    HIERARCHY_FORWARD = "System.LinkTypes.Hierarchy-Forward"
    HIERARCHY_REVERSE = "System.LinkTypes.Hierarchy-Reverse"
    PARENT = "System.LinkTypes.Parent"
    CHILD = "System.LinkTypes.Child"

    # Dependencies
    DEPENDENCY_FORWARD = "System.LinkTypes.Dependency-Forward"
    DEPENDENCY_REVERSE = "System.LinkTypes.Dependency-Reverse"
    SUCCESSOR = "System.LinkTypes.Successor"
    PREDECESSOR = "System.LinkTypes.Predecessor"

    # Other relationships
    RELATED = "System.LinkTypes.Related"
    DUPLICATE_FORWARD = "System.LinkTypes.Duplicate-Forward"
    DUPLICATE_REVERSE = "System.LinkTypes.Duplicate-Reverse"
    AFFECTS = "System.LinkTypes.Affects"
    AFFECTED_BY = "System.LinkTypes.AffectedBy"


# ============================================================================
# Priority and Severity Values
# ============================================================================

class Priority:
    """Work item priority values (1 is highest)."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class Severity:
    """Bug severity values (1 is most severe)."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


# ============================================================================
# Helper Functions
# ============================================================================

def get_fields_for_work_item_type(work_item_type: str) -> List[str]:
    """
    Get optimal field set for a specific work item type.

    Args:
        work_item_type: The work item type (Bug, User Story, Task, etc.)

    Returns:
        List of field names optimized for that work item type
    """
    work_item_type_upper = work_item_type.upper()

    if "BUG" in work_item_type_upper:
        return BUG_FIELDS
    elif "USER STORY" in work_item_type_upper or "PRODUCT BACKLOG ITEM" in work_item_type_upper:
        return USER_STORY_FIELDS
    elif "TASK" in work_item_type_upper:
        return TASK_FIELDS
    else:
        return DETAILED_FIELDS


def fields_to_string(fields: List[str]) -> str:
    """
    Convert field list to comma-separated string for Azure DevOps API.

    Args:
        fields: List of field names

    Returns:
        Comma-separated field names
    """
    return ','.join(fields)


def format_wiql_fields(fields: List[str]) -> str:
    """
    Format field list for WIQL SELECT clause.

    Args:
        fields: List of field names

    Returns:
        Formatted field list for WIQL (e.g., "[System.Id], [System.Title]")
    """
    return ', '.join(f'[{field}]' for field in fields)
