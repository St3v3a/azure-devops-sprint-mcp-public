"""
Unit tests for ServiceManager module.

Tests multi-project service management, lazy loading, caching, and statistics.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from src.service_manager import ServiceManager
from src.auth import AzureDevOpsAuth
from src.validation import ValidationError


class TestServiceManagerInitialization:
    """Test ServiceManager initialization."""

    def test_initialization_with_auth_and_default_project(self):
        """Test creating ServiceManager with auth and default project."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()  # Simulate initialized auth

        manager = ServiceManager(auth, default_project="TestProject")

        assert manager.auth == auth
        assert manager.default_project == "TestProject"
        assert len(manager._sprint_services) == 0
        assert len(manager._workitem_services) == 0

    def test_initialization_without_default_project(self):
        """Test creating ServiceManager without default project."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()

        manager = ServiceManager(auth)

        assert manager.auth == auth
        assert manager.default_project is None

    def test_initialization_requires_initialized_auth(self):
        """Test that ServiceManager requires initialized auth."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = None  # Not initialized

        with pytest.raises(ValueError, match="initialized AzureDevOpsAuth"):
            ServiceManager(auth)

    def test_initialization_requires_auth_parameter(self):
        """Test that ServiceManager requires auth parameter."""
        with pytest.raises(ValueError, match="initialized AzureDevOpsAuth"):
            ServiceManager(None)


