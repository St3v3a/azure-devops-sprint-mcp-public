"""
Input validation and WIQL query sanitization.

This module provides whitelist-based validation to prevent SQL injection
and ensure data integrity for Azure DevOps API operations.
"""

import re
from typing import Optional, List, Set


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


# Azure DevOps work item states (comprehensive list)
ALLOWED_STATES: Set[str] = {
    # Common states across all work item types
    'New',
    'Active',
    'Resolved',
    'Closed',
    'Done',
    'Removed',

    # Agile/Scrum states
    'In Progress',
    'Committed',
    'In Review',
    'Completed',

    # CMMI states
    'Proposed',
    'Approved',
    'Analysis',
    'Design',
    'Development',
    'Testing',
    'Verified',

    # Additional states
    'Ready',
    'To Do',
    'In Planning',
    'Cut',
}


# Azure DevOps work item types (comprehensive list)
ALLOWED_WORK_ITEM_TYPES: Set[str] = {
    # Agile
    'User Story',
    'Task',
    'Bug',
    'Feature',
    'Epic',
    'Issue',

    # Scrum
    'Product Backlog Item',
    'Impediment',

    # CMMI
    'Requirement',
    'Change Request',
    'Review',
    'Risk',
    'Test Case',

    # Additional types
    'Code Review Request',
    'Code Review Response',
    'Feedback Request',
    'Feedback Response',
    'Shared Steps',
    'Shared Parameter',
    'Test Plan',
    'Test Suite',
}


# Azure DevOps field reference names (comprehensive list)
ALLOWED_FIELD_NAMES: Set[str] = {
    # System fields
    'System.Id',
    'System.Rev',
    'System.AreaPath',
    'System.TeamProject',
    'System.IterationPath',
    'System.WorkItemType',
    'System.State',
    'System.Reason',
    'System.AssignedTo',
    'System.CreatedDate',
    'System.CreatedBy',
    'System.ChangedDate',
    'System.ChangedBy',
    'System.CommentCount',
    'System.Title',
    'System.BoardColumn',
    'System.BoardColumnDone',
    'System.Description',
    'System.Tags',
    'System.History',
    'System.RelatedLinkCount',
    'System.AttachedFileCount',
    'System.HyperLinkCount',
    'System.ExternalLinkCount',
    'System.RemoteLinkCount',
    'System.AuthorizedAs',
    'System.AuthorizedDate',
    'System.RevisedDate',
    'System.Watermark',
    'System.Parent',

    # Microsoft.VSTS.Common fields
    'Microsoft.VSTS.Common.StateChangeDate',
    'Microsoft.VSTS.Common.ActivatedDate',
    'Microsoft.VSTS.Common.ActivatedBy',
    'Microsoft.VSTS.Common.ResolvedDate',
    'Microsoft.VSTS.Common.ResolvedBy',
    'Microsoft.VSTS.Common.ResolvedReason',
    'Microsoft.VSTS.Common.ClosedDate',
    'Microsoft.VSTS.Common.ClosedBy',
    'Microsoft.VSTS.Common.Priority',
    'Microsoft.VSTS.Common.Severity',
    'Microsoft.VSTS.Common.ValueArea',
    'Microsoft.VSTS.Common.Risk',
    'Microsoft.VSTS.Common.StackRank',
    'Microsoft.VSTS.Common.Triage',
    'Microsoft.VSTS.Common.AcceptanceCriteria',
    'Microsoft.VSTS.Common.BacklogPriority',
    'Microsoft.VSTS.Common.BusinessValue',
    'Microsoft.VSTS.Common.TimeCriticality',

    # Microsoft.VSTS.Scheduling fields
    'Microsoft.VSTS.Scheduling.RemainingWork',
    'Microsoft.VSTS.Scheduling.CompletedWork',
    'Microsoft.VSTS.Scheduling.OriginalEstimate',
    'Microsoft.VSTS.Scheduling.StoryPoints',
    'Microsoft.VSTS.Scheduling.Effort',
    'Microsoft.VSTS.Scheduling.Size',
    'Microsoft.VSTS.Scheduling.StartDate',
    'Microsoft.VSTS.Scheduling.FinishDate',
    'Microsoft.VSTS.Scheduling.TargetDate',
    'Microsoft.VSTS.Scheduling.DueDate',

    # Microsoft.VSTS.Build fields
    'Microsoft.VSTS.Build.IntegrationBuild',
    'Microsoft.VSTS.Build.FoundIn',

    # Microsoft.VSTS.CMMI fields
    'Microsoft.VSTS.CMMI.RequirementType',
    'Microsoft.VSTS.CMMI.Analysis',
    'Microsoft.VSTS.CMMI.TaskType',
    'Microsoft.VSTS.CMMI.Blocked',
    'Microsoft.VSTS.CMMI.Impact',
    'Microsoft.VSTS.CMMI.Probability',
    'Microsoft.VSTS.CMMI.Mitigation',
    'Microsoft.VSTS.CMMI.ContingencyPlan',

    # Microsoft.VSTS.TCM (Test Case Management) fields
    'Microsoft.VSTS.TCM.ReproSteps',
    'Microsoft.VSTS.TCM.SystemInfo',
    'Microsoft.VSTS.TCM.Steps',
    'Microsoft.VSTS.TCM.LocalDataSource',
    'Microsoft.VSTS.TCM.Parameters',
    'Microsoft.VSTS.TCM.AutomatedTestName',
    'Microsoft.VSTS.TCM.AutomatedTestStorage',
    'Microsoft.VSTS.TCM.AutomatedTestId',
    'Microsoft.VSTS.TCM.AutomatedTestType',
}


