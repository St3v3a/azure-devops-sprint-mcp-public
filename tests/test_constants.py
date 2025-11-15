"""
Unit tests for constants module.

Tests field definitions, query limits, and helper functions.
"""

import pytest
from src.constants import (
    FieldNames,
    BASIC_FIELDS,
    DETAILED_FIELDS,
    SPRINT_FIELDS,
    BUG_FIELDS,
    USER_STORY_FIELDS,
    TASK_FIELDS,
    MY_WORK_ITEMS_FIELDS,
    QueryLimits,
    ExpandOptions,
    WorkItemStates,
    LinkTypes,
    Priority,
    Severity,
    get_fields_for_work_item_type,
    fields_to_string,
    format_wiql_fields
)


class TestFieldNames:
    """Test FieldNames class."""

    def test_system_fields_exist(self):
        """Test that common system fields are defined."""
        assert hasattr(FieldNames, 'ID')
        assert hasattr(FieldNames, 'TITLE')
        assert hasattr(FieldNames, 'STATE')
        assert hasattr(FieldNames, 'WORK_ITEM_TYPE')
        assert hasattr(FieldNames, 'ASSIGNED_TO')

    def test_system_field_values(self):
        """Test that system fields have correct values."""
        assert FieldNames.ID == "System.Id"
        assert FieldNames.TITLE == "System.Title"
        assert FieldNames.STATE == "System.State"
        assert FieldNames.ASSIGNED_TO == "System.AssignedTo"

    def test_vsts_common_fields_exist(self):
        """Test that VSTS.Common fields are defined."""
        assert hasattr(FieldNames, 'PRIORITY')
        assert hasattr(FieldNames, 'SEVERITY')
        assert hasattr(FieldNames, 'STACK_RANK')
        assert hasattr(FieldNames, 'ACTIVITY')

    def test_vsts_common_field_values(self):
        """Test VSTS.Common field values."""
        assert FieldNames.PRIORITY == "Microsoft.VSTS.Common.Priority"
        assert FieldNames.SEVERITY == "Microsoft.VSTS.Common.Severity"
        assert FieldNames.ACTIVITY == "Microsoft.VSTS.Common.Activity"

    def test_vsts_scheduling_fields_exist(self):
        """Test that VSTS.Scheduling fields are defined."""
        assert hasattr(FieldNames, 'REMAINING_WORK')
        assert hasattr(FieldNames, 'COMPLETED_WORK')
        assert hasattr(FieldNames, 'STORY_POINTS')
        assert hasattr(FieldNames, 'ORIGINAL_ESTIMATE')

    def test_vsts_scheduling_field_values(self):
        """Test VSTS.Scheduling field values."""
        assert FieldNames.REMAINING_WORK == "Microsoft.VSTS.Scheduling.RemainingWork"
        assert FieldNames.STORY_POINTS == "Microsoft.VSTS.Scheduling.StoryPoints"

    def test_iteration_and_area_paths(self):
        """Test path fields."""
        assert FieldNames.ITERATION_PATH == "System.IterationPath"
        assert FieldNames.AREA_PATH == "System.AreaPath"

    def test_date_fields_exist(self):
        """Test that date fields are defined."""
        assert hasattr(FieldNames, 'CREATED_DATE')
        assert hasattr(FieldNames, 'CHANGED_DATE')
        assert hasattr(FieldNames, 'CLOSED_DATE')

    def test_build_fields_exist(self):
        """Test that build-related fields exist."""
        assert hasattr(FieldNames, 'INTEGRATION_BUILD')
        assert hasattr(FieldNames, 'FOUND_IN')