class TestServiceManagerSprintService:
    """Test ServiceManager sprint service management."""

    def test_get_sprint_service_creates_new_instance(self):
        """Test getting sprint service creates new instance."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="DefaultProject")

        with patch('src.service_manager.SprintService') as MockService:
            mock_instance = Mock()
            MockService.return_value = mock_instance

            service = manager.get_sprint_service("TestProject")

            MockService.assert_called_once_with(auth, "TestProject")
            assert service == mock_instance
            assert "TestProject" in manager._sprint_services
            assert manager._service_creation_count == 1

    def test_get_sprint_service_returns_cached_instance(self):
        """Test getting sprint service returns cached instance."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService') as MockService:
            mock_instance = Mock()
            MockService.return_value = mock_instance

            # First call creates instance
            service1 = manager.get_sprint_service("TestProject")
            # Second call returns cached
            service2 = manager.get_sprint_service("TestProject")

            # Should only create once
            assert MockService.call_count == 1
            assert service1 is service2
            assert manager._service_creation_count == 1
            assert manager._cache_hit_count == 1

    def test_get_sprint_service_uses_default_project(self):
        """Test getting sprint service uses default project when not specified."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="DefaultProject")

        with patch('src.service_manager.SprintService') as MockService:
            mock_instance = Mock()
            MockService.return_value = mock_instance

            service = manager.get_sprint_service()

            MockService.assert_called_once_with(auth, "DefaultProject")

    def test_get_sprint_service_raises_without_project_or_default(self):
        """Test getting sprint service raises error without project or default."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)  # No default project

        with pytest.raises(ValidationError, match="Project name is required"):
            manager.get_sprint_service()

    def test_get_sprint_service_multiple_projects(self):
        """Test getting sprint services for multiple projects."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService') as MockService:
            MockService.side_effect = [Mock(), Mock(), Mock()]

            service1 = manager.get_sprint_service("Project1")
            service2 = manager.get_sprint_service("Project2")
            service3 = manager.get_sprint_service("Project3")

            assert service1 is not service2
            assert service2 is not service3
            assert len(manager._sprint_services) == 3
            assert manager._service_creation_count == 3


class TestServiceManagerWorkItemService:
    """Test ServiceManager work item service management."""

    def test_get_workitem_service_creates_new_instance(self):
        """Test getting work item service creates new instance."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.WorkItemService') as MockService:
            mock_instance = Mock()
            MockService.return_value = mock_instance

            service = manager.get_workitem_service("TestProject")

            MockService.assert_called_once_with(auth, "TestProject")
            assert service == mock_instance
            assert "TestProject" in manager._workitem_services
            assert manager._service_creation_count == 1

    def test_get_workitem_service_returns_cached_instance(self):
        """Test getting work item service returns cached instance."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="TestProject")

        with patch('src.service_manager.WorkItemService') as MockService:
            mock_instance = Mock()
            MockService.return_value = mock_instance

            service1 = manager.get_workitem_service()
            service2 = manager.get_workitem_service()

            assert MockService.call_count == 1
            assert service1 is service2
            assert manager._cache_hit_count == 1

    def test_get_workitem_service_uses_default_project(self):
        """Test getting work item service uses default project."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="DefaultProject")

        with patch('src.service_manager.WorkItemService') as MockService:
            mock_instance = Mock()
            MockService.return_value = mock_instance

            service = manager.get_workitem_service()

            MockService.assert_called_once_with(auth, "DefaultProject")

    def test_get_workitem_service_raises_without_project_or_default(self):
        """Test getting work item service raises error without project."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with pytest.raises(ValidationError, match="Project name is required"):
            manager.get_workitem_service()


class TestServiceManagerMixedServices:
    """Test ServiceManager with both sprint and work item services."""

    def test_different_services_for_same_project(self):
        """Test getting different service types for same project."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService') as MockSprint, \
             patch('src.service_manager.WorkItemService') as MockWorkItem:

            mock_sprint = Mock()
            mock_workitem = Mock()
            MockSprint.return_value = mock_sprint
            MockWorkItem.return_value = mock_workitem

            sprint_svc = manager.get_sprint_service("TestProject")
            workitem_svc = manager.get_workitem_service("TestProject")

            assert sprint_svc is not workitem_svc
            assert len(manager._sprint_services) == 1
            assert len(manager._workitem_services) == 1
            assert manager._service_creation_count == 2

    def test_services_cached_independently(self):
        """Test that sprint and work item services are cached independently."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService') as MockSprint, \
             patch('src.service_manager.WorkItemService') as MockWorkItem:

            MockSprint.return_value = Mock()
            MockWorkItem.return_value = Mock()

            # Create both service types for same project
            manager.get_sprint_service("Project1")
            manager.get_workitem_service("Project1")

            # Get them again (should be cached)
            manager.get_sprint_service("Project1")
            manager.get_workitem_service("Project1")

            # Each type created only once
            assert MockSprint.call_count == 1
            assert MockWorkItem.call_count == 1
            assert manager._cache_hit_count == 2


class TestServiceManagerProjectResolution:
    """Test ServiceManager project name resolution."""

    def test_resolve_project_with_explicit_parameter(self):
        """Test resolving project with explicit parameter."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="Default")

        resolved = manager._resolve_project("ExplicitProject")
        assert resolved == "ExplicitProject"

    def test_resolve_project_with_default(self):
        """Test resolving project falls back to default."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="DefaultProject")

        resolved = manager._resolve_project(None)
        assert resolved == "DefaultProject"

    def test_resolve_project_strips_whitespace(self):
        """Test resolving project strips whitespace."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        resolved = manager._resolve_project("  ProjectWithSpaces  ")
        assert resolved == "ProjectWithSpaces"

    def test_resolve_project_raises_without_default(self):
        """Test resolving project raises error without default."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with pytest.raises(ValidationError, match="Project name is required"):
            manager._resolve_project(None)


class TestServiceManagerUtilityMethods:
    """Test ServiceManager utility methods."""

    def test_get_loaded_projects_empty(self):
        """Test getting loaded projects when none exist."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        projects = manager.get_loaded_projects()
        assert projects == []

    def test_get_loaded_projects_with_services(self):
        """Test getting loaded projects with active services."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'), \
             patch('src.service_manager.WorkItemService'):

            manager.get_sprint_service("Project1")
            manager.get_sprint_service("Project2")
            manager.get_workitem_service("Project2")
            manager.get_workitem_service("Project3")

            projects = manager.get_loaded_projects()

            # Should return unique projects, sorted
            assert projects == ["Project1", "Project2", "Project3"]

    def test_clear_project_services(self):
        """Test clearing services for specific project."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'), \
             patch('src.service_manager.WorkItemService'):

            manager.get_sprint_service("Project1")
            manager.get_workitem_service("Project1")
            manager.get_sprint_service("Project2")

            assert len(manager.get_loaded_projects()) == 2

            manager.clear_project_services("Project1")

            assert len(manager.get_loaded_projects()) == 1
            assert "Project2" in manager.get_loaded_projects()
            assert "Project1" not in manager._sprint_services
            assert "Project1" not in manager._workitem_services

    def test_clear_project_services_nonexistent(self):
        """Test clearing services for nonexistent project doesn't error."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        # Should not raise error
        manager.clear_project_services("NonExistent")

    def test_clear_all_services(self):
        """Test clearing all services."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'), \
             patch('src.service_manager.WorkItemService'):

            manager.get_sprint_service("Project1")
            manager.get_sprint_service("Project2")
            manager.get_workitem_service("Project3")

            assert len(manager.get_loaded_projects()) == 3

            manager.clear_all_services()

            assert len(manager.get_loaded_projects()) == 0
            assert len(manager._sprint_services) == 0
            assert len(manager._workitem_services) == 0