# Link types for hierarchical queries
ALLOWED_LINK_TYPES: Set[str] = {
    'System.LinkTypes.Hierarchy-Forward',
    'System.LinkTypes.Hierarchy-Reverse',
    'System.LinkTypes.Related',
    'System.LinkTypes.Dependency-Forward',
    'System.LinkTypes.Dependency-Reverse',
    'System.LinkTypes.Duplicate-Forward',
    'System.LinkTypes.Duplicate-Reverse',
    'System.LinkTypes.Successor',
    'System.LinkTypes.Predecessor',
    'System.LinkTypes.Child',
    'System.LinkTypes.Parent',
    'System.LinkTypes.Affects',
    'System.LinkTypes.AffectedBy',
}


class StateValidator:
    """Validator for work item states."""

    @staticmethod
    def validate(state: str) -> str:
        """
        Validate work item state against whitelist.

        Args:
            state: The state to validate

        Returns:
            The validated state (unchanged)

        Raises:
            ValidationError: If state is not in whitelist
        """
        if not state:
            raise ValidationError("State cannot be empty")

        if state not in ALLOWED_STATES:
            raise ValidationError(
                f"Invalid state: '{state}'. "
                f"Allowed states: {', '.join(sorted(ALLOWED_STATES))}"
            )

        return state


class WorkItemTypeValidator:
    """Validator for work item types."""

    @staticmethod
    def validate(work_item_type: str) -> str:
        """
        Validate work item type against whitelist.

        Args:
            work_item_type: The work item type to validate

        Returns:
            The validated work item type (unchanged)

        Raises:
            ValidationError: If work item type is not in whitelist
        """
        if not work_item_type:
            raise ValidationError("Work item type cannot be empty")

        if work_item_type not in ALLOWED_WORK_ITEM_TYPES:
            raise ValidationError(
                f"Invalid work item type: '{work_item_type}'. "
                f"Allowed types: {', '.join(sorted(ALLOWED_WORK_ITEM_TYPES))}"
            )

        return work_item_type


class FieldNameValidator:
    """Validator for Azure DevOps field reference names."""

    @staticmethod
    def validate(field_name: str) -> str:
        """
        Validate field reference name against whitelist.

        Args:
            field_name: The field reference name to validate

        Returns:
            The validated field name (unchanged)

        Raises:
            ValidationError: If field name is not in whitelist
        """
        if not field_name:
            raise ValidationError("Field name cannot be empty")

        # Strip /fields/ prefix if present
        clean_field_name = field_name.replace('/fields/', '')

        if clean_field_name not in ALLOWED_FIELD_NAMES:
            raise ValidationError(
                f"Invalid field name: '{field_name}'. "
                f"Field is not in the allowed list. "
                f"Common fields: System.Id, System.Title, System.State, "
                f"Microsoft.VSTS.Common.Priority, Microsoft.VSTS.Scheduling.StoryPoints"
            )

        return field_name


class LinkTypeValidator:
    """Validator for work item link types."""

    @staticmethod
    def validate(link_type: str) -> str:
        """
        Validate link type against whitelist.

        Args:
            link_type: The link type to validate

        Returns:
            The validated link type (unchanged)

        Raises:
            ValidationError: If link type is not in whitelist
        """
        if not link_type:
            raise ValidationError("Link type cannot be empty")

        if link_type not in ALLOWED_LINK_TYPES:
            raise ValidationError(
                f"Invalid link type: '{link_type}'. "
                f"Allowed link types: {', '.join(sorted(ALLOWED_LINK_TYPES))}"
            )

        return link_type


