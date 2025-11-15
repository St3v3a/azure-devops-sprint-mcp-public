"""
Authentication handling for Azure DevOps
Supports both Azure Managed Identity and Personal Access Tokens
"""
import os
import sys
from typing import Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import asyncio


class AzureDevOpsAuth:
    """
    Handles authentication to Azure DevOps using multiple methods:
    1. Managed Identity (preferred for production)
    2. Service Principal (for automation)
    3. Personal Access Token (for development)
    """
    
    # Azure DevOps resource ID for token acquisition
    AZURE_DEVOPS_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798"
    
    def __init__(self, organization_url: str):
        """
        Initialize authentication handler
        
        Args:
            organization_url: Azure DevOps organization URL 
                            (e.g., https://dev.azure.com/yourorg)
        """
        self.organization_url = organization_url
        self.connection: Optional[Connection] = None
        self._credential = None
        self._auth_method = None
    
    async def initialize(self):
        """Initialize and establish connection to Azure DevOps"""
        # Try different authentication methods in order of preference
        auth_methods = [
            self._try_managed_identity,
            self._try_service_principal,
            self._try_pat
        ]
        
        for auth_method in auth_methods:
            try:
                self.connection = await auth_method()
                if self.connection:
                    print(f"✓ Authenticated using: {self._auth_method}", file=sys.stderr)
                    return
            except Exception as e:
                print(f"✗ {auth_method.__name__} failed: {str(e)}", file=sys.stderr)
                continue
        
        raise ValueError(
            "Failed to authenticate. Please configure one of:\n"
            "1. Azure Managed Identity (recommended)\n"
            "2. Service Principal (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)\n"
            "3. Personal Access Token (AZURE_DEVOPS_PAT)"
        )
    
    async def _try_managed_identity(self) -> Optional[Connection]:
        """
        Attempt authentication using Azure Managed Identity or DefaultAzureCredential
        This works for:
        - Azure VMs with managed identity
        - Azure Functions
        - Azure Container Instances
        - Local development with Azure CLI login
        """
        try:
            credential = DefaultAzureCredential()
            
            # Get token for Azure DevOps
            token = await asyncio.to_thread(
                credential.get_token,
                f"{self.AZURE_DEVOPS_RESOURCE_ID}/.default"
            )
            
            # Use the access token as credentials
            # Azure DevOps accepts the token in the same way as a PAT
            from msrest.authentication import BasicAuthentication
            credentials = BasicAuthentication('', token.token)
            
            self._credential = credential
            self._auth_method = "Azure Managed Identity / DefaultAzureCredential"
            
            return Connection(base_url=self.organization_url, creds=credentials)
            
        except Exception as e:
            raise Exception(f"Managed Identity authentication failed: {str(e)}")
    
    async def _try_service_principal(self) -> Optional[Connection]:
        """
        Attempt authentication using Service Principal
        Requires environment variables:
        - AZURE_CLIENT_ID
        - AZURE_CLIENT_SECRET
        - AZURE_TENANT_ID
        """
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        
        if not all([client_id, client_secret, tenant_id]):
            raise ValueError("Missing service principal credentials")
        
        try:
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Get token for Azure DevOps
            token = await asyncio.to_thread(
                credential.get_token,
                f"{self.AZURE_DEVOPS_RESOURCE_ID}/.default"
            )
            
            credentials = BasicAuthentication('', token.token)
            
            self._credential = credential
            self._auth_method = "Service Principal"
            
            return Connection(base_url=self.organization_url, creds=credentials)
            
        except Exception as e:
            raise Exception(f"Service Principal authentication failed: {str(e)}")
    
    async def _try_pat(self) -> Optional[Connection]:
        """
        Attempt authentication using Personal Access Token
        Requires environment variable: AZURE_DEVOPS_PAT
        
        Note: PATs are convenient but less secure than managed identity.
        Use only for development/testing.
        """
        pat = os.getenv("AZURE_DEVOPS_PAT")
        
        if not pat:
            raise ValueError("AZURE_DEVOPS_PAT environment variable not set")
        
        credentials = BasicAuthentication('', pat)
        
        self._auth_method = "Personal Access Token"
        
        return Connection(base_url=self.organization_url, creds=credentials)
    
    async def _ensure_valid_token(self):
        """
        Automatically refresh token if expired or near expiry.

        This method should be called before any API operation to ensure
        the token is still valid.
        """
        import time

        if self._token_expiry and self._credential:
            current_time = time.time()
            time_until_expiry = self._token_expiry - current_time

            # Refresh if expired or within threshold
            if time_until_expiry <= self._refresh_threshold_seconds:
                logger.info(
                    f"Token expiring in {time_until_expiry:.0f}s, refreshing..."
                )
                await self.refresh_token()

    def get_client(self, client_type: str):
        """
        Get a specific Azure DevOps client
        
        Args:
            client_type: Type of client to get. Options:
                - 'work_item_tracking': For work items
                - 'core': For projects and teams
                - 'work': For boards, sprints, iterations
                
        Returns:
            The requested client instance
        """
        if not self.connection:
            raise RuntimeError("Not authenticated. Call initialize() first.")
        
        client_map = {
            'work_item_tracking': self.connection.clients.get_work_item_tracking_client,
            'core': self.connection.clients.get_core_client,
            'work': self.connection.clients.get_work_client,
        }
        
        if client_type not in client_map:
            raise ValueError(f"Unknown client type: {client_type}")
        
        return client_map[client_type]()
    
    async def refresh_token(self):
        """
        Refresh the authentication token
        Useful for long-running processes
        """
        if self._credential and self._auth_method != "Personal Access Token":
            try:
                token = await asyncio.to_thread(
                    self._credential.get_token,
                    f"{self.AZURE_DEVOPS_RESOURCE_ID}/.default"
                )
                
                # Update connection with new token
                credentials = BasicAuthentication('', token.token)
                self.connection = Connection(
                    base_url=self.organization_url,
                    creds=credentials
                )
                print("✓ Token refreshed successfully")
            except Exception as e:
                print(f"✗ Token refresh failed: {str(e)}")
                raise
    
    async def close(self):
        """Clean up resources"""
        # Close credential if it has a close method
        if hasattr(self._credential, 'close'):
            self._credential.close()
        
        self.connection = None
    
    def get_auth_info(self) -> dict:
        """Get information about current authentication"""
        return {
            "method": self._auth_method,
            "organization_url": self.organization_url,
            "authenticated": self.connection is not None
        }