class TestFieldSets:
    """Test predefined field sets."""

    def test_basic_fields_minimal(self):
        """Test that BASIC_FIELDS is minimal."""
        assert len(BASIC_FIELDS) == 5
        assert FieldNames.ID in BASIC_FIELDS
        assert FieldNames.TITLE in BASIC_FIELDS
        assert FieldNames.STATE in BASIC_FIELDS
        assert FieldNames.WORK_ITEM_TYPE in BASIC_FIELDS
        assert FieldNames.ASSIGNED_TO in BASIC_FIELDS

    def test_detailed_fields_includes_basic(self):
        """Test that DETAILED_FIELDS includes all BASIC_FIELDS."""
        for field in BASIC_FIELDS:
            assert field in DETAILED_FIELDS

    def test_detailed_fields_has_more_than_basic(self):
        """Test that DETAILED_FIELDS has more fields than BASIC_FIELDS."""
        assert len(DETAILED_FIELDS) > len(BASIC_FIELDS)

    def test_detailed_fields_includes_metadata(self):
        """Test that DETAILED_FIELDS includes metadata."""
        assert FieldNames.CREATED_DATE in DETAILED_FIELDS
        assert FieldNames.CHANGED_DATE in DETAILED_FIELDS
        assert FieldNames.CREATED_BY in DETAILED_FIELDS

    def test_sprint_fields_includes_tracking(self):
        """Test that SPRINT_FIELDS includes sprint tracking fields."""
        assert FieldNames.ITERATION_PATH in SPRINT_FIELDS
        assert FieldNames.PRIORITY in SPRINT_FIELDS
        assert FieldNames.REMAINING_WORK in SPRINT_FIELDS
        assert FieldNames.STORY_POINTS in SPRINT_FIELDS

    def test_bug_fields_includes_bug_specific(self):
        """Test that BUG_FIELDS includes bug-specific fields."""
        assert FieldNames.SEVERITY in BUG_FIELDS
        assert FieldNames.PRIORITY in BUG_FIELDS
        assert FieldNames.REPRO_STEPS in BUG_FIELDS

    def test_user_story_fields_includes_story_specific(self):
        """Test that USER_STORY_FIELDS includes story-specific fields."""
        assert FieldNames.STORY_POINTS in USER_STORY_FIELDS
        assert FieldNames.PRIORITY in USER_STORY_FIELDS
        assert FieldNames.ACCEPTANCE_CRITERIA in USER_STORY_FIELDS

    def test_task_fields_includes_task_specific(self):
        """Test that TASK_FIELDS includes task-specific fields."""
        assert FieldNames.REMAINING_WORK in TASK_FIELDS
        assert FieldNames.COMPLETED_WORK in TASK_FIELDS
        assert FieldNames.ORIGINAL_ESTIMATE in TASK_FIELDS
        assert FieldNames.ACTIVITY in TASK_FIELDS

    def test_my_work_items_fields_includes_essentials(self):
        """Test that MY_WORK_ITEMS_FIELDS includes essential fields."""
        assert FieldNames.ID in MY_WORK_ITEMS_FIELDS
        assert FieldNames.TITLE in MY_WORK_ITEMS_FIELDS
        assert FieldNames.STATE in MY_WORK_ITEMS_FIELDS
        assert FieldNames.ASSIGNED_TO in MY_WORK_ITEMS_FIELDS
        assert FieldNames.ITERATION_PATH in MY_WORK_ITEMS_FIELDS

    def test_no_duplicate_fields(self):
        """Test that field sets don't have duplicates."""
        assert len(BASIC_FIELDS) == len(set(BASIC_FIELDS))
        assert len(DETAILED_FIELDS) == len(set(DETAILED_FIELDS))
        assert len(SPRINT_FIELDS) == len(set(SPRINT_FIELDS))


class TestQueryLimits:
    """Test QueryLimits class."""

    def test_default_limit(self):
        """Test default query limit."""
        assert QueryLimits.DEFAULT_LIMIT == 100

    def test_sprint_limit(self):
        """Test sprint query limit."""
        assert QueryLimits.SPRINT_LIMIT == 500

    def test_max_limit(self):
        """Test maximum query limit."""
        assert QueryLimits.MAX_LIMIT == 20000

    def test_batch_size(self):
        """Test batch size for work item retrieval."""
        assert QueryLimits.BATCH_SIZE == 200

    def test_limits_are_increasing(self):
        """Test that limits are in increasing order."""
        assert QueryLimits.DEFAULT_LIMIT < QueryLimits.SPRINT_LIMIT
        assert QueryLimits.SPRINT_LIMIT < QueryLimits.MAX_LIMIT

    def test_batch_size_reasonable(self):
        """Test that batch size is reasonable."""
        assert QueryLimits.BATCH_SIZE <= QueryLimits.SPRINT_LIMIT
        assert QueryLimits.BATCH_SIZE >= 100


class TestExpandOptions:
    """Test ExpandOptions class."""

    def test_expand_none(self):
        """Test NONE expand option."""
        assert ExpandOptions.NONE == "None"

    def test_expand_relations(self):
        """Test RELATIONS expand option."""
        assert ExpandOptions.RELATIONS == "Relations"

    def test_expand_fields(self):
        """Test FIELDS expand option."""
        assert ExpandOptions.FIELDS == "Fields"

    def test_expand_links(self):
        """Test LINKS expand option."""
        assert ExpandOptions.LINKS == "Links"

    def test_expand_all(self):
        """Test ALL expand option."""
        assert ExpandOptions.ALL == "All"


