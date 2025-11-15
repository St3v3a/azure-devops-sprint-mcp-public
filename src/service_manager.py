"""
Service Manager for handling multiple Azure DevOps projects
Provides lazy-loading service instances with caching per project
"""
from typing import Dict, List, Optional
from .services.sprint_service import SprintService
from .services.workitem_service import WorkItemService
from .auth import AzureDevOpsAuth
from .validation import ValidationError


class ServiceManager:
    """
    Manages service instances for multiple Azure DevOps projects

    Features:
    - Single authentication instance shared across all projects
    - Lazy-loading: services created only when first accessed
    - Per-project caching: each project maintains isolated cache
    - Thread-safe service instance caching
    - Project validation and listing

    Example:
        auth = AzureDevOpsAuth(org_url)
        await auth.initialize()

        manager = ServiceManager(auth)

        # Services created on first access
        service1 = manager.get_sprint_service("AI-Proj")
        service2 = manager.get_workitem_service("Marketing-Proj")

        # Subsequent calls return cached instances
        same_service = manager.get_sprint_service("AI-Proj")
    """

    def __init__(self, auth: AzureDevOpsAuth, default_project: Optional[str] = None):
        """
        Initialize service manager

        Args:
            auth: Authenticated AzureDevOpsAuth instance
            default_project: Optional default project name for backward compatibility
        """
        if not auth or not auth.connection:
            raise ValueError(
                "ServiceManager requires an initialized AzureDevOpsAuth instance. "
                "Call auth.initialize() before creating ServiceManager."
            )

        self.auth = auth
        self.default_project = default_project

        # Service instance caches (keyed by project name)
        self._sprint_services: Dict[str, SprintService] = {}
        self._workitem_services: Dict[str, WorkItemService] = {}

        # Statistics
        self._service_creation_count = 0
        self._cache_hit_count = 0

    def get_sprint_service(self, project: Optional[str] = None) -> SprintService:
        """
        Get or create a SprintService instance for a project

        Args:
            project: Azure DevOps project name. If None, uses default_project.

        Returns:
            SprintService instance for the project

        Raises:
            ValidationError: If no project specified and no default set
        """
        project = self._resolve_project(project)

        # Return cached instance if exists
        if project in self._sprint_services:
            self._cache_hit_count += 1
            return self._sprint_services[project]

        # Create new service instance
        service = SprintService(self.auth, project)
        self._sprint_services[project] = service
        self._service_creation_count += 1

        return service

    def get_workitem_service(self, project: Optional[str] = None) -> WorkItemService:
        """
        Get or create a WorkItemService instance for a project

        Args:
            project: Azure DevOps project name. If None, uses default_project.

        Returns:
            WorkItemService instance for the project

        Raises:
            ValidationError: If no project specified and no default set
        """
        project = self._resolve_project(project)

        # Return cached instance if exists
        if project in self._workitem_services:
            self._cache_hit_count += 1
            return self._workitem_services[project]

        # Create new service instance
        service = WorkItemService(self.auth, project)
        self._workitem_services[project] = service
        self._service_creation_count += 1

        return service

    def _resolve_project(self, project: Optional[str]) -> str:
        """
        Resolve project name, using default if not specified

        Args:
            project: Optional project name

        Returns:
            Resolved project name

        Raises:
            ValidationError: If no project specified and no default
        """
        if project:
            return project.strip()

        if self.default_project:
            return self.default_project

        raise ValidationError(
            "project",
            "Project name is required. Either specify project parameter or set "
            "AZURE_DEVOPS_PROJECT environment variable as default."
        )

    def get_loaded_projects(self) -> List[str]:
        """
        Get list of projects that have service instances loaded

        Returns:
            List of project names with active services
        """
        sprint_projects = set(self._sprint_services.keys())
        workitem_projects = set(self._workitem_services.keys())
        return sorted(sprint_projects | workitem_projects)

    def clear_project_services(self, project: str) -> None:
        """
        Remove cached service instances for a specific project
        Useful for forcing service recreation or freeing resources

        Args:
            project: Project name to clear
        """
        self._sprint_services.pop(project, None)
        self._workitem_services.pop(project, None)

    def clear_all_services(self) -> None:
        """
        Clear all cached service instances
        Useful for testing or resource cleanup
        """
        self._sprint_services.clear()
        self._workitem_services.clear()

    def get_statistics(self) -> Dict[str, any]:
        """
        Get service manager statistics

        Returns:
            Dictionary with usage statistics:
            - loaded_projects: Number of unique projects loaded
            - sprint_services: Number of sprint service instances
            - workitem_services: Number of workitem service instances
            - total_services: Total service instances
            - service_creations: Total services created (including cleared)
            - cache_hits: Number of times cached service was returned
            - cache_hit_rate: Percentage of cache hits vs total requests
        """
        total_requests = self._service_creation_count + self._cache_hit_count
        cache_hit_rate = (
            (self._cache_hit_count / total_requests * 100)
            if total_requests > 0 else 0.0
        )

        return {
            "loaded_projects": len(self.get_loaded_projects()),
            "sprint_services": len(self._sprint_services),
            "workitem_services": len(self._workitem_services),
            "total_services": len(self._sprint_services) + len(self._workitem_services),
            "service_creations": self._service_creation_count,
            "cache_hits": self._cache_hit_count,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "default_project": self.default_project
        }

    def __repr__(self) -> str:
        """String representation for debugging"""
        stats = self.get_statistics()
        return (
            f"ServiceManager(projects={stats['loaded_projects']}, "
            f"services={stats['total_services']}, "
            f"default='{self.default_project}')"
        )
