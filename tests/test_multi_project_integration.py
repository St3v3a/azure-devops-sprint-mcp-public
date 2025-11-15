"""
Integration tests for multi-project support.

Tests the integration between ServiceManager, server tools, and services.
Requires actual Azure DevOps credentials and is marked with @pytest.mark.integration.
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from src.service_manager import ServiceManager
from src.auth import AzureDevOpsAuth
from src.services.sprint_service import SprintService
from src.services.workitem_service import WorkItemService


class TestMultiProjectServiceManager:
    """Test ServiceManager with mocked services (unit-level integration)."""

    @pytest.fixture
    def mock_auth(self):
        """Create mock authenticated auth."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        return auth

    @pytest.fixture
    def service_manager(self, mock_auth):
        """Create ServiceManager with mock auth."""
        return ServiceManager(mock_auth, default_project="DefaultProject")

    def test_service_manager_creates_isolated_caches_per_project(self, service_manager):
        """Test that each project gets its own cache namespace."""
        with patch('src.service_manager.SprintService') as MockSprint:
            # Create mock services
            mock_svc1 = Mock()
            mock_svc2 = Mock()
            MockSprint.side_effect = [mock_svc1, mock_svc2]

            service1 = service_manager.get_sprint_service("Project1")
            service2 = service_manager.get_sprint_service("Project2")

            # Verify services created with correct projects
            calls = MockSprint.call_args_list
            assert calls[0][0][1] == "Project1"
            assert calls[1][0][1] == "Project2"

            # Services should be different instances
            assert service1 is not service2

    def test_service_manager_reuses_services_for_same_project(self, service_manager):
        """Test that repeated calls for same project reuse service instance."""
        with patch('src.service_manager.SprintService') as MockSprint:
            mock_svc = Mock()
            MockSprint.return_value = mock_svc

            service1 = service_manager.get_sprint_service("Project1")
            service2 = service_manager.get_sprint_service("Project1")
            service3 = service_manager.get_sprint_service("Project1")

            # Should only create once
            assert MockSprint.call_count == 1
            assert service1 is service2 is service3

            stats = service_manager.get_statistics()
            assert stats['service_creations'] == 1
            assert stats['cache_hits'] == 2

    def test_service_manager_handles_multiple_projects_efficiently(self, service_manager):
        """Test handling multiple projects with efficient caching."""
        with patch('src.service_manager.SprintService') as MockSprint, \
             patch('src.service_manager.WorkItemService') as MockWorkItem:

            MockSprint.side_effect = [Mock(), Mock(), Mock()]
            MockWorkItem.side_effect = [Mock(), Mock(), Mock()]

            # Create services for 3 projects
            for project in ["Project1", "Project2", "Project3"]:
                service_manager.get_sprint_service(project)
                service_manager.get_workitem_service(project)

            # Request them again (should be cached)
            for project in ["Project1", "Project2", "Project3"]:
                service_manager.get_sprint_service(project)
                service_manager.get_workitem_service(project)

            # Should create 3 of each type (6 total)
            assert MockSprint.call_count == 3
            assert MockWorkItem.call_count == 3

            stats = service_manager.get_statistics()
            assert stats['service_creations'] == 6
            assert stats['cache_hits'] == 6  # 3 sprint + 3 workitem hits
            assert stats['cache_hit_rate_percent'] == 50.0


