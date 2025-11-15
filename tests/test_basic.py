"""
Basic tests for Azure DevOps Sprint MCP Server
Run with: pytest tests/
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import os


class TestAuthentication:
    """Test authentication functionality"""
    
    @pytest.mark.asyncio
    async def test_auth_initialization(self):
        """Test that auth initializes correctly"""
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG_URL': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PAT': 'test-token'
        }):
            from src.auth import AzureDevOpsAuth
            
            auth = AzureDevOpsAuth('https://dev.azure.com/test')
            # Note: actual initialization would require real credentials
            # This is just a structure test
            assert auth.organization_url == 'https://dev.azure.com/test'
    
    def test_auth_info(self):
        """Test auth info retrieval"""
        from src.auth import AzureDevOpsAuth
        
        auth = AzureDevOpsAuth('https://dev.azure.com/test')
        info = auth.get_auth_info()
        
        assert 'organization_url' in info
        assert info['organization_url'] == 'https://dev.azure.com/test'


class TestWorkItemService:
    """Test work item service"""
    
    def test_service_initialization(self):
        """Test service initializes with proper dependencies"""
        from src.services.workitem_service import WorkItemService
        
        mock_auth = Mock()
        service = WorkItemService(mock_auth, 'TestProject')
        
        assert service.project == 'TestProject'
        assert service.auth == mock_auth


class TestSprintService:
    """Test sprint service"""
    
    def test_service_initialization(self):
        """Test service initializes with proper dependencies"""
        from src.services.sprint_service import SprintService
        
        mock_auth = Mock()
        service = SprintService(mock_auth, 'TestProject')
        
        assert service.project == 'TestProject'
        assert service.auth == mock_auth


# Integration test placeholder
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_work_items_integration():
    """
    Integration test for getting work items
    Requires real Azure DevOps credentials
    """
    # Skip if credentials not available
    if not os.getenv('AZURE_DEVOPS_ORG_URL'):
        pytest.skip('Azure DevOps credentials not configured')
    
    # This would be a real integration test
    # from src.auth import AzureDevOpsAuth
    # from src.services.workitem_service import WorkItemService
    # 
    # auth = AzureDevOpsAuth(os.getenv('AZURE_DEVOPS_ORG_URL'))
    # await auth.initialize()
    # 
    # service = WorkItemService(auth, os.getenv('AZURE_DEVOPS_PROJECT'))
    # items = await service.get_my_work_items()
    # 
    # assert isinstance(items, list)
    pass
