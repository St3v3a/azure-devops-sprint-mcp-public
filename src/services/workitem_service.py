"""
Work Item service for Azure DevOps operations
Handles CRUD operations for work items
"""
from typing import List, Dict, Any, Optional
from azure.devops.v7_1.work_item_tracking.models import (
    JsonPatchOperation,
    Wiql,
    CommentCreate
)
from azure.devops.v7_1.work.models import TeamContext
from datetime import datetime

from ..validation import (
    validate_state,
    validate_work_item_type,
    validate_field_name,
    validate_field_value,
    validate_wiql,
    validate_iteration_path,
    validate_priority,
    sanitize_wiql_string,
    ValidationError
)
from ..decorators import azure_devops_operation, validate_work_item_id
from ..constants import (
    MY_WORK_ITEMS_FIELDS,
    DETAILED_FIELDS,
    QueryLimits,
    ExpandOptions,
    LinkTypes,
    format_wiql_fields,
    fields_to_string
)
from ..cache import CachedService


class WorkItemService(CachedService):
    """Service for work item operations with caching support"""

    def __init__(self, auth, project: str):
        """
        Initialize work item service

        Args:
            auth: AzureDevOpsAuth instance
            project: Azure DevOps project name
        """
        # Initialize caching with namespace
        super().__init__(cache_namespace=f"workitems:{project}", cache_ttl=300)

        self.auth = auth
        self.project = project
        self._wit_client = None
    
    @property
    def wit_client(self):
        """Lazy load work item tracking client"""
        if not self._wit_client:
            self._wit_client = self.auth.get_client('work_item_tracking')
        return self._wit_client
    
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_my_work_items(
        self,
        state: Optional[str] = None,
        work_item_type: Optional[str] = None,
        limit: int = QueryLimits.DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Get work items assigned to the current user

        Args:
            state: Optional state filter
            work_item_type: Optional work item type filter
            limit: Maximum number of work items to return (default: 100)

        Returns:
            List of work items

        Raises:
            ValidationError: If state or work_item_type is invalid
        """
        # Validate inputs
        if state:
            state = validate_state(state)

        if work_item_type:
            work_item_type = validate_work_item_type(work_item_type)

        # Ensure limit doesn't exceed maximum
        limit = min(limit, QueryLimits.MAX_LIMIT)

        # Build WIQL query - simplified to avoid field specification issues
        wiql_query = f"""SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
FROM WorkItems
WHERE [System.TeamProject] = '{self.project}'
AND [System.AssignedTo] = @Me"""

        if state:
            wiql_query += f" AND [System.State] = '{state}'"

        if work_item_type:
            wiql_query += f" AND [System.WorkItemType] = '{work_item_type}'"

        wiql_query += " ORDER BY [System.ChangedDate] DESC"

        # Validate WIQL query
        validate_wiql(wiql_query)

        # Execute query with team context
        wiql = Wiql(query=wiql_query)
        team_context = TeamContext(project=self.project)
        query_result = self.wit_client.query_by_wiql(wiql, team_context=team_context)

        if not query_result.work_items:
            return []

        # Get work item IDs
        ids = [item.id for item in query_result.work_items]

        # Fetch work items with all fields
        work_items = self.wit_client.get_work_items(
            ids=ids,
            expand='All'
        )

        # Format response
        return [self._format_work_item(wi) for wi in work_items]
    
    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_work_item(
        self,
        work_item_id: int,
        include_comments: bool = True,
        expand: str = ExpandOptions.RELATIONS
    ) -> Dict[str, Any]:
        """
        Get full details of a specific work item

        Args:
            work_item_id: Work item ID
            include_comments: Whether to load comments (default: True)
            expand: Expand option (None, Relations, Fields, Links, All)

        Returns:
            Work item details
        """
        # Try to get from cache
        cache_key_parts = (work_item_id, include_comments, expand)
        cached_result = self._get_cached('work_item', *cache_key_parts)
        if cached_result is not None:
            return cached_result

        # Note: Cannot use both fields and expand parameters together
        # Using expand to get all data including relations
        work_item = self.wit_client.get_work_item(
            id=work_item_id,
            expand=expand
        )
        
        # Get comments only if requested
        comments = []
        if include_comments:
            try:
                comments_result = self.wit_client.get_comments(
                    project=self.project,
                    work_item_id=work_item_id
                )
                comments = [
                    {
                        'id': c.id,
                        'text': c.text,
                        'created_date': c.created_date.isoformat() if c.created_date else None,
                        'created_by': c.created_by.display_name if c.created_by else None
                    }
                    for c in (comments_result.comments or [])
                ]
            except Exception:
                pass  # Comments might not be available

        result = self._format_work_item(work_item)
        result['comments'] = comments

        # Cache the result
        self._set_cached(result, 'work_item', *cache_key_parts)

        return result
    
    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def update_work_item(
        self,
        work_item_id: int,
        fields: Dict[str, Any],
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a work item

        Args:
            work_item_id: Work item ID
            fields: Dictionary of fields to update
            comment: Optional comment to add

        Returns:
            Updated work item

        Raises:
            ValidationError: If field names are invalid
        """
        # Build patch document
        patch_document = []

        for field_name, value in fields.items():
            # Validate field name
            validate_field_name(field_name)

            # Validate field value (type checking, XSS prevention, etc.)
            validated_value = validate_field_value(field_name, value)

            # Ensure field name has proper format
            if not field_name.startswith('/fields/'):
                field_path = f'/fields/{field_name}'
            else:
                field_path = field_name

            patch_document.append(
                JsonPatchOperation(
                    op='add',
                    path=field_path,
                    value=validated_value
                )
            )
        
        # Update work item
        updated_item = self.wit_client.update_work_item(
            document=patch_document,
            id=work_item_id,
            project=self.project
        )
        
        # Add comment if provided
        if comment:
            await self.add_comment(work_item_id, comment)

        # Invalidate cache for this work item
        self._invalidate_cached('work_item', work_item_id)

        return self._format_work_item(updated_item)
    
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def create_work_item(
        self,
        title: str,
        work_item_type: str,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        iteration_path: Optional[str] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new work item

        Args:
            title: Work item title
            work_item_type: Type (Task, Bug, User Story, etc.)
            description: Optional description
            assigned_to: Optional assignee email
            iteration_path: Optional sprint/iteration
            priority: Optional priority (1-4)

        Returns:
            Created work item

        Raises:
            ValidationError: If work_item_type, iteration_path, or priority is invalid
        """
        # Validate inputs
        work_item_type = validate_work_item_type(work_item_type)

        if iteration_path:
            iteration_path = validate_iteration_path(iteration_path, self.project)

        if priority is not None:
            priority = validate_priority(priority)

        # Build patch document
        patch_document = [
            JsonPatchOperation(
                op='add',
                path='/fields/System.Title',
                value=title
            )
        ]

        if description:
            patch_document.append(
                JsonPatchOperation(
                    op='add',
                    path='/fields/System.Description',
                    value=description
                )
            )

        if assigned_to:
            patch_document.append(
                JsonPatchOperation(
                    op='add',
                    path='/fields/System.AssignedTo',
                    value=assigned_to
                )
            )

        if iteration_path:
            patch_document.append(
                JsonPatchOperation(
                    op='add',
                    path='/fields/System.IterationPath',
                    value=iteration_path
                )
            )

        if priority:
            patch_document.append(
                JsonPatchOperation(
                    op='add',
                    path='/fields/Microsoft.VSTS.Common.Priority',
                    value=priority
                )
            )
        
        # Create work item
        created_item = self.wit_client.create_work_item(
            document=patch_document,
            project=self.project,
            type=work_item_type
        )

        # Invalidate my work items cache (list changed)
        self._invalidate_cached('my_work_items')

        return self._format_work_item(created_item)
    
    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def add_comment(
        self,
        work_item_id: int,
        comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to a work item

        Args:
            work_item_id: Work item ID
            comment: Comment text

        Returns:
            Comment details
        """
        comment_create = CommentCreate(text=comment)
        
        result = self.wit_client.add_comment(
            project=self.project,
            work_item_id=work_item_id,
            request=comment_create
        )
        
        return {
            'id': result.id,
            'text': result.text,
            'created_date': result.created_date.isoformat() if result.created_date else None,
            'created_by': result.created_by.display_name if result.created_by else None
        }
    
    async def _batch_get_work_items(
        self,
        ids: List[int],
        fields: Optional[List[str]] = None,
        expand: str = ExpandOptions.NONE
    ) -> List[Any]:
        """
        Fetch work items in batches respecting Azure DevOps batch size limit.

        Args:
            ids: List of work item IDs
            fields: Fields to retrieve (defaults to DETAILED_FIELDS)
            expand: Expand option

        Returns:
            List of work items

        Raises:
            QueryTooLargeError: If more than MAX_LIMIT IDs requested
        """
        from ..errors import QueryTooLargeError

        if len(ids) > QueryLimits.MAX_LIMIT:
            raise QueryTooLargeError(
                result_count=len(ids),
                max_results=QueryLimits.MAX_LIMIT
            )

        # Use default fields if not specified
        if fields is None:
            fields = DETAILED_FIELDS

        all_items = []

        # Batch process in chunks of BATCH_SIZE (200)
        for i in range(0, len(ids), QueryLimits.BATCH_SIZE):
            batch_ids = ids[i:i + QueryLimits.BATCH_SIZE]

            batch_items = self.wit_client.get_work_items(
                ids=batch_ids,
                fields=fields_to_string(fields),
                expand=expand
            )

            all_items.extend(batch_items)

        return all_items

    @azure_devops_operation(timeout_seconds=60, max_retries=3)
    async def get_work_item_hierarchy(
        self,
        work_item_id: int,
        link_type: str = LinkTypes.HIERARCHY_FORWARD,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Get work item with hierarchical children or parents.

        Args:
            work_item_id: Root work item ID
            link_type: Link type to follow (default: Hierarchy-Forward for children)
            max_depth: Maximum depth to traverse (default: 5)

        Returns:
            Dictionary with work item and hierarchical structure

        Example:
            # Get Epic with all child Features, Stories, Tasks
            hierarchy = await service.get_work_item_hierarchy(
                work_item_id=123,
                link_type=LinkTypes.HIERARCHY_FORWARD
            )
        """
        from ..validation import validate_link_type

        # Validate link type
        validate_link_type(link_type)

        # Build WIQL query for hierarchical links
        wiql_query = f"""
        SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
        FROM WorkItemLinks
        WHERE ([Source].[System.Id] = {work_item_id})
          AND ([System.Links.LinkType] = '{link_type}')
          AND ([Target].[System.TeamProject] = '{self.project}')
        MODE (Recursive)
        """

        # Validate WIQL
        validate_wiql(wiql_query)

        # Execute query
        from azure.devops.v7_1.work_item_tracking.models import Wiql
        wiql = Wiql(query=wiql_query)
        query_result = self.wit_client.query_by_wiql(wiql, project=self.project)

        # Extract work item links
        work_item_relations = query_result.work_item_relations or []

        if not work_item_relations:
            # No children/parents found, return just the root item
            root_item = await self.get_work_item(work_item_id, include_comments=False)
            return {
                'root': root_item,
                'children': [],
                'total_count': 1
            }

        # Collect all unique work item IDs
        all_ids = set()
        for relation in work_item_relations:
            if relation.source:
                all_ids.add(relation.source.id)
            if relation.target:
                all_ids.add(relation.target.id)

        # Fetch all work items
        work_items_list = await self._batch_get_work_items(
            list(all_ids),
            fields=DETAILED_FIELDS,
            expand=ExpandOptions.NONE
        )

        # Create lookup dictionary
        work_items_dict = {wi.id: self._format_work_item(wi) for wi in work_items_list}

        # Build hierarchy tree
        hierarchy_tree = self._build_hierarchy_tree(
            work_item_relations,
            work_items_dict,
            work_item_id,
            max_depth
        )

        return {
            'root': work_items_dict.get(work_item_id, {}),
            'children': hierarchy_tree,
            'total_count': len(all_ids),
            'link_type': link_type
        }

    def _build_hierarchy_tree(
        self,
        relations: List[Any],
        work_items_dict: Dict[int, Dict[str, Any]],
        root_id: int,
        max_depth: int,
        current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Recursively build hierarchy tree from work item relations.

        Args:
            relations: List of work item relations
            work_items_dict: Dictionary of work items by ID
            root_id: Current root ID
            max_depth: Maximum depth to traverse
            current_depth: Current depth in tree

        Returns:
            List of child work items with their children
        """
        if current_depth >= max_depth:
            return []

        children = []

        for relation in relations:
            if relation.source and relation.source.id == root_id and relation.target:
                child_id = relation.target.id
                child_item = work_items_dict.get(child_id)

                if child_item:
                    # Recursively get children of this child
                    child_item_with_children = child_item.copy()
                    child_item_with_children['children'] = self._build_hierarchy_tree(
                        relations,
                        work_items_dict,
                        child_id,
                        max_depth,
                        current_depth + 1
                    )
                    children.append(child_item_with_children)

        return children

    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def search_work_items(
        self,
        search_text: str,
        field: str = "System.Title",
        work_item_type: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = QueryLimits.DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Search work items using indexed full-text search (Contains Words).

        Uses Azure DevOps indexed search for better performance than Contains.

        Args:
            search_text: Text to search for
            field: Field to search in (default: System.Title)
            work_item_type: Optional work item type filter
            state: Optional state filter
            limit: Maximum results (default: 100)

        Returns:
            List of matching work items
        """
        from ..validation import validate_field_name

        # Validate inputs
        validate_field_name(field)

        if work_item_type:
            work_item_type = validate_work_item_type(work_item_type)

        if state:
            state = validate_state(state)

        # Ensure limit doesn't exceed maximum
        limit = min(limit, QueryLimits.MAX_LIMIT)

        # Sanitize search text to prevent WIQL injection
        search_text_safe = sanitize_wiql_string(search_text)

        # Build WIQL query with Contains Words (indexed search)
        wiql_query = f"""
        SELECT TOP {limit} {format_wiql_fields(MY_WORK_ITEMS_FIELDS)}
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.project}'
          AND [{field}] Contains Words '{search_text_safe}'
        """

        if work_item_type:
            wiql_query += f" AND [System.WorkItemType] = '{work_item_type}'"

        if state:
            wiql_query += f" AND [System.State] = '{state}'"

        wiql_query += " ORDER BY [System.ChangedDate] DESC"

        # Validate WIQL
        validate_wiql(wiql_query)

        # Execute query
        from azure.devops.v7_1.work_item_tracking.models import Wiql
        wiql = Wiql(query=wiql_query)
        query_result = self.wit_client.query_by_wiql(wiql)

        if not query_result.work_items:
            return []

        # Get work item IDs
        ids = [item.id for item in query_result.work_items]

        # Fetch work items
        work_items = await self._batch_get_work_items(
            ids,
            fields=MY_WORK_ITEMS_FIELDS,
            expand=ExpandOptions.NONE
        )

        return [self._format_work_item(wi) for wi in work_items]

    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_historical_work_items(
        self,
        historical_state: str,
        work_item_type: Optional[str] = None,
        limit: int = QueryLimits.DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Find work items that were ever in a specific state (historical query).

        Useful for tracking regressions, finding resolved bugs, etc.

        Args:
            historical_state: State to check for in history (e.g., "Resolved")
            work_item_type: Optional work item type filter
            limit: Maximum results (default: 100)

        Returns:
            List of work items that were ever in the specified state

        Example:
            # Find all bugs that were ever resolved (for regression tracking)
            bugs = await service.get_historical_work_items(
                historical_state="Resolved",
                work_item_type="Bug"
            )
        """
        # Validate inputs
        historical_state = validate_state(historical_state)

        if work_item_type:
            work_item_type = validate_work_item_type(work_item_type)

        # Ensure limit doesn't exceed maximum
        limit = min(limit, QueryLimits.MAX_LIMIT)

        # Build WIQL query with "Was Ever" operator
        wiql_query = f"""
        SELECT TOP {limit} {format_wiql_fields(MY_WORK_ITEMS_FIELDS)}
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.project}'
          AND [System.State] Was Ever '{historical_state}'
        """

        if work_item_type:
            wiql_query += f" AND [System.WorkItemType] = '{work_item_type}'"

        wiql_query += " ORDER BY [System.ChangedDate] DESC"

        # Validate WIQL
        validate_wiql(wiql_query)

        # Execute query
        from azure.devops.v7_1.work_item_tracking.models import Wiql
        wiql = Wiql(query=wiql_query)
        query_result = self.wit_client.query_by_wiql(wiql)

        if not query_result.work_items:
            return []

        # Get work item IDs
        ids = [item.id for item in query_result.work_items]

        # Fetch work items
        work_items = await self._batch_get_work_items(
            ids,
            fields=MY_WORK_ITEMS_FIELDS,
            expand=ExpandOptions.NONE
        )

        return [self._format_work_item(wi) for wi in work_items]

    def _format_work_item(self, wi) -> Dict[str, Any]:
        """Format work item for response"""
        fields = wi.fields or {}
        
        return {
            'id': wi.id,
            'rev': wi.rev,
            'title': fields.get('System.Title'),
            'state': fields.get('System.State'),
            'work_item_type': fields.get('System.WorkItemType'),
            'assigned_to': self._format_identity(fields.get('System.AssignedTo')),
            'created_date': self._format_date(fields.get('System.CreatedDate')),
            'changed_date': self._format_date(fields.get('System.ChangedDate')),
            'iteration_path': fields.get('System.IterationPath'),
            'area_path': fields.get('System.AreaPath'),
            'priority': fields.get('Microsoft.VSTS.Common.Priority'),
            'remaining_work': fields.get('Microsoft.VSTS.Scheduling.RemainingWork'),
            'description': fields.get('System.Description'),
            'reason': fields.get('System.Reason'),
            'url': wi.url
        }
    
    @staticmethod
    def _format_identity(identity) -> Optional[str]:
        """Format identity field"""
        if not identity:
            return None
        if isinstance(identity, dict):
            return identity.get('displayName') or identity.get('uniqueName')
        return str(identity)
    
    @staticmethod
    def _format_date(date) -> Optional[str]:
        """Format date field"""
        if not date:
            return None
        if isinstance(date, datetime):
            return date.isoformat()
        return str(date)
