"""
Sprint/Iteration service for Azure DevOps operations
Handles sprint board and iteration management
"""
import sys
from typing import List, Dict, Any, Optional
from azure.devops.v7_1.work_item_tracking.models import Wiql
from azure.devops.v7_1.work.models import TeamContext
from datetime import datetime, timezone

from ..validation import (
    validate_iteration_path,
    validate_wiql,
    ValidationError
)
from ..decorators import azure_devops_operation
from ..constants import (
    SPRINT_FIELDS,
    QueryLimits,
    ExpandOptions,
    WorkItemStates,
    format_wiql_fields,
    fields_to_string
)
from ..cache import CachedService


class SprintService(CachedService):
    """Service for sprint/iteration operations with caching support"""

    def __init__(self, auth, project: str):
        """
        Initialize sprint service

        Args:
            auth: AzureDevOpsAuth instance
            project: Azure DevOps project name
        """
        # Initialize caching with namespace
        super().__init__(cache_namespace=f"sprints:{project}", cache_ttl=300)

        self.auth = auth
        self.project = project
        self._work_client = None
        self._core_client = None
        self._wit_client = None
    
    @property
    def work_client(self):
        """Lazy load work client"""
        if not self._work_client:
            self._work_client = self.auth.get_client('work')
        return self._work_client
    
    @property
    def core_client(self):
        """Lazy load core client"""
        if not self._core_client:
            self._core_client = self.auth.get_client('core')
        return self._core_client
    
    @property
    def wit_client(self):
        """Lazy load work item tracking client"""
        if not self._wit_client:
            self._wit_client = self.auth.get_client('work_item_tracking')
        return self._wit_client
    
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_team_iterations(
        self,
        team_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of iterations for a team

        Args:
            team_name: Team name, or None for default team

        Returns:
            List of iterations
        """
        team = await self._get_team(team_name)
        
        iterations = self.work_client.get_team_iterations(
            team_context=team
        )
        
        return [
            {
                'id': iteration.id,
                'name': iteration.name,
                'path': iteration.path,
                'start_date': iteration.attributes.start_date.isoformat() 
                    if iteration.attributes and iteration.attributes.start_date else None,
                'finish_date': iteration.attributes.finish_date.isoformat() 
                    if iteration.attributes and iteration.attributes.finish_date else None,
                'time_frame': iteration.attributes.time_frame 
                    if iteration.attributes else None
            }
            for iteration in iterations
        ]
    
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_current_sprint(
        self,
        team_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the current active sprint

        Args:
            team_name: Team name, or None for default team

        Returns:
            Current sprint details
        """
        team = await self._get_team(team_name)
        
        # Get current iteration
        iterations = self.work_client.get_team_iterations(
            team_context=team,
            timeframe='current'
        )
        
        if not iterations:
            raise ValueError("No current iteration found")
        
        current_iteration = iterations[0]
        
        # Get work items for this iteration
        work_items_result = await self.get_sprint_work_items(
            iteration_path=current_iteration.path,
            team_name=team_name
        )
        
        # Calculate days remaining
        days_remaining = None
        if current_iteration.attributes and current_iteration.attributes.finish_date:
            finish_date = current_iteration.attributes.finish_date
            now = datetime.now(timezone.utc)
            if finish_date > now:
                days_remaining = (finish_date - now).days
        
        return {
            'id': current_iteration.id,
            'name': current_iteration.name,
            'path': current_iteration.path,
            'start_date': current_iteration.attributes.start_date.isoformat()
                if current_iteration.attributes and current_iteration.attributes.start_date else None,
            'end_date': current_iteration.attributes.finish_date.isoformat()
                if current_iteration.attributes and current_iteration.attributes.finish_date else None,
            'days_remaining': days_remaining,
            'total_items': work_items_result['total_items'],
            'completed_items': work_items_result['completed_items'],
            'in_progress_items': work_items_result['in_progress_items'],
            'not_started_items': work_items_result['not_started_items'],
            'completion_percentage': work_items_result['completion_percentage']
        }
    
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_sprint_work_items(
        self,
        iteration_path: Optional[str] = None,
        team_name: Optional[str] = None,
        limit: int = QueryLimits.SPRINT_LIMIT
    ) -> Dict[str, Any]:
        """
        Get work items for a sprint

        Args:
            iteration_path: Sprint iteration path, or None for current
            team_name: Team name, or None for default team
            limit: Maximum number of work items to return (default: 500)

        Returns:
            Sprint details with work items

        Raises:
            ValidationError: If iteration_path is invalid
        """
        # If no iteration path, get current
        if not iteration_path:
            current = await self.get_current_sprint(team_name)
            iteration_path = current['path']

        # Validate and normalize iteration path
        iteration_path = validate_iteration_path(iteration_path, self.project)

        # Ensure limit doesn't exceed maximum
        limit = min(limit, QueryLimits.MAX_LIMIT)

        # Try to get from cache
        cache_key_parts = ('sprint_work_items', iteration_path, limit)
        cached_result = self._get_cached(*cache_key_parts)
        if cached_result is not None:
            return cached_result

        # Build WIQL query with TOP clause and optimized field selection
        # Order by priority first (most selective), then creation date
        # Use a simpler query with just basic fields
        # Note: FROM WorkItems is case-sensitive in Azure DevOps WIQL
        wiql_query = f"""SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
FROM WorkItems
WHERE [System.IterationPath] = '{iteration_path}'
AND [System.TeamProject] = '{self.project}'
ORDER BY [System.CreatedDate] DESC"""

        # Validate WIQL query
        validate_wiql(wiql_query)

        # Execute query with team context
        wiql = Wiql(query=wiql_query)

        # Pass team_context to specify the project
        team_context = TeamContext(project=self.project)
        query_result = self.wit_client.query_by_wiql(wiql, team_context=team_context)

        work_items = []
        if query_result.work_items:
            # Get work item IDs
            ids = [item.id for item in query_result.work_items]

            # Fetch work items with expand='All' to get all fields
            work_items_full = self.wit_client.get_work_items(
                ids=ids,
                expand='All'
            )

            work_items = [
                self._format_work_item(wi) for wi in work_items_full
            ]

        # Calculate statistics
        total_items = len(work_items)

        # Use constants for state matching
        completed_states = WorkItemStates.COMPLETED_STATES
        in_progress_states = WorkItemStates.IN_PROGRESS_STATES
        
        completed_items = sum(
            1 for wi in work_items 
            if wi['state'] in completed_states
        )
        
        in_progress_items = sum(
            1 for wi in work_items 
            if wi['state'] in in_progress_states
        )
        
        not_started_items = total_items - completed_items - in_progress_items
        
        completion_percentage = (
            (completed_items / total_items * 100) if total_items > 0 else 0
        )
        
        # Extract sprint name from path
        sprint_name = iteration_path.split('\\')[-1]

        result = {
            'sprint_name': sprint_name,
            'iteration_path': iteration_path,
            'total_items': total_items,
            'completed_items': completed_items,
            'in_progress_items': in_progress_items,
            'not_started_items': not_started_items,
            'completion_percentage': completion_percentage,
            'work_items': work_items
        }

        # Cache the result
        self._set_cached(result, *cache_key_parts)

        return result
    
    async def _get_team(self, team_name: Optional[str] = None):
        """
        Get team context

        Args:
            team_name: Team name, or None for default team

        Returns:
            Team context object
        """
        if not team_name:
            # Get default team (first team in project)
            teams = self.core_client.get_teams(self.project)
            if not teams:
                raise ValueError(f"No teams found in project {self.project}")
            team_name = teams[0].name

        return TeamContext(project=self.project, team=team_name)
    
    @staticmethod
    def _format_work_item(wi) -> Dict[str, Any]:
        """Format work item for response"""
        fields = wi.fields or {}
        
        # Format assigned to
        assigned_to = fields.get('System.AssignedTo')
        if assigned_to and isinstance(assigned_to, dict):
            assigned_to = assigned_to.get('displayName') or assigned_to.get('uniqueName')
        
        return {
            'id': wi.id,
            'title': fields.get('System.Title'),
            'state': fields.get('System.State'),
            'work_item_type': fields.get('System.WorkItemType'),
            'assigned_to': str(assigned_to) if assigned_to else None,
            'priority': fields.get('Microsoft.VSTS.Common.Priority'),
            'remaining_work': fields.get('Microsoft.VSTS.Scheduling.RemainingWork'),
            'url': wi.url
        }
