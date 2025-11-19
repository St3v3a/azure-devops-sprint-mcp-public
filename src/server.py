"""
Azure DevOps Sprint Board MCP Server
Focused MCP server for managing sprint boards and work items in Azure DevOps
"""
from fastmcp import FastMCP, Context
from typing import Optional, List, Dict, Any
import os
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from .auth import AzureDevOpsAuth
from .service_manager import ServiceManager
from .models import WorkItem, Sprint, WorkItemUpdate
from .cache import close_global_cache


# Global state for authentication and service manager
# Initialized during lifespan startup
_auth = None
_service_manager = None


@asynccontextmanager
async def lifespan(app):
    """Initialize services on startup"""
    global _auth, _service_manager

    # Load environment variables from .env file
    load_dotenv()

    # Get configuration from environment
    org_url = os.getenv("AZURE_DEVOPS_ORG_URL")
    default_project = os.getenv("AZURE_DEVOPS_PROJECT")  # Optional default

    if not org_url:
        raise ValueError(
            "Missing required environment variable: AZURE_DEVOPS_ORG_URL"
        )

    # Initialize authentication
    _auth = AzureDevOpsAuth(org_url)
    await _auth.initialize()

    # Initialize service manager with optional default project
    _service_manager = ServiceManager(_auth, default_project=default_project)

    yield  # Server runs

    # Cleanup on shutdown
    await _auth.close()
    await close_global_cache()


# Initialize FastMCP server with lifespan
mcp = FastMCP(
    name="Azure DevOps Sprint Manager",
    lifespan=lifespan
)


# ============================================================================
# TOOLS (Actions that modify state or retrieve data)
# ============================================================================

