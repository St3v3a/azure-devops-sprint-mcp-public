"""
Unit tests for validation module.

Tests whitelist validation, WIQL syntax validation, and input sanitization.
"""

import pytest
from src.validation import (
    validate_state,
    validate_work_item_type,
    validate_field_name,
    validate_iteration_path,
    validate_wiql,
    ValidationError,
    WiqlValidator,
    ALLOWED_STATES,
    ALLOWED_WORK_ITEM_TYPES,
    ALLOWED_FIELD_NAMES as ALLOWED_FIELDS
)


class TestStateValidation:
    """Test work item state validation."""

    def test_validate_valid_states(self):
        """Test that all allowed states are accepted."""
        for state in ['New', 'Active', 'Resolved', 'Closed', 'Done']:
            result = validate_state(state)
            assert result == state

    def test_validate_case_insensitive(self):
        """Test that state validation is case-insensitive."""
        assert validate_state('active') == 'Active'
        assert validate_state('RESOLVED') == 'Resolved'
        assert validate_state('DoNe') == 'Done'

    def test_validate_invalid_state(self):
        """Test that invalid states raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_state('InvalidState')

        assert 'Invalid state' in str(exc_info.value)
        assert 'InvalidState' in str(exc_info.value)

    def test_validate_empty_state(self):
        """Test that empty state raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_state('')

    def test_validate_none_state(self):
        """Test that None state raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_state(None)

    def test_validate_sql_injection_attempt(self):
        """Test that SQL injection attempts are rejected."""
        with pytest.raises(ValidationError):
            validate_state("Active' OR '1'='1")

        with pytest.raises(ValidationError):
            validate_state("Active; DROP TABLE workitems;--")


class TestWorkItemTypeValidation:
    """Test work item type validation."""

    def test_validate_valid_types(self):
        """Test that all allowed types are accepted."""
        for wit_type in ['Task', 'Bug', 'User Story', 'Feature', 'Epic']:
            result = validate_work_item_type(wit_type)
            assert result == wit_type

    def test_validate_case_insensitive(self):
        """Test that type validation is case-insensitive."""
        assert validate_work_item_type('task') == 'Task'
        assert validate_work_item_type('BUG') == 'Bug'
        assert validate_work_item_type('user story') == 'User Story'

    def test_validate_invalid_type(self):
        """Test that invalid types raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_work_item_type('InvalidType')

        assert 'Invalid work item type' in str(exc_info.value)

    def test_validate_product_backlog_item(self):
        """Test Scrum-specific work item type."""
        result = validate_work_item_type('Product Backlog Item')
        assert result == 'Product Backlog Item'