class WiqlValidator:
    """Validator for WIQL (Work Item Query Language) queries."""

    MAX_QUERY_LENGTH = 32000  # 32KB limit per Azure DevOps documentation

    @staticmethod
    def validate(query: str) -> str:
        """
        Validate WIQL query syntax and structure.

        Args:
            query: The WIQL query to validate

        Returns:
            The validated query (unchanged)

        Raises:
            ValidationError: If query is invalid
        """
        if not query:
            raise ValidationError("WIQL query cannot be empty")

        # Check length
        if len(query) > WiqlValidator.MAX_QUERY_LENGTH:
            raise ValidationError(
                f"WIQL query exceeds maximum length of {WiqlValidator.MAX_QUERY_LENGTH} characters "
                f"(current length: {len(query)})"
            )

        # Check for required clauses
        query_upper = query.upper()

        if 'SELECT' not in query_upper:
            raise ValidationError("WIQL query must contain SELECT clause")

        if 'FROM' not in query_upper:
            raise ValidationError("WIQL query must contain FROM clause")

        # Check for valid FROM target
        valid_targets = ['WORKITEMS', 'WORKITEMLINKS']
        has_valid_target = any(target in query_upper for target in valid_targets)

        if not has_valid_target:
            raise ValidationError(
                "WIQL query FROM clause must specify 'WorkItems' or 'WorkItemLinks'"
            )

        # Check for balanced brackets
        if not WiqlValidator._check_balanced_brackets(query):
            raise ValidationError("WIQL query has unbalanced square brackets")

        return query

    @staticmethod
    def _check_balanced_brackets(query: str) -> bool:
        """
        Check if square brackets are balanced in the query.

        Args:
            query: The query to check

        Returns:
            True if balanced, False otherwise
        """
        count = 0
        for char in query:
            if char == '[':
                count += 1
            elif char == ']':
                count -= 1
            if count < 0:
                return False
        return count == 0

    @staticmethod
    def sanitize_string_literal(value: str) -> str:
        """
        Sanitize a string value for use in WIQL query.

        This escapes single quotes to prevent injection attacks.

        Args:
            value: The string value to sanitize

        Returns:
            The sanitized string value
        """
        if value is None:
            return None

        # Escape single quotes (SQL-style escaping)
        return value.replace("'", "''")


class IterationPathValidator:
    """Validator for iteration paths."""

    @staticmethod
    def validate(iteration_path: str, project: str) -> str:
        """
        Validate and normalize iteration path.

        Ensures the iteration path includes the project name prefix.

        Args:
            iteration_path: The iteration path to validate
            project: The project name

        Returns:
            The normalized iteration path with project prefix

        Raises:
            ValidationError: If iteration path contains invalid characters
        """
        if not iteration_path:
            raise ValidationError("Iteration path cannot be empty")

        if not project:
            raise ValidationError("Project name is required for iteration path validation")

        # Check for injection attempts (basic path traversal)
        if '..' in iteration_path or '//' in iteration_path:
            raise ValidationError(
                f"Invalid iteration path: '{iteration_path}'. "
                "Path traversal characters not allowed."
            )

        # Auto-prefix with project name if not present
        if not iteration_path.startswith(f'{project}\\'):
            iteration_path = f'{project}\\{iteration_path}'

        return iteration_path


class PriorityValidator:
    """Validator for work item priority."""

    ALLOWED_PRIORITIES = {1, 2, 3, 4}

    @staticmethod
    def validate(priority: int) -> int:
        """
        Validate work item priority.

        Args:
            priority: The priority to validate (1-4)

        Returns:
            The validated priority (unchanged)

        Raises:
            ValidationError: If priority is not 1-4
        """
        if priority not in PriorityValidator.ALLOWED_PRIORITIES:
            raise ValidationError(
                f"Invalid priority: {priority}. "
                f"Priority must be 1-4 (where 1 is highest)"
            )

        return priority


class SeverityValidator:
    """Validator for bug severity."""

    ALLOWED_SEVERITIES = {1, 2, 3, 4}

    @staticmethod
    def validate(severity: int) -> int:
        """
        Validate bug severity.

        Args:
            severity: The severity to validate (1-4)

        Returns:
            The validated severity (unchanged)

        Raises:
            ValidationError: If severity is not 1-4
        """
        if severity not in SeverityValidator.ALLOWED_SEVERITIES:
            raise ValidationError(
                f"Invalid severity: {severity}. "
                f"Severity must be 1-4 (where 1 is most severe)"
            )

        return severity


# Convenience functions for common validations

def validate_state(state: Optional[str]) -> Optional[str]:
    """Validate state if provided."""
    return StateValidator.validate(state) if state else None


def validate_work_item_type(work_item_type: Optional[str]) -> Optional[str]:
    """Validate work item type if provided."""
    return WorkItemTypeValidator.validate(work_item_type) if work_item_type else None


def validate_field_name(field_name: str) -> str:
    """Validate field reference name."""
    return FieldNameValidator.validate(field_name)


def validate_field_names(field_names: List[str]) -> List[str]:
    """Validate a list of field reference names."""
    return [FieldNameValidator.validate(name) for name in field_names]


def validate_wiql(query: str) -> str:
    """Validate WIQL query."""
    return WiqlValidator.validate(query)


def validate_link_type(link_type: str) -> str:
    """Validate link type."""
    return LinkTypeValidator.validate(link_type)


def validate_iteration_path(iteration_path: str, project: str) -> str:
    """Validate and normalize iteration path."""
    return IterationPathValidator.validate(iteration_path, project)


def validate_priority(priority: Optional[int]) -> Optional[int]:
    """Validate priority if provided."""
    return PriorityValidator.validate(priority) if priority is not None else None


def validate_severity(severity: Optional[int]) -> Optional[int]:
    """Validate severity if provided."""
    return SeverityValidator.validate(severity) if severity is not None else None


def sanitize_wiql_string(value: str) -> str:
    """Sanitize a string value for use in WIQL queries."""
    return WiqlValidator.sanitize_string_literal(value)