@mcp.tool()
async def get_my_work_items(
    project: Optional[str] = None,
    state: Optional[str] = None,
    work_item_type: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get all work items assigned to the current user.

    Args:
        project: Azure DevOps project name. If None, uses default project.
        state: Optional filter by state (e.g., "Active", "New", "Resolved")
        work_item_type: Optional filter by type (e.g., "Task", "Bug", "User Story")

    Returns:
        List of work items with id, title, state, type, and assigned to
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching work items assigned to you from project: {workitem_service.project}...")

    items = await workitem_service.get_my_work_items(
        state=state,
        work_item_type=work_item_type
    )

    await ctx.info(f"Found {len(items)} work items")
    return items


@mcp.tool()
async def get_sprint_work_items(
    project: Optional[str] = None,
    iteration_path: Optional[str] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get work items for a specific sprint/iteration.

    Args:
        project: Azure DevOps project name. If None, uses default project.
        iteration_path: Sprint iteration path (e.g., "Sprint 1").
                       If None, gets current sprint.
        team_name: Team name. If None, uses default team.

    Returns:
        Dictionary with sprint details and work items
    """
    sprint_service = _service_manager.get_sprint_service(project)

    if iteration_path:
        await ctx.info(f"Fetching work items for sprint: {iteration_path} in project: {sprint_service.project}")
    else:
        await ctx.info(f"Fetching work items for current sprint in project: {sprint_service.project}...")

    result = await sprint_service.get_sprint_work_items(
        iteration_path=iteration_path,
        team_name=team_name
    )

    await ctx.info(
        f"Sprint '{result['sprint_name']}' has {result['total_items']} work items"
    )
    return result


@mcp.tool()
async def update_work_item(
    work_item_id: int,
    fields: Dict[str, Any],
    project: Optional[str] = None,
    comment: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Update a work item's fields.

    Args:
        work_item_id: ID of the work item to update
        fields: Dictionary of fields to update. Common fields:
            - "System.State": Work item state (e.g., "Active", "Resolved")
            - "System.AssignedTo": Assigned user email
            - "Microsoft.VSTS.Common.Priority": Priority (1-4)
            - "Microsoft.VSTS.Scheduling.RemainingWork": Remaining hours
            - "System.Title": Work item title
            - "System.Description": Work item description
        project: Azure DevOps project name. If None, uses default project.
        comment: Optional comment to add with the update

    Returns:
        Updated work item details
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Updating work item {work_item_id} in project: {workitem_service.project}...")

    result = await workitem_service.update_work_item(
        work_item_id=work_item_id,
        fields=fields,
        comment=comment
    )

    await ctx.info(f"Successfully updated work item {work_item_id}")
    return result


@mcp.tool()
async def add_comment(
    work_item_id: int,
    comment: str,
    project: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add a comment to a work item.

    Args:
        work_item_id: ID of the work item
        comment: Comment text to add
        project: Azure DevOps project name. If None, uses default project.

    Returns:
        Comment details including ID and creation time
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Adding comment to work item {work_item_id} in project: {workitem_service.project}...")

    result = await workitem_service.add_comment(work_item_id, comment)

    await ctx.info("Comment added successfully")
    return result


@mcp.tool()
async def create_work_item(
    title: str,
    work_item_type: str,
    project: Optional[str] = None,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    iteration_path: Optional[str] = None,
    priority: Optional[int] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a new work item.

    Args:
        title: Work item title
        work_item_type: Type of work item (e.g., "Task", "Bug", "User Story")
        project: Azure DevOps project name. If None, uses default project.
        description: Optional description
        assigned_to: Optional user email to assign to
        iteration_path: Optional sprint/iteration path
        priority: Optional priority (1-4, where 1 is highest)

    Returns:
        Created work item details including ID
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Creating new {work_item_type} in project: {workitem_service.project}: {title}")

    result = await workitem_service.create_work_item(
        title=title,
        work_item_type=work_item_type,
        description=description,
        assigned_to=assigned_to,
        iteration_path=iteration_path,
        priority=priority
    )

    await ctx.info(f"Created work item {result['id']}")
    return result


@mcp.tool()
async def move_to_sprint(
    work_item_id: int,
    iteration_path: str,
    project: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Move a work item to a different sprint/iteration.

    Args:
        work_item_id: ID of the work item to move
        iteration_path: Target sprint iteration path (e.g., "Sprint 2")
        project: Azure DevOps project name. If None, uses default project.

    Returns:
        Updated work item details
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Moving work item {work_item_id} to sprint: {iteration_path} in project: {workitem_service.project}")

    result = await workitem_service.update_work_item(
        work_item_id=work_item_id,
        fields={"System.IterationPath": iteration_path}
    )

    await ctx.info("Work item moved successfully")
    return result


@mcp.tool()
async def get_work_item_details(
    work_item_id: int,
    project: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get full details of a specific work item.

    Args:
        work_item_id: ID of the work item
        project: Azure DevOps project name. If None, uses default project.

    Returns:
        Complete work item details including all fields and relations
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching details for work item {work_item_id} from project: {workitem_service.project}...")

    result = await workitem_service.get_work_item(work_item_id)

    return result


@mcp.tool()
async def get_team_iterations(
    project: Optional[str] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get list of available sprints/iterations for a team.

    Args:
        project: Azure DevOps project name. If None, uses default project.
        team_name: Optional team name. If None, uses default team.

    Returns:
        List of iterations with name, path, start date, and end date
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Fetching team iterations from project: {sprint_service.project}...")

    iterations = await sprint_service.get_team_iterations(team_name)

    await ctx.info(f"Found {len(iterations)} iterations")
    return iterations


@mcp.tool()
async def get_current_sprint(
    project: Optional[str] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get details about the current active sprint.

    Args:
        project: Azure DevOps project name. If None, uses default project.
        team_name: Optional team name. If None, uses default team.

    Returns:
        Current sprint details including dates and work items summary
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Fetching current sprint information from project: {sprint_service.project}...")

    result = await sprint_service.get_current_sprint(team_name)

    await ctx.info(f"Current sprint: {result['name']}")
    return result


@mcp.tool()
async def get_work_item_hierarchy(
    work_item_id: int,
    project: Optional[str] = None,
    link_type: str = "System.LinkTypes.Hierarchy-Forward",
    max_depth: int = 5,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get work item with hierarchical children or parents.

    Retrieves a work item and its hierarchical relationships (children or parents)
    up to a specified depth. Useful for viewing Epic > Feature > Story > Task hierarchies.

    Args:
        work_item_id: Root work item ID to get hierarchy from
        project: Azure DevOps project name. If None, uses default project.
        link_type: Link type to follow. Common values:
            - "System.LinkTypes.Hierarchy-Forward" (default): Get children
            - "System.LinkTypes.Hierarchy-Reverse": Get parents
        max_depth: Maximum depth to traverse (default: 5, max: 10)

    Returns:
        Dictionary with root work item, hierarchical children/parents, and total count
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching hierarchy for work item {work_item_id} from project: {workitem_service.project}...")

    # Cap max_depth at 10 to prevent excessive queries
    max_depth = min(max_depth, 10)

    result = await workitem_service.get_work_item_hierarchy(
        work_item_id=work_item_id,
        link_type=link_type,
        max_depth=max_depth
    )

    await ctx.info(f"Found {result['total_count']} work items in hierarchy")
    return result


@mcp.tool()
async def search_work_items(
    search_text: str,
    project: Optional[str] = None,
    field: str = "System.Title",
    work_item_type: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 100,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Search work items using indexed full-text search.

    Uses Azure DevOps indexed search (Contains Words) for fast, efficient searching.

    Args:
        search_text: Text to search for
        project: Azure DevOps project name. If None, uses default project.
        field: Field to search in (default: "System.Title"). Other options:
            - "System.Description"
            - "System.Tags"
        work_item_type: Optional filter by type (e.g., "Task", "Bug", "User Story")
        state: Optional filter by state (e.g., "Active", "New", "Resolved")
        limit: Maximum number of results to return (default: 100, max: 1000)

    Returns:
        List of matching work items
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Searching for '{search_text}' in {field} from project: {workitem_service.project}...")

    results = await workitem_service.search_work_items(
        search_text=search_text,
        field=field,
        work_item_type=work_item_type,
        state=state,
        limit=limit
    )

    await ctx.info(f"Found {len(results)} matching work items")
    return results


@mcp.tool()
async def get_historical_work_items(
    historical_state: str,
    project: Optional[str] = None,
    work_item_type: Optional[str] = None,
    limit: int = 100,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Find work items that were ever in a specific state (historical query).

    Uses Azure DevOps "Was Ever" operator to find items that were previously
    in a state, even if they're not in that state now. Useful for tracking
    regressions, finding resolved bugs that reopened, etc.

    Args:
        historical_state: State to check for in history (e.g., "Resolved", "Closed")
        project: Azure DevOps project name. If None, uses default project.
        work_item_type: Optional filter by type (e.g., "Bug", "Task")
        limit: Maximum number of results to return (default: 100, max: 1000)

    Returns:
        List of work items that were ever in the specified state

    Example use cases:
        - Find bugs that were resolved (to check for regressions)
        - Find tasks that were blocked at some point
        - Track items that went through specific workflow states
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Searching for items that were ever '{historical_state}' in project: {workitem_service.project}...")

    results = await workitem_service.get_historical_work_items(
        historical_state=historical_state,
        work_item_type=work_item_type,
        limit=limit
    )

    await ctx.info(f"Found {len(results)} work items")
    return results


@mcp.tool()
async def link_work_items(
    source_id: int,
    target_id: int,
    link_type: str = "System.LinkTypes.Related",
    project: Optional[str] = None,
    comment: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a link between two work items.

    Establishes a relationship between work items such as parent-child,
    related, or dependency relationships.

    Args:
        source_id: Source work item ID
        target_id: Target work item ID to link to
        link_type: Type of link to create. Common values:
            - "System.LinkTypes.Related" (default): Related items
            - "System.LinkTypes.Hierarchy-Forward": Parent to Child
            - "System.LinkTypes.Hierarchy-Reverse": Child to Parent
            - "System.LinkTypes.Dependency-Forward": Predecessor to Successor
            - "System.LinkTypes.Dependency-Reverse": Successor to Predecessor
        project: Azure DevOps project name. If None, uses default project.
        comment: Optional comment for the link

    Returns:
        Updated source work item

    Example uses:
        - Link Epic to Feature (parent-child)
        - Link related user stories
        - Create task dependencies
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(
        f"Linking work item {source_id} to {target_id} "
        f"with {link_type} in project: {workitem_service.project}..."
    )

    result = await workitem_service.add_work_item_link(
        source_id=source_id,
        target_id=target_id,
        link_type=link_type,
        comment=comment
    )

    await ctx.info(f"Successfully linked work items")
    return result


@mcp.tool()
async def unlink_work_items(
    source_id: int,
    target_id: int,
    project: Optional[str] = None,
    link_type: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Remove a link between two work items.

    Args:
        source_id: Source work item ID
        target_id: Target work item ID to unlink from
        project: Azure DevOps project name. If None, uses default project.
        link_type: Optional link type to remove. If None, removes first matching link.

    Returns:
        Updated source work item
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(
        f"Unlinking work item {source_id} from {target_id} "
        f"in project: {workitem_service.project}..."
    )

    result = await workitem_service.remove_work_item_link(
        source_id=source_id,
        target_id=target_id,
        link_type=link_type
    )

    await ctx.info(f"Successfully unlinked work items")
    return result


@mcp.tool()
async def get_linked_work_items(
    work_item_id: int,
    project: Optional[str] = None,
    link_type: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get all work items linked to a specific work item.

    Returns work items that are linked via any relationship type,
    with information about the link type.

    Args:
        work_item_id: Work item ID to get links from
        project: Azure DevOps project name. If None, uses default project.
        link_type: Optional filter by link type. If None, returns all linked items.

    Returns:
        List of linked work items with link_type and optional link_comment fields

    Example uses:
        - Get all children of an Epic
        - Find related user stories
        - See task dependencies
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching linked work items for {work_item_id} from project: {workitem_service.project}...")

    results = await workitem_service.get_linked_work_items(
        work_item_id=work_item_id,
        link_type=link_type
    )

    await ctx.info(f"Found {len(results)} linked work items")
    return results


@mcp.tool()
async def batch_update_work_items(
    updates: List[Dict[str, Any]],
    project: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Update multiple work items in a single operation.

    Efficiently updates many work items at once. Each update can modify different
    fields and optionally include a comment.

    Args:
        updates: List of update dictionaries, each containing:
            - id: Work item ID (required)
            - fields: Dictionary of fields to update (required)
            - comment: Optional comment to add
        project: Azure DevOps project name. If None, uses default project.

    Returns:
        List of updated work items (includes success/error status for each)

    Example:
        updates = [
            {"id": 123, "fields": {"System.State": "Active"}},
            {"id": 124, "fields": {"System.State": "Resolved"}, "comment": "Fixed"}
        ]

    Note: Maximum 200 items per batch
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Batch updating {len(updates)} work items in project: {workitem_service.project}...")

    results = await workitem_service.batch_update_work_items(updates)

    successful = sum(1 for r in results if r.get('success', True))
    await ctx.info(f"Successfully updated {successful}/{len(results)} work items")
    return results


@mcp.tool()
async def create_child_work_items(
    parent_id: int,
    children: List[Dict[str, Any]],
    project: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Create multiple child work items under a parent.

    Efficiently creates multiple child work items and automatically links them
    to the parent with hierarchical relationships. Great for breaking down
    Epics into Features, Features into Stories, or Stories into Tasks.

    Args:
        parent_id: Parent work item ID
        children: List of child specs, each containing:
            - title: Work item title (required)
            - work_item_type: Type (required, e.g., "Task", "Bug", "User Story")
            - description: Optional description
            - assigned_to: Optional assignee email
            - priority: Optional priority (1-4)
            - iteration_path: Optional sprint
        project: Azure DevOps project name. If None, uses default project.

    Returns:
        List of created child work items with parent_id field

    Example:
        children = [
            {"title": "Implement login", "work_item_type": "Task"},
            {"title": "Add validation", "work_item_type": "Task", "assigned_to": "dev@example.com"}
        ]

    Note: Maximum 50 children per batch
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(
        f"Creating {len(children)} child work items under parent {parent_id} "
        f"in project: {workitem_service.project}..."
    )

    results = await workitem_service.create_child_work_items(
        parent_id=parent_id,
        children=children
    )

    successful = sum(1 for r in results if r.get('success', False))
    await ctx.info(f"Successfully created {successful}/{len(children)} child work items")
    return results


@mcp.tool()
async def list_work_item_revisions(
    work_item_id: int,
    project: Optional[str] = None,
    top: Optional[int] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get historical revisions of a work item.

    Shows complete audit trail of changes - who changed what and when.
    Useful for tracking work item history and understanding changes over time.

    Args:
        work_item_id: Work item ID
        project: Azure DevOps project name. If None, uses default project.
        top: Optional limit on number of revisions to return

    Returns:
        List of revisions ordered by revision number (newest first)
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching revisions for work item {work_item_id} from project: {workitem_service.project}...")

    results = await workitem_service.get_work_item_revisions(
        work_item_id=work_item_id,
        top=top
    )

    await ctx.info(f"Found {len(results)} revisions")
    return results


@mcp.tool()
async def list_work_item_comments(
    work_item_id: int,
    project: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get comments for a work item with pagination support.

    Retrieves comments with full pagination control. Useful for
    work items with many comments.

    Args:
        work_item_id: Work item ID
        project: Azure DevOps project name. If None, uses default project.
        top: Optional limit on number of comments to return
        skip: Optional number of comments to skip (for pagination)

    Returns:
        List of comments ordered by creation date (newest first)
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching comments for work item {work_item_id} from project: {workitem_service.project}...")

    results = await workitem_service.get_work_item_comments(
        work_item_id=work_item_id,
        top=top,
        skip=skip
    )

    await ctx.info(f"Found {len(results)} comments")
    return results


@mcp.tool()
async def get_work_item_type(
    work_item_type_name: str,
    project: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get work item type definition and metadata.

    Retrieves the schema/definition for a work item type including
    available fields, states, and field requirements. Useful for understanding
    what fields are available and required for a specific work item type.

    Args:
        work_item_type_name: Work item type name (e.g., "Task", "Bug", "User Story")
        project: Azure DevOps project name. If None, uses default project.

    Returns:
        Work item type definition with fields, states, and metadata
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching work item type definition for '{work_item_type_name}' from project: {workitem_service.project}...")

    result = await workitem_service.get_work_item_type(work_item_type_name)

    await ctx.info(f"Retrieved definition with {len(result.get('states', []))} states and {len(result.get('field_instances', []))} fields")
    return result


@mcp.tool()
async def get_query(
    query_id: str,
    project: Optional[str] = None,
    depth: int = 1,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get a saved WIQL query definition.

    Retrieves a saved query by ID or path. Useful for understanding
    what queries are available and their WIQL definitions.

    Args:
        query_id: Query ID (GUID) or path (e.g., "My Queries/Active Bugs")
        project: Azure DevOps project name. If None, uses default project.
        depth: Query tree depth (1=query only, 2=query+children folders)

    Returns:
        Query definition with WIQL, metadata, and folder information
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Fetching query '{query_id}' from project: {workitem_service.project}...")

    result = await workitem_service.get_query(
        query_id=query_id,
        depth=depth
    )

    await ctx.info(f"Retrieved query: {result['name']}")
    return result


@mcp.tool()
async def execute_query_by_id(
    query_id: str,
    project: Optional[str] = None,
    limit: int = 100,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Execute a saved query and return matching work items.

    Runs a saved WIQL query and returns the results. Useful for
    running pre-defined queries that users have saved in Azure DevOps.

    Args:
        query_id: Query ID (GUID) or path (e.g., "Shared Queries/Sprint Backlog")
        project: Azure DevOps project name. If None, uses default project.
        limit: Maximum number of results to return (default: 100, max: 1000)

    Returns:
        List of work items matching the query

    Example paths:
        - "My Queries/Active Work Items"
        - "Shared Queries/Current Sprint"
        - Query GUID like "12345678-1234-1234-1234-123456789012"
    """
    workitem_service = _service_manager.get_workitem_service(project)
    await ctx.info(f"Executing query '{query_id}' from project: {workitem_service.project}...")

    results = await workitem_service.execute_query_by_id(
        query_id=query_id,
        limit=limit
    )

    await ctx.info(f"Query returned {len(results)} work items")
    return results


@mcp.tool()
async def list_backlogs(
    project: Optional[str] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get backlog levels for a team.

    Returns available backlog levels (Stories, Features, Epics) and their
    associated work item types. Useful for understanding team backlog structure.

    Args:
        project: Azure DevOps project name. If None, uses default project.
        team_name: Optional team name. If None, uses default team.

    Returns:
        List of backlog levels with metadata and work item types
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Fetching backlogs from project: {sprint_service.project}...")

    results = await sprint_service.get_backlogs(team_name)

    await ctx.info(f"Found {len(results)} backlog levels")
    return results


@mcp.tool()
async def list_backlog_work_items(
    backlog_id: str,
    project: Optional[str] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get work items from a specific backlog level.

    Retrieves all work items from a particular backlog category
    (e.g., all Features, all User Stories).

    Args:
        backlog_id: Backlog ID (e.g., "Microsoft.RequirementCategory" for Stories,
                    "Microsoft.FeatureCategory" for Features,
                    "Microsoft.EpicCategory" for Epics)
        project: Azure DevOps project name. If None, uses default project.
        team_name: Optional team name. If None, uses default team.

    Returns:
        List of work items in the specified backlog level
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Fetching backlog items for '{backlog_id}' from project: {sprint_service.project}...")

    results = await sprint_service.get_backlog_work_items(
        backlog_id=backlog_id,
        team_name=team_name
    )

    await ctx.info(f"Found {len(results)} backlog work items")
    return results


@mcp.tool()
async def create_iteration(
    name: str,
    project: Optional[str] = None,
    start_date: Optional[str] = None,
    finish_date: Optional[str] = None,
    path: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a new iteration/sprint.

    Args:
        name: Iteration name (e.g., "Sprint 15")
        project: Azure DevOps project name. If None, uses default project.
        start_date: Optional start date (ISO format: YYYY-MM-DD)
        finish_date: Optional finish date (ISO format: YYYY-MM-DD)
        path: Optional parent path (e.g., "ProjectName\\Iteration" or None for root)

    Returns:
        Created iteration details with ID, name, path, and dates
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Creating iteration '{name}' in project: {sprint_service.project}...")

    result = await sprint_service.create_iteration(
        name=name,
        start_date=start_date,
        finish_date=finish_date,
        path=path
    )

    await ctx.info(f"Created iteration: {result['name']}")
    return result


@mcp.tool()
async def assign_iteration_to_team(
    iteration_id: str,
    project: Optional[str] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Assign an iteration/sprint to a team.

    Makes an iteration available for a team to use in their sprint planning.

    Args:
        iteration_id: Iteration ID (GUID)
        project: Azure DevOps project name. If None, uses default project.
        team_name: Optional team name. If None, uses default team.

    Returns:
        Team iteration details
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Assigning iteration {iteration_id} to team in project: {sprint_service.project}...")

    result = await sprint_service.assign_iteration_to_team(
        iteration_id=iteration_id,
        team_name=team_name
    )

    await ctx.info(f"Assigned iteration: {result['name']}")
    return result


@mcp.tool()
async def get_team_capacity(
    iteration_id: str,
    project: Optional[str] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    Get team member capacity for an iteration.

    Returns capacity planning information for all team members in a sprint,
    including their activities, capacity per day, and days off.

    Args:
        iteration_id: Iteration ID (GUID)
        project: Azure DevOps project name. If None, uses default project.
        team_name: Optional team name. If None, uses default team.

    Returns:
        List of team member capacities with activities and days off
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Fetching team capacity for iteration {iteration_id} from project: {sprint_service.project}...")

    results = await sprint_service.get_team_capacity(
        iteration_id=iteration_id,
        team_name=team_name
    )

    await ctx.info(f"Found capacity info for {len(results)} team members")
    return results


@mcp.tool()
async def update_team_capacity(
    iteration_id: str,
    team_member_id: str,
    activities: List[Dict[str, Any]],
    project: Optional[str] = None,
    days_off: Optional[List[Dict[str, str]]] = None,
    team_name: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Update team member capacity for an iteration.

    Sets capacity planning information for a team member including their
    activities and days off.

    Args:
        iteration_id: Iteration ID (GUID)
        team_member_id: Team member ID (GUID)
        activities: List of activities with 'name' and 'capacity_per_day' keys
        project: Azure DevOps project name. If None, uses default project.
        days_off: Optional list of days off with 'start' and 'end' date keys (ISO format)
        team_name: Optional team name. If None, uses default team.

    Returns:
        Updated capacity details

    Example activities:
        [{"name": "Development", "capacity_per_day": 6}]

    Example days_off:
        [{"start": "2025-01-15", "end": "2025-01-17"}]
    """
    sprint_service = _service_manager.get_sprint_service(project)
    await ctx.info(f"Updating team capacity for member {team_member_id} in project: {sprint_service.project}...")

    result = await sprint_service.update_team_capacity(
        iteration_id=iteration_id,
        team_member_id=team_member_id,
        activities=activities,
        days_off=days_off,
        team_name=team_name
    )

    await ctx.info(f"Updated capacity for team member")
    return result


# ============================================================================
# RESOURCES (Read-only data exposure)
# ============================================================================

@mcp.resource("sprint://current")
async def current_sprint_resource(ctx: Context = None) -> str:
    """Provides overview of the current sprint (uses default project)"""
    sprint_service = _service_manager.get_sprint_service()
    sprint = await sprint_service.get_current_sprint()

    return f"""# Current Sprint: {sprint['name']}
**Project:** {sprint_service.project}

**Period:** {sprint['start_date']} to {sprint['end_date']}
**Days Remaining:** {sprint['days_remaining']}

## Work Items Summary
- Total Items: {sprint['total_items']}
- Completed: {sprint['completed_items']}
- In Progress: {sprint['in_progress_items']}
- Not Started: {sprint['not_started_items']}

## Progress
{sprint['completion_percentage']:.1f}% complete
"""


@mcp.resource("sprint://{iteration_path}")
async def sprint_resource(iteration_path: str, ctx: Context = None) -> str:
    """Provides details about a specific sprint (uses default project)"""
    sprint_service = _service_manager.get_sprint_service()
    result = await sprint_service.get_sprint_work_items(iteration_path=iteration_path)

    items_by_state = {}
    for item in result['work_items']:
        state = item['state']
        items_by_state[state] = items_by_state.get(state, 0) + 1

    items_list = "\n".join([
        f"- [{item['id']}] {item['title']} ({item['state']})"
        for item in result['work_items'][:20]  # Limit to first 20
    ])

    return f"""# Sprint: {result['sprint_name']}
**Project:** {sprint_service.project}

**Iteration Path:** {iteration_path}

## Work Items by State
{chr(10).join([f"- {state}: {count}" for state, count in items_by_state.items()])}

## Work Items (showing first 20)
{items_list}
"""


@mcp.resource("workitem://{work_item_id}")
async def workitem_resource(work_item_id: str, ctx: Context = None) -> str:
    """Provides full details about a specific work item (uses default project)"""
    workitem_service = _service_manager.get_workitem_service()
    wi = await workitem_service.get_work_item(int(work_item_id))

    return f"""# [{wi['id']}] {wi['title']}
**Project:** {workitem_service.project}

**Type:** {wi['work_item_type']}
**State:** {wi['state']}
**Assigned To:** {wi.get('assigned_to', 'Unassigned')}
**Priority:** {wi.get('priority', 'Not set')}

## Details
**Created:** {wi['created_date']}
**Updated:** {wi['changed_date']}
**Iteration:** {wi.get('iteration_path', 'Not set')}

## Description
{wi.get('description', 'No description')}

## Recent Comments
{chr(10).join([f"- [{c['created_date']}] {c['text']}" for c in wi.get('comments', [])[:5]])}
"""


# ============================================================================
# MONITORING TOOLS (Health and Statistics)
# ============================================================================

@mcp.tool()
async def health_check(ctx: Context = None) -> Dict[str, Any]:
    """
    Get server health status for monitoring.

    Returns server health, authentication status, and version information.
    Useful for Docker health checks and monitoring systems.

    Returns:
        Dictionary with health status, authentication info, and version
    """
    try:
        # Verify auth is still valid
        auth = _auth
        auth_info = auth.get_auth_info() if auth else None
        auth_failure_stats = auth.get_auth_failure_stats() if auth else {}

        return {
            "status": "healthy",
            "service": "Azure DevOps Sprint Manager",
            "version": "3.0",
            "authenticated": auth_info.get("authenticated") if auth_info else False,
            "auth_method": auth_info.get("method") if auth_info else None,
            "organization": auth_info.get("organization_url") if auth_info else None,
            "auth_failure_stats": auth_failure_stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@mcp.tool()
async def get_service_statistics(ctx: Context = None) -> Dict[str, Any]:
    """
    Get service manager statistics and multi-project metrics.

    Returns detailed statistics about service usage, cache performance,
    and loaded projects. Useful for monitoring and optimization.

    Returns:
        Dictionary with service manager stats and loaded projects
    """
    try:
        if not _service_manager:
            return {"error": "Service manager not initialized"}

        stats = _service_manager.get_statistics()
        loaded_projects = _service_manager.get_loaded_projects()

        return {
            "service_manager": stats,
            "loaded_projects": loaded_projects,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


# Entry point for running the server
if __name__ == "__main__":
    # Support both STDIO and HTTP transports via configuration
    transport_mode = os.getenv("MCP_TRANSPORT", "http").lower()

    if transport_mode == "stdio":
        # STDIO mode for Claude Desktop direct connection
        import sys
        print("Starting MCP server in STDIO mode", file=sys.stderr)
        print("Server ready for JSON-RPC messages on stdin/stdout", file=sys.stderr)
        mcp.run()  # Default transport is stdio
    else:
        # HTTP mode (default) for web-based clients
        import uvicorn
        port = int(os.getenv("PORT", 8000))

        print(f"Starting MCP server with HTTP streaming on port {port}")
        print(f"Server URL: http://localhost:{port}/mcp")
        print(f"Health check: Use 'health_check' tool")
        print(f"Statistics:   Use 'get_service_statistics' tool")

        # Use modern Streamable HTTP transport (not deprecated SSE)
        mcp.run(transport="streamable-http", port=port, host="0.0.0.0")