class TestWorkItemStates:
    """Test WorkItemStates class."""

    def test_basic_states_exist(self):
        """Test that basic states are defined."""
        assert hasattr(WorkItemStates, 'NEW')
        assert hasattr(WorkItemStates, 'ACTIVE')
        assert hasattr(WorkItemStates, 'RESOLVED')
        assert hasattr(WorkItemStates, 'CLOSED')

    def test_state_values(self):
        """Test state values."""
        assert WorkItemStates.NEW == "New"
        assert WorkItemStates.ACTIVE == "Active"
        assert WorkItemStates.DONE == "Done"

    def test_completed_states_set(self):
        """Test COMPLETED_STATES set."""
        assert isinstance(WorkItemStates.COMPLETED_STATES, set)
        assert 'Done' in WorkItemStates.COMPLETED_STATES
        assert 'Closed' in WorkItemStates.COMPLETED_STATES
        assert 'Completed' in WorkItemStates.COMPLETED_STATES

    def test_in_progress_states_set(self):
        """Test IN_PROGRESS_STATES set."""
        assert isinstance(WorkItemStates.IN_PROGRESS_STATES, set)
        assert 'Active' in WorkItemStates.IN_PROGRESS_STATES
        assert 'In Progress' in WorkItemStates.IN_PROGRESS_STATES

    def test_states_dont_overlap(self):
        """Test that completed and in-progress states don't overlap."""
        overlap = WorkItemStates.COMPLETED_STATES & WorkItemStates.IN_PROGRESS_STATES
        assert len(overlap) == 0

    def test_states_are_non_empty(self):
        """Test that state sets are non-empty."""
        assert len(WorkItemStates.COMPLETED_STATES) > 0
        assert len(WorkItemStates.IN_PROGRESS_STATES) > 0


class TestLinkTypes:
    """Test LinkTypes class."""

    def test_hierarchy_links_exist(self):
        """Test that hierarchy link types exist."""
        assert hasattr(LinkTypes, 'HIERARCHY_FORWARD')
        assert hasattr(LinkTypes, 'HIERARCHY_REVERSE')
        assert hasattr(LinkTypes, 'PARENT')
        assert hasattr(LinkTypes, 'CHILD')

    def test_dependency_links_exist(self):
        """Test that dependency link types exist."""
        assert hasattr(LinkTypes, 'DEPENDENCY_FORWARD')
        assert hasattr(LinkTypes, 'DEPENDENCY_REVERSE')
        assert hasattr(LinkTypes, 'SUCCESSOR')
        assert hasattr(LinkTypes, 'PREDECESSOR')

    def test_link_type_values(self):
        """Test link type values."""
        assert LinkTypes.RELATED == "System.LinkTypes.Related"
        assert "System.LinkTypes" in LinkTypes.HIERARCHY_FORWARD


