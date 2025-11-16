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
            "version": "2.1",
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