class TestServiceManagerStatistics:
    """Test ServiceManager statistics tracking."""

    def test_statistics_initial_state(self):
        """Test statistics in initial state."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="TestProject")

        stats = manager.get_statistics()

        assert stats['loaded_projects'] == 0
        assert stats['sprint_services'] == 0
        assert stats['workitem_services'] == 0
        assert stats['total_services'] == 0
        assert stats['service_creations'] == 0
        assert stats['cache_hits'] == 0
        assert stats['cache_hit_rate_percent'] == 0.0
        assert stats['default_project'] == "TestProject"

    def test_statistics_after_service_creation(self):
        """Test statistics after creating services."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'), \
             patch('src.service_manager.WorkItemService'):

            manager.get_sprint_service("Project1")
            manager.get_sprint_service("Project2")
            manager.get_workitem_service("Project1")

            stats = manager.get_statistics()

            assert stats['loaded_projects'] == 2
            assert stats['sprint_services'] == 2
            assert stats['workitem_services'] == 1
            assert stats['total_services'] == 3
            assert stats['service_creations'] == 3
            assert stats['cache_hits'] == 0

    def test_statistics_cache_hit_rate(self):
        """Test statistics cache hit rate calculation."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'):
            # 1 creation
            manager.get_sprint_service("Project1")
            # 9 cache hits
            for _ in range(9):
                manager.get_sprint_service("Project1")

            stats = manager.get_statistics()

            # 9 hits out of 10 total = 90%
            assert stats['service_creations'] == 1
            assert stats['cache_hits'] == 9
            assert stats['cache_hit_rate_percent'] == 90.0

    def test_statistics_after_clear(self):
        """Test statistics after clearing services."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'):
            manager.get_sprint_service("Project1")
            manager.clear_all_services()

            stats = manager.get_statistics()

            # Counts persist, but active services cleared
            assert stats['loaded_projects'] == 0
            assert stats['sprint_services'] == 0
            assert stats['total_services'] == 0
            assert stats['service_creations'] == 1  # History preserved


class TestServiceManagerStringRepresentation:
    """Test ServiceManager string representation."""

    def test_repr_with_default_project(self):
        """Test __repr__ with default project."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="TestProject")

        repr_str = repr(manager)

        assert "ServiceManager" in repr_str
        assert "default='TestProject'" in repr_str

    def test_repr_with_services(self):
        """Test __repr__ with loaded services."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'), \
             patch('src.service_manager.WorkItemService'):

            manager.get_sprint_service("Project1")
            manager.get_workitem_service("Project1")

            repr_str = repr(manager)

            # Both services are for same project, so should be 1 unique project
            assert "projects=1" in repr_str
            assert "services=2" in repr_str