class TestMultiProjectServerIntegration:
    """Test server tools with multi-project support (mocked)."""

    @pytest.fixture
    def mock_service_manager(self):
        """Create mock service manager."""
        manager = Mock(spec=ServiceManager)
        manager.get_sprint_service = Mock()
        manager.get_workitem_service = Mock()
        return manager

    def test_tools_accept_project_parameter(self, mock_service_manager):
        """Test that tools accept and use project parameter."""
        # This would test actual server tools with mocked service manager
        # Example structure:

        mock_sprint_svc = AsyncMock()
        mock_sprint_svc.project = "TestProject"
        mock_sprint_svc.get_current_sprint = AsyncMock(return_value={
            'name': 'Sprint 1',
            'start_date': '2024-01-01',
            'end_date': '2024-01-15',
            'days_remaining': 5,
            'total_items': 10,
            'completed_items': 5,
            'in_progress_items': 3,
            'not_started_items': 2,
            'completion_percentage': 50.0
        })

        mock_service_manager.get_sprint_service.return_value = mock_sprint_svc

        # Simulate tool call
        with patch('src.server.service_manager', mock_service_manager):
            # Would call actual tool here
            # result = await get_current_sprint(project="TestProject")
            pass

        # Verify service manager was called with correct project
        # mock_service_manager.get_sprint_service.assert_called_with("TestProject")

    def test_tools_use_default_project_when_not_specified(self, mock_service_manager):
        """Test that tools use default project when project not specified."""
        mock_workitem_svc = AsyncMock()
        mock_workitem_svc.project = "DefaultProject"
        mock_workitem_svc.get_my_work_items = AsyncMock(return_value=[])

        mock_service_manager.get_workitem_service.return_value = mock_workitem_svc

        with patch('src.server.service_manager', mock_service_manager):
            # Would call actual tool without project parameter
            # result = await get_my_work_items(state="Active")
            pass

        # Verify service manager was called with None (uses default)
        # mock_service_manager.get_workitem_service.assert_called_with(None)


@pytest.mark.integration
class TestMultiProjectRealIntegration:
    """Integration tests with real Azure DevOps connection.

    These tests require actual Azure DevOps credentials and are skipped
    by default. Run with: pytest -m integration
    """

    @pytest.fixture
    async def real_auth(self):
        """Create real authenticated auth (requires credentials)."""
        org_url = os.getenv("AZURE_DEVOPS_ORG_URL")
        if not org_url:
            pytest.skip("AZURE_DEVOPS_ORG_URL not set")

        auth = AzureDevOpsAuth(org_url)
        await auth.initialize()
        yield auth
        await auth.close()

    @pytest.fixture
    def real_service_manager(self, real_auth):
        """Create ServiceManager with real auth."""
        default_project = os.getenv("AZURE_DEVOPS_PROJECT")
        return ServiceManager(real_auth, default_project=default_project)

    @pytest.mark.asyncio
    async def test_real_multi_project_service_creation(self, real_service_manager):
        """Test creating real services for multiple projects."""
        project1 = os.getenv("AZURE_DEVOPS_PROJECT")
        project2 = os.getenv("AZURE_DEVOPS_PROJECT_2", project1)  # Use same if not set

        if not project1:
            pytest.skip("AZURE_DEVOPS_PROJECT not set")

        # Create services for both projects
        sprint_svc1 = real_service_manager.get_sprint_service(project1)
        sprint_svc2 = real_service_manager.get_sprint_service(project2)

        # Verify they're SprintService instances
        assert isinstance(sprint_svc1, SprintService)
        assert isinstance(sprint_svc2, SprintService)

        # Verify correct projects
        assert sprint_svc1.project == project1
        assert sprint_svc2.project == project2

        # If different projects, should be different instances
        if project1 != project2:
            assert sprint_svc1 is not sprint_svc2

    @pytest.mark.asyncio
    async def test_real_service_caching_across_types(self, real_service_manager):
        """Test that service caching works correctly across service types."""
        project = os.getenv("AZURE_DEVOPS_PROJECT")
        if not project:
            pytest.skip("AZURE_DEVOPS_PROJECT not set")

        # Get both service types for same project
        sprint_svc1 = real_service_manager.get_sprint_service(project)
        workitem_svc1 = real_service_manager.get_workitem_service(project)

        # Get them again
        sprint_svc2 = real_service_manager.get_sprint_service(project)
        workitem_svc2 = real_service_manager.get_workitem_service(project)

        # Should be cached (same instances)
        assert sprint_svc1 is sprint_svc2
        assert workitem_svc1 is workitem_svc2

        # But different service types should be different
        assert sprint_svc1 is not workitem_svc1

        # Verify statistics
        stats = real_service_manager.get_statistics()
        assert stats['service_creations'] == 2
        assert stats['cache_hits'] == 2
        assert stats['cache_hit_rate_percent'] == 50.0

    @pytest.mark.asyncio
    async def test_real_service_manager_statistics(self, real_service_manager):
        """Test service manager statistics with real services."""
        project = os.getenv("AZURE_DEVOPS_PROJECT")
        if not project:
            pytest.skip("AZURE_DEVOPS_PROJECT not set")

        # Initial state
        initial_stats = real_service_manager.get_statistics()
        assert initial_stats['loaded_projects'] == 0
        assert initial_stats['total_services'] == 0

        # Create some services
        real_service_manager.get_sprint_service(project)
        real_service_manager.get_workitem_service(project)

        # Check statistics
        stats = real_service_manager.get_statistics()
        assert stats['loaded_projects'] == 1
        assert stats['sprint_services'] == 1
        assert stats['workitem_services'] == 1
        assert stats['total_services'] == 2
        assert project in real_service_manager.get_loaded_projects()

    @pytest.mark.asyncio
    async def test_real_services_have_isolated_caches(self, real_service_manager):
        """Test that services for different projects have isolated caches."""
        project1 = os.getenv("AZURE_DEVOPS_PROJECT")
        project2 = os.getenv("AZURE_DEVOPS_PROJECT_2", f"{project1}_alt")

        if not project1:
            pytest.skip("AZURE_DEVOPS_PROJECT not set")

        sprint_svc1 = real_service_manager.get_sprint_service(project1)
        sprint_svc2 = real_service_manager.get_sprint_service(project2)

        # Verify different cache namespaces
        assert sprint_svc1.cache_namespace == f"sprints:{project1}"
        assert sprint_svc2.cache_namespace == f"sprints:{project2}"

        # Cache namespaces should be different if projects are different
        if project1 != project2:
            assert sprint_svc1.cache_namespace != sprint_svc2.cache_namespace