class TestPriorityAndSeverity:
    """Test Priority and Severity classes."""

    def test_priority_values(self):
        """Test priority values."""
        assert Priority.CRITICAL == 1
        assert Priority.HIGH == 2
        assert Priority.MEDIUM == 3
        assert Priority.LOW == 4

    def test_priority_ordering(self):
        """Test that priority values are ordered (1 is highest)."""
        assert Priority.CRITICAL < Priority.HIGH
        assert Priority.HIGH < Priority.MEDIUM
        assert Priority.MEDIUM < Priority.LOW

    def test_severity_values(self):
        """Test severity values."""
        assert Severity.CRITICAL == 1
        assert Severity.HIGH == 2
        assert Severity.MEDIUM == 3
        assert Severity.LOW == 4

    def test_severity_ordering(self):
        """Test that severity values are ordered (1 is most severe)."""
        assert Severity.CRITICAL < Severity.HIGH
        assert Severity.HIGH < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.LOW


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_fields_for_bug(self):
        """Test getting fields for Bug work item type."""
        fields = get_fields_for_work_item_type('Bug')
        assert fields == BUG_FIELDS
        assert FieldNames.SEVERITY in fields

    def test_get_fields_for_user_story(self):
        """Test getting fields for User Story work item type."""
        fields = get_fields_for_work_item_type('User Story')
        assert fields == USER_STORY_FIELDS
        assert FieldNames.STORY_POINTS in fields

    def test_get_fields_for_task(self):
        """Test getting fields for Task work item type."""
        fields = get_fields_for_work_item_type('Task')
        assert fields == TASK_FIELDS
        assert FieldNames.REMAINING_WORK in fields

    def test_get_fields_case_insensitive(self):
        """Test that field lookup is case-insensitive."""
        fields1 = get_fields_for_work_item_type('BUG')
        fields2 = get_fields_for_work_item_type('bug')
        fields3 = get_fields_for_work_item_type('Bug')
        assert fields1 == fields2 == fields3

    def test_get_fields_for_unknown_type(self):
        """Test that unknown types return DETAILED_FIELDS."""
        fields = get_fields_for_work_item_type('UnknownType')
        assert fields == DETAILED_FIELDS

    def test_get_fields_for_product_backlog_item(self):
        """Test getting fields for Product Backlog Item (Scrum)."""
        fields = get_fields_for_work_item_type('Product Backlog Item')
        assert fields == USER_STORY_FIELDS

    def test_fields_to_string_basic(self):
        """Test converting field list to string."""
        fields = [FieldNames.ID, FieldNames.TITLE, FieldNames.STATE]
        result = fields_to_string(fields)
        assert result == "System.Id,System.Title,System.State"

    def test_fields_to_string_empty(self):
        """Test converting empty field list."""
        result = fields_to_string([])
        assert result == ""

    def test_fields_to_string_single(self):
        """Test converting single field."""
        result = fields_to_string([FieldNames.ID])
        assert result == "System.Id"

    def test_format_wiql_fields_basic(self):
        """Test formatting fields for WIQL."""
        fields = [FieldNames.ID, FieldNames.TITLE]
        result = format_wiql_fields(fields)
        assert result == "[System.Id], [System.Title]"

    def test_format_wiql_fields_empty(self):
        """Test formatting empty field list for WIQL."""
        result = format_wiql_fields([])
        assert result == ""

    def test_format_wiql_fields_single(self):
        """Test formatting single field for WIQL."""
        result = format_wiql_fields([FieldNames.STATE])
        assert result == "[System.State]"

    def test_format_wiql_fields_brackets(self):
        """Test that WIQL formatting adds brackets."""
        fields = [FieldNames.ID, FieldNames.TITLE, FieldNames.STATE]
        result = format_wiql_fields(fields)
        # Each field should be in brackets
        assert result.count('[') == 3
        assert result.count(']') == 3


class TestConstantsIntegration:
    """Test that constants work together correctly."""

    def test_field_sets_use_fieldnames(self):
        """Test that field sets use FieldNames constants."""
        # All fields in sets should be valid FieldNames values
        for field in BASIC_FIELDS:
            assert isinstance(field, str)
            assert field.startswith('System.') or field.startswith('Microsoft.VSTS.')

    def test_sprint_fields_optimized_for_sprints(self):
        """Test that SPRINT_FIELDS is optimized for sprint queries."""
        # Should include ID, title, state (basics)
        assert FieldNames.ID in SPRINT_FIELDS
        assert FieldNames.TITLE in SPRINT_FIELDS
        assert FieldNames.STATE in SPRINT_FIELDS

        # Should include sprint tracking
        assert FieldNames.ITERATION_PATH in SPRINT_FIELDS
        assert FieldNames.PRIORITY in SPRINT_FIELDS

        # Should include effort tracking
        assert FieldNames.REMAINING_WORK in SPRINT_FIELDS
        assert FieldNames.STORY_POINTS in SPRINT_FIELDS

    def test_limits_suitable_for_azure_devops(self):
        """Test that limits are suitable for Azure DevOps API."""
        # Azure DevOps max is 20,000
        assert QueryLimits.MAX_LIMIT == 20000

        # Default should be reasonable for most queries
        assert 50 <= QueryLimits.DEFAULT_LIMIT <= 200

        # Batch size should be efficient
        assert 100 <= QueryLimits.BATCH_SIZE <= 500

    def test_work_item_type_field_sets_comprehensive(self):
        """Test that work item type field sets are comprehensive."""
        # Bug fields should cover bug-specific needs
        bug_fields = get_fields_for_work_item_type('Bug')
        assert FieldNames.SEVERITY in bug_fields
        assert FieldNames.PRIORITY in bug_fields
        assert FieldNames.REPRO_STEPS in bug_fields

        # User Story fields should cover story-specific needs
        story_fields = get_fields_for_work_item_type('User Story')
        assert FieldNames.STORY_POINTS in story_fields
        assert FieldNames.ACCEPTANCE_CRITERIA in story_fields

        # Task fields should cover task-specific needs
        task_fields = get_fields_for_work_item_type('Task')
        assert FieldNames.REMAINING_WORK in task_fields
        assert FieldNames.COMPLETED_WORK in task_fields
        assert FieldNames.ACTIVITY in task_fields
