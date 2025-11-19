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

        # Fetch work items with optimized field selection (70% smaller than expand='All')
        work_items = self.wit_client.get_work_items(
            ids=ids,
            fields=fields_to_string(MY_WORK_ITEMS_FIELDS)
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

    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def add_work_item_link(
        self,
        source_id: int,
        target_id: int,
        link_type: str = LinkTypes.RELATED,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a link between two work items.

        Args:
            source_id: Source work item ID
            target_id: Target work item ID
            link_type: Type of link to create. Options from LinkTypes:
                - HIERARCHY_FORWARD: Parent->Child
                - HIERARCHY_REVERSE: Child->Parent
                - RELATED: Related link
                - DEPENDENCY_FORWARD: Predecessor->Successor
                - DEPENDENCY_REVERSE: Successor->Predecessor
            comment: Optional comment for the link

        Returns:
            Updated source work item

        Raises:
            ValidationError: If link type is invalid
            WorkItemNotFoundError: If source or target doesn't exist
        """
        from ..validation import validate_link_type

        # Validate link type
        validate_link_type(link_type)

        # Validate target exists
        _ = await self.get_work_item(target_id, include_comments=False)

        # Build patch document
        patches = [
            JsonPatchOperation(
                op="add",
                path="/relations/-",
                value={
                    "rel": link_type,
                    "url": f"{self.auth.organization_url}/{self.project}/_apis/wit/workItems/{target_id}",
                    "attributes": {
                        "comment": comment
                    } if comment else {}
                }
            )
        ]

        # Update work item
        updated_wi = self.wit_client.update_work_item(
            document=patches,
            id=source_id,
            project=self.project
        )

        # Invalidate cache
        self.invalidate_cache(source_id)

        return self._format_work_item(updated_wi)

    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def remove_work_item_link(
        self,
        source_id: int,
        target_id: int,
        link_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove a link between two work items.

        Args:
            source_id: Source work item ID
            target_id: Target work item ID
            link_type: Optional link type to remove. If None, removes all link types.

        Returns:
            Updated source work item

        Raises:
            WorkItemNotFoundError: If source doesn't exist or link not found
        """
        from ..validation import validate_link_type

        if link_type:
            validate_link_type(link_type)

        # Get current work item with relations
        source_wi = self.wit_client.get_work_item(
            id=source_id,
            expand=ExpandOptions.RELATIONS
        )

        if not source_wi.relations:
            from ..errors import WorkItemNotFoundError
            raise WorkItemNotFoundError(f"Work item {source_id} has no relations")

        # Find the relation index to remove
        relation_index = None
        for idx, relation in enumerate(source_wi.relations):
            if relation.url and str(target_id) in relation.url:
                if link_type is None or relation.rel == link_type:
                    relation_index = idx
                    break

        if relation_index is None:
            from ..errors import WorkItemNotFoundError
            raise WorkItemNotFoundError(
                f"Link from {source_id} to {target_id} "
                f"{'with type ' + link_type if link_type else ''} not found"
            )

        # Build patch document to remove relation
        patches = [
            JsonPatchOperation(
                op="remove",
                path=f"/relations/{relation_index}"
            )
        ]

        # Update work item
        updated_wi = self.wit_client.update_work_item(
            document=patches,
            id=source_id,
            project=self.project
        )

        # Invalidate cache
        self.invalidate_cache(source_id)

        return self._format_work_item(updated_wi)

    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_linked_work_items(
        self,
        work_item_id: int,
        link_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get work items linked to a specific work item.

        Args:
            work_item_id: Work item ID to get links from
            link_type: Optional filter by link type

        Returns:
            List of linked work items with link type information

        Raises:
            WorkItemNotFoundError: If work item doesn't exist
        """
        from ..validation import validate_link_type

        if link_type:
            validate_link_type(link_type)

        # Get work item with relations
        wi = self.wit_client.get_work_item(
            id=work_item_id,
            expand=ExpandOptions.RELATIONS
        )

        if not wi.relations:
            return []

        # Filter relations to work item links only (not attachments, hyperlinks, etc.)
        linked_items = []
        linked_ids = []

        for relation in wi.relations:
            # Filter by link type if specified
            if link_type and relation.rel != link_type:
                continue

            # Extract work item ID from URL
            if relation.url and '/workItems/' in relation.url:
                try:
                    linked_id = int(relation.url.split('/workItems/')[-1])
                    linked_ids.append(linked_id)
                    linked_items.append({
                        'id': linked_id,
                        'link_type': relation.rel,
                        'comment': relation.attributes.get('comment') if relation.attributes else None
                    })
                except (ValueError, IndexError):
                    continue

        if not linked_ids:
            return []

        # Fetch full details of linked work items
        work_items = await self._batch_get_work_items(
            linked_ids,
            fields=MY_WORK_ITEMS_FIELDS,
            expand=ExpandOptions.NONE
        )

        # Merge link info with work item details
        wi_dict = {wi.id: self._format_work_item(wi) for wi in work_items}

        result = []
        for link_info in linked_items:
            if link_info['id'] in wi_dict:
                item = wi_dict[link_info['id']].copy()
                item['link_type'] = link_info['link_type']
                if link_info['comment']:
                    item['link_comment'] = link_info['comment']
                result.append(item)

        return result

    @azure_devops_operation(timeout_seconds=60, max_retries=3)
    async def batch_update_work_items(
        self,
        updates: List[Dict[str, Any]],
        max_batch_size: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Update multiple work items in a single operation.

        Args:
            updates: List of update dictionaries, each containing:
                - id: Work item ID (required)
                - fields: Dictionary of fields to update (required)
                - comment: Optional comment
            max_batch_size: Maximum number of items per batch (default: 200)

        Returns:
            List of updated work items

        Raises:
            ValidationError: If batch size exceeds maximum or updates are invalid

        Example:
            updates = [
                {"id": 123, "fields": {"System.State": "Active"}},
                {"id": 124, "fields": {"System.State": "Active"}, "comment": "Updated"}
            ]
            results = await service.batch_update_work_items(updates)
        """
        from ..validation import ValidationError

        if not updates:
            return []

        if len(updates) > max_batch_size:
            raise ValidationError(
                f"Batch size {len(updates)} exceeds maximum {max_batch_size}"
            )

        # Validate all updates have required fields
        for idx, update in enumerate(updates):
            if 'id' not in update:
                raise ValidationError(f"Update at index {idx} missing 'id' field")
            if 'fields' not in update:
                raise ValidationError(f"Update at index {idx} missing 'fields' field")

        # Process each update
        results = []
        for update in updates:
            work_item_id = update['id']
            fields = update['fields']
            comment = update.get('comment')

            # Use existing update method
            try:
                result = await self.update_work_item(
                    work_item_id=work_item_id,
                    fields=fields,
                    comment=comment
                )
                results.append(result)
            except Exception as e:
                # Include error in results
                results.append({
                    'id': work_item_id,
                    'error': str(e),
                    'success': False
                })

        return results

    @azure_devops_operation(timeout_seconds=60, max_retries=3)
    async def create_child_work_items(
        self,
        parent_id: int,
        children: List[Dict[str, Any]],
        max_batch_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Create multiple child work items under a parent in a single operation.

        Automatically creates hierarchical links (parent-child) for each created item.

        Args:
            parent_id: Parent work item ID
            children: List of child work item specs, each containing:
                - title: Work item title (required)
                - work_item_type: Type (required, e.g., "Task", "Bug")
                - description: Optional description
                - assigned_to: Optional assignee email
                - priority: Optional priority (1-4)
                - iteration_path: Optional sprint
            max_batch_size: Maximum number of children per batch (default: 50)

        Returns:
            List of created child work items with link information

        Raises:
            ValidationError: If batch size exceeds maximum or children are invalid
            WorkItemNotFoundError: If parent doesn't exist

        Example:
            children = [
                {"title": "Task 1", "work_item_type": "Task"},
                {"title": "Task 2", "work_item_type": "Task", "assigned_to": "user@example.com"}
            ]
            results = await service.create_child_work_items(parent_id=123, children=children)
        """
        from ..validation import ValidationError

        if not children:
            return []

        if len(children) > max_batch_size:
            raise ValidationError(
                f"Batch size {len(children)} exceeds maximum {max_batch_size}"
            )

        # Validate parent exists
        _ = await self.get_work_item(parent_id, include_comments=False)

        # Validate all children have required fields
        for idx, child in enumerate(children):
            if 'title' not in child:
                raise ValidationError(f"Child at index {idx} missing 'title' field")
            if 'work_item_type' not in child:
                raise ValidationError(f"Child at index {idx} missing 'work_item_type' field")

        # Create each child work item
        results = []
        for child in children:
            try:
                # Create the child work item
                created = await self.create_work_item(
                    title=child['title'],
                    work_item_type=child['work_item_type'],
                    description=child.get('description'),
                    assigned_to=child.get('assigned_to'),
                    iteration_path=child.get('iteration_path'),
                    priority=child.get('priority')
                )

                # Link child to parent
                await self.add_work_item_link(
                    source_id=parent_id,
                    target_id=created['id'],
                    link_type=LinkTypes.HIERARCHY_FORWARD,
                    comment=f"Auto-linked during batch child creation"
                )

                # Add parent_id to result for reference
                created['parent_id'] = parent_id
                created['success'] = True
                results.append(created)

            except Exception as e:
                # Include error in results
                results.append({
                    'title': child['title'],
                    'error': str(e),
                    'success': False
                })

        return results

    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_work_item_revisions(
        self,
        work_item_id: int,
        top: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical revisions of a work item.

        Shows who changed what and when for full audit trail.

        Args:
            work_item_id: Work item ID
            top: Optional limit on number of revisions to return

        Returns:
            List of revisions ordered by revision number (newest first)

        Raises:
            WorkItemNotFoundError: If work item doesn't exist
        """
        # Get all revisions
        revisions = self.wit_client.get_revisions(
            id=work_item_id,
            project=self.project,
            top=top
        )

        # Format revisions
        result = []
        for rev in revisions:
            fields = rev.fields or {}
            result.append({
                'id': rev.id,
                'rev': rev.rev,
                'changed_by': self._format_identity(fields.get('System.ChangedBy')),
                'changed_date': self._format_date(fields.get('System.ChangedDate')),
                'state': fields.get('System.State'),
                'title': fields.get('System.Title'),
                'work_item_type': fields.get('System.WorkItemType'),
                'assigned_to': self._format_identity(fields.get('System.AssignedTo')),
                'iteration_path': fields.get('System.IterationPath'),
                'reason': fields.get('System.Reason')
            })

        return result

    @validate_work_item_id
    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_work_item_comments(
        self,
        work_item_id: int,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get comments for a work item with pagination support.

        Args:
            work_item_id: Work item ID
            top: Optional limit on number of comments to return
            skip: Optional number of comments to skip (for pagination)

        Returns:
            List of comments ordered by creation date (newest first)

        Raises:
            WorkItemNotFoundError: If work item doesn't exist
        """
        # Get comments
        comments_response = self.wit_client.get_comments(
            project=self.project,
            work_item_id=work_item_id,
            top=top,
            skip=skip
        )

        # Format comments
        result = []
        for comment in comments_response.comments:
            result.append({
                'id': comment.id,
                'text': comment.text,
                'created_by': self._format_identity(comment.created_by) if hasattr(comment, 'created_by') else None,
                'created_date': self._format_date(comment.created_date) if hasattr(comment, 'created_date') else None,
                'modified_by': self._format_identity(comment.modified_by) if hasattr(comment, 'modified_by') else None,
                'modified_date': self._format_date(comment.modified_date) if hasattr(comment, 'modified_date') else None
            })

        return result

    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_work_item_type(
        self,
        work_item_type_name: str
    ) -> Dict[str, Any]:
        """
        Get work item type definition and metadata.

        Retrieves the schema/definition for a work item type including
        available fields, states, and transitions.

        Args:
            work_item_type_name: Work item type name (e.g., "Task", "Bug", "User Story")

        Returns:
            Work item type definition with fields and states

        Raises:
            ValidationError: If work item type is invalid
        """
        # Validate work item type
        work_item_type_name = validate_work_item_type(work_item_type_name)

        # Get work item type definition
        wit_type = self.wit_client.get_work_item_type(
            project=self.project,
            type=work_item_type_name
        )

        # Format response
        return {
            'name': wit_type.name,
            'description': wit_type.description,
            'icon': wit_type.icon.id if wit_type.icon else None,
            'color': wit_type.color,
            'is_disabled': wit_type.is_disabled if hasattr(wit_type, 'is_disabled') else False,
            'states': [state.name for state in wit_type.states] if wit_type.states else [],
            'field_instances': [
                {
                    'name': field.name,
                    'reference_name': field.reference_name,
                    'always_required': field.always_required if hasattr(field, 'always_required') else False,
                    'help_text': field.help_text if hasattr(field, 'help_text') else None
                }
                for field in (wit_type.field_instances or [])
            ][:20]  # Limit to first 20 fields for readability
        }

    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def get_query(
        self,
        query_id: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Get a saved WIQL query definition.

        Args:
            query_id: Query ID or path (e.g., "My Queries/Active Bugs")
            depth: Query tree depth (1=query only, 2=query+children)

        Returns:
            Query definition with WIQL and metadata

        Raises:
            NotFoundError: If query doesn't exist
        """
        # Get query
        query = self.wit_client.get_query(
            project=self.project,
            query=query_id,
            depth=depth
        )

        # Format response
        return {
            'id': query.id,
            'name': query.name,
            'path': query.path,
            'wiql': query.wiql if hasattr(query, 'wiql') else None,
            'is_folder': query.is_folder if hasattr(query, 'is_folder') else False,
            'is_public': query.is_public if hasattr(query, 'is_public') else False,
            'created_by': self._format_identity(query.created_by) if hasattr(query, 'created_by') else None,
            'created_date': self._format_date(query.created_date) if hasattr(query, 'created_date') else None,
            'last_modified_by': self._format_identity(query.last_modified_by) if hasattr(query, 'last_modified_by') else None,
            'last_modified_date': self._format_date(query.last_modified_date) if hasattr(query, 'last_modified_date') else None
        }

    @azure_devops_operation(timeout_seconds=30, max_retries=3)
    async def execute_query_by_id(
        self,
        query_id: str,
        limit: int = QueryLimits.DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Execute a saved query and return results.

        Args:
            query_id: Query ID or path
            limit: Maximum number of results to return

        Returns:
            List of work items matching the query

        Raises:
            NotFoundError: If query doesn't exist
        """
        # Get and validate query
        query = await self.get_query(query_id, depth=1)

        if not query.get('wiql'):
            from ..errors import ValidationError
            raise ValidationError(f"Query '{query_id}' is a folder or has no WIQL")

        # Execute query
        from azure.devops.v7_1.work_item_tracking.models import Wiql
        wiql = Wiql(query=query['wiql'])
        query_result = self.wit_client.query_by_wiql(wiql, project=self.project)

        if not query_result.work_items:
            return []

        # Get work item IDs
        ids = [item.id for item in query_result.work_items[:limit]]

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