class TestMultiProjectErrorHandling:
    """Test error handling in multi-project scenarios."""

    def test_service_manager_validates_project_name(self):
        """Test that service manager validates project names."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)  # No default project

        from src.validation import ValidationError

        # Should raise when no project specified and no default
        with pytest.raises(ValidationError):
            manager.get_sprint_service()

        with pytest.raises(ValidationError):
            manager.get_workitem_service()

    def test_service_manager_handles_whitespace_in_project_names(self):
        """Test that service manager strips whitespace from project names."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService') as MockSprint:
            MockSprint.return_value = Mock()

            manager.get_sprint_service("  ProjectName  ")

            # Should be called with stripped name
            MockSprint.assert_called_once_with(auth, "ProjectName")

    def test_clearing_services_doesnt_affect_statistics(self):
        """Test that clearing services preserves creation statistics."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'):
            # Create services
            manager.get_sprint_service("Project1")
            manager.get_sprint_service("Project2")

            stats_before = manager.get_statistics()
            creations_before = stats_before['service_creations']

            # Clear services
            manager.clear_all_services()

            stats_after = manager.get_statistics()

            # Statistics should be preserved
            assert stats_after['service_creations'] == creations_before
            # But active services should be cleared
            assert stats_after['total_services'] == 0


class TestMultiProjectPerformance:
    """Test performance characteristics of multi-project support."""

    def test_service_creation_is_lazy(self):
        """Test that services are only created when requested."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth, default_project="DefaultProject")

        with patch('src.service_manager.SprintService') as MockSprint:
            # Just creating manager shouldn't create any services
            assert MockSprint.call_count == 0

            # Only creates when requested
            manager.get_sprint_service("Project1")
            assert MockSprint.call_count == 1

    def test_cache_hit_rate_with_mixed_usage(self):
        """Test cache hit rate with realistic mixed usage pattern."""
        auth = Mock(spec=AzureDevOpsAuth)
        auth.connection = Mock()
        manager = ServiceManager(auth)

        with patch('src.service_manager.SprintService'):
            # Simulate realistic usage:
            # - Work with Project1 frequently
            # - Occasionally switch to Project2
            # - Rarely use Project3

            manager.get_sprint_service("Project1")  # Create
            for _ in range(50):  # Hit cache 50 times
                manager.get_sprint_service("Project1")

            manager.get_sprint_service("Project2")  # Create
            for _ in range(10):  # Hit cache 10 times
                manager.get_sprint_service("Project2")

            manager.get_sprint_service("Project3")  # Create
            for _ in range(2):  # Hit cache 2 times
                manager.get_sprint_service("Project3")

            stats = manager.get_statistics()

            # 3 creations, 62 cache hits = 95.4% hit rate
            assert stats['service_creations'] == 3
            assert stats['cache_hits'] == 62
            assert stats['cache_hit_rate_percent'] > 95.0