class TestFieldNameValidation:
    """Test field name validation."""

    def test_validate_valid_system_fields(self):
        """Test that system fields are accepted."""
        for field in ['System.Id', 'System.Title', 'System.State', 'System.AssignedTo']:
            result = validate_field_name(field)
            assert result == field

    def test_validate_valid_vsts_fields(self):
        """Test that VSTS fields are accepted."""
        for field in ['Microsoft.VSTS.Common.Priority', 'Microsoft.VSTS.Scheduling.RemainingWork']:
            result = validate_field_name(field)
            assert result == field

    def test_validate_invalid_field(self):
        """Test that invalid fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_field_name('Invalid.Field.Name')

        assert 'Invalid field name' in str(exc_info.value)

    def test_validate_sql_injection_in_field(self):
        """Test that SQL injection in field names is rejected."""
        with pytest.raises(ValidationError):
            validate_field_name("System.Id'; DROP TABLE--")


class TestIterationPathValidation:
    """Test iteration path validation."""

    def test_validate_simple_path(self):
        """Test simple iteration path."""
        result = validate_iteration_path('Sprint 1', 'MyProject')
        assert result == 'MyProject\\Sprint 1'

    def test_validate_already_prefixed_path(self):
        """Test path that already has project prefix."""
        result = validate_iteration_path('MyProject\\Sprint 1', 'MyProject')
        assert result == 'MyProject\\Sprint 1'

    def test_validate_nested_path(self):
        """Test nested iteration path."""
        result = validate_iteration_path('2024\\Q1\\Sprint 1', 'MyProject')
        assert result == 'MyProject\\2024\\Q1\\Sprint 1'

    def test_validate_backslash_separators(self):
        """Test that backslashes are normalized."""
        result = validate_iteration_path('Sprint 1', 'MyProject')
        assert '\\' in result
        assert result.startswith('MyProject\\')

    def test_validate_sql_injection_in_path(self):
        """Test that SQL injection in paths is rejected."""
        with pytest.raises(ValidationError):
            validate_iteration_path("Sprint'; DROP TABLE--", 'MyProject')

    def test_validate_special_characters(self):
        """Test that dangerous characters are rejected."""
        with pytest.raises(ValidationError):
            validate_iteration_path('Sprint;1', 'MyProject')

        with pytest.raises(ValidationError):
            validate_iteration_path("Sprint'1", 'MyProject')


class TestWiqlValidation:
    """Test WIQL query validation."""

    def test_validate_simple_query(self):
        """Test that simple valid queries are accepted."""
        query = 'SELECT [System.Id] FROM workitems WHERE [System.State] = "Active"'
        result = validate_wiql(query)
        assert result == query

    def test_validate_query_with_top(self):
        """Test query with TOP clause."""
        query = 'SELECT TOP 100 [System.Id], [System.Title] FROM workitems'
        result = validate_wiql(query)
        assert result == query

    def test_validate_query_with_order(self):
        """Test query with ORDER BY clause."""
        query = '''
        SELECT [System.Id]
        FROM workitems
        WHERE [System.State] = "Active"
        ORDER BY [System.CreatedDate] DESC
        '''
        result = validate_wiql(query)
        assert 'SELECT' in result

    def test_validate_workitemlinks_query(self):
        """Test WorkItemLinks query type."""
        query = '''
        SELECT [System.Id]
        FROM WorkItemLinks
        WHERE [Source].[System.Id] = 123
        MODE (Recursive)
        '''
        result = validate_wiql(query)
        assert 'WorkItemLinks' in result

    def test_validate_missing_select(self):
        """Test that queries without SELECT are rejected."""
        query = 'FROM workitems WHERE [System.State] = "Active"'
        with pytest.raises(ValidationError) as exc_info:
            validate_wiql(query)

        assert 'must contain a SELECT clause' in str(exc_info.value)

    def test_validate_missing_from(self):
        """Test that queries without FROM are rejected."""
        query = 'SELECT [System.Id] WHERE [System.State] = "Active"'
        with pytest.raises(ValidationError) as exc_info:
            validate_wiql(query)

        assert 'must contain a FROM clause' in str(exc_info.value)

    def test_validate_invalid_from_clause(self):
        """Test that invalid FROM targets are rejected."""
        query = 'SELECT [System.Id] FROM invalid_table WHERE [System.State] = "Active"'
        with pytest.raises(ValidationError) as exc_info:
            validate_wiql(query)

        assert 'FROM clause must reference' in str(exc_info.value)

    def test_validate_unbalanced_brackets(self):
        """Test that unbalanced brackets are rejected."""
        query = 'SELECT [System.Id FROM workitems'
        with pytest.raises(ValidationError) as exc_info:
            validate_wiql(query)

        assert 'unbalanced brackets' in str(exc_info.value)

    def test_validate_query_too_long(self):
        """Test that queries exceeding max length are rejected."""
        # Create a query longer than 32KB
        long_query = 'SELECT [System.Id] FROM workitems WHERE ' + ' OR '.join(
            [f'[System.Id] = {i}' for i in range(10000)]
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_wiql(long_query)

        assert 'exceeds maximum length' in str(exc_info.value)
        assert '32768' in str(exc_info.value)

    def test_validate_empty_query(self):
        """Test that empty queries are rejected."""
        with pytest.raises(ValidationError):
            validate_wiql('')

        with pytest.raises(ValidationError):
            validate_wiql('   ')

    def test_validate_none_query(self):
        """Test that None queries are rejected."""
        with pytest.raises(ValidationError):
            validate_wiql(None)


class TestWiqlValidator:
    """Test WiqlValidator class methods."""

    def test_validator_has_select(self):
        """Test _has_select_clause method."""
        assert WiqlValidator._has_select_clause('SELECT [System.Id] FROM workitems')
        assert not WiqlValidator._has_select_clause('FROM workitems WHERE [System.State] = "Active"')

    def test_validator_has_from(self):
        """Test _has_from_clause method."""
        assert WiqlValidator._has_from_clause('SELECT [System.Id] FROM workitems')
        assert not WiqlValidator._has_from_clause('SELECT [System.Id] WHERE [System.State] = "Active"')

    def test_validator_valid_from(self):
        """Test _has_valid_from_clause method."""
        assert WiqlValidator._has_valid_from_clause('FROM workitems WHERE')
        assert WiqlValidator._has_valid_from_clause('FROM WorkItemLinks WHERE')
        assert not WiqlValidator._has_valid_from_clause('FROM invalid_table WHERE')

    def test_validator_balanced_brackets(self):
        """Test _has_balanced_brackets method."""
        assert WiqlValidator._has_balanced_brackets('[System.Id]')
        assert WiqlValidator._has_balanced_brackets('[System.Id], [System.Title]')
        assert not WiqlValidator._has_balanced_brackets('[System.Id')
        assert not WiqlValidator._has_balanced_brackets('System.Id]')
        assert not WiqlValidator._has_balanced_brackets('[System.Id][')


class TestWhitelistCoverage:
    """Test that whitelists cover common use cases."""

    def test_all_common_states_included(self):
        """Test that common states are in whitelist."""
        common_states = ['New', 'Active', 'Resolved', 'Closed', 'Done',
                        'In Progress', 'Committed', 'Completed']
        for state in common_states:
            assert state in ALLOWED_STATES

    def test_all_common_types_included(self):
        """Test that common work item types are in whitelist."""
        common_types = ['Task', 'Bug', 'User Story', 'Feature', 'Epic',
                       'Product Backlog Item', 'Issue']
        for wit_type in common_types:
            assert wit_type in ALLOWED_WORK_ITEM_TYPES

    def test_all_common_fields_included(self):
        """Test that common fields are in whitelist."""
        common_fields = [
            'System.Id', 'System.Title', 'System.State', 'System.AssignedTo',
            'System.Description', 'Microsoft.VSTS.Common.Priority',
            'Microsoft.VSTS.Scheduling.RemainingWork'
        ]
        for field in common_fields:
            assert field in ALLOWED_FIELDS
