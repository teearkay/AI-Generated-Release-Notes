"""
Azure authentication utilities for local development.
Uses Azure CLI for authentication and managed identity setup.
"""

import os
import subprocess
import json
import logging
import platform
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_az_command():
    """Get the correct az command based on the operating system."""
    if platform.system() == "Windows":
        return "az.cmd"
    return "az"


def get_storage_account_resource_group(storage_account_name: str) -> Optional[str]:
    """Get the resource group name for a given storage account using Azure CLI."""
    try:
        result = subprocess.run([
            get_az_command(), "storage", "account", "show",
            "--name", storage_account_name,
            "--query", "resourceGroup",
            "-o", "tsv"
        ], capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"Failed to get resource group for storage account {storage_account_name}: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Exception while getting resource group: {e}")
        return None


class AzureCliAuth:
    """Utility class for Azure CLI authentication and identity management."""
    
    @staticmethod
    def is_azure_cli_logged_in() -> bool:
        """Check if user is logged in to Azure CLI."""
        try:
            logger.debug("AUTH: Checking Azure CLI login status")
            result = subprocess.run(
                [get_az_command(), "account", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            is_logged_in = result.returncode == 0
            
            if is_logged_in:
                logger.info("AUTH: User is logged in to Azure CLI")
                # Try to get basic account info for logging
                try:
                    account_data = json.loads(result.stdout)
                    user_name = account_data.get('user', {}).get('name', 'Unknown')
                    subscription_name = account_data.get('name', 'Unknown')
                    logger.info(f"AUTH: Current user: {user_name}")
                    logger.info(f"AUTH: Current subscription: {subscription_name}")
                except Exception as parse_error:
                    logger.debug(f"AUTH: Could not parse account info: {parse_error}")
            else:
                logger.warning("AUTH: User is NOT logged in to Azure CLI")
                logger.debug(f"AUTH: CLI error: {result.stderr}")
            
            return is_logged_in
        except Exception as e:
            logger.error(f"AUTH: Failed to check Azure CLI login status: {e}")
            return False
    
    @staticmethod
    def get_current_user_info() -> Optional[Dict[str, Any]]:
        """Get current Azure CLI user information."""
        try:
            result = subprocess.run(
                [get_az_command(), "account", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get user info: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    @staticmethod
    def get_user_object_id() -> Optional[str]:
        """Get the current user's object ID from Azure AD."""
        try:
            # First try to get from signed-in user
            result = subprocess.run(
                [get_az_command(), "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Fallback: get from account info
            account_info = AzureCliAuth.get_current_user_info()
            if account_info and "user" in account_info:
                user_info = account_info["user"]
                if "name" in user_info:
                    # Try to get object ID by UPN
                    result = subprocess.run([
                        get_az_command(), "ad", "user", "show", 
                        "--id", user_info["name"], 
                        "--query", "id", "-o", "tsv"
                    ], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        return result.stdout.strip()
            
            logger.error("Could not retrieve user object ID")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user object ID: {e}")
            return None
    
    @staticmethod
    def check_storage_account_permissions(storage_account_name: str) -> bool:
        """Check if the current user has required permissions on the storage account."""
        try:
            required_roles = [
                "Storage Blob Data Contributor",
                "Storage Queue Data Contributor", 
                "Storage Table Data Contributor"
            ]
            
            logger.info(f"Checking permissions for storage account: {storage_account_name}")
            
            # Get resource group for the storage account
            resource_group = get_storage_account_resource_group(storage_account_name)
            if not resource_group:
                logger.warning("Could not determine resource group for storage account.")
                return False
            
            # Get current user's object ID
            object_id = AzureCliAuth.get_user_object_id()
            if not object_id:
                logger.warning("Could not get user object ID to check permissions")
                return False
            
            # Use the correct scope for the storage account
            scope = f"/subscriptions/{os.environ.get('AZURE_SUBSCRIPTION_ID', '')}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
            
            # Check role assignments
            result = subprocess.run([
                get_az_command(), "role", "assignment", "list",
                "--assignee", object_id,
                "--scope", scope,
                "--query", "[].roleDefinitionName",
                "-o", "json"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                assigned_roles = json.loads(result.stdout)
                missing_roles = [role for role in required_roles if role not in assigned_roles]
                
                if not missing_roles:
                    logger.info("✅ User has all required storage permissions")
                    return True
                else:
                    logger.warning(f"⚠️  Missing required roles: {missing_roles}")
                    logger.info(f"To grant permissions, run:")
                    for role in missing_roles:
                        logger.info(f"az role assignment create --assignee {object_id} --role '{role}' --scope {scope}")
                    return False
            else:
                logger.error(f"Failed to check role assignments: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking storage permissions: {e}")
            return False
    
    @staticmethod
    def setup_environment_variables() -> bool:
        """Set up environment variables for Azure authentication."""
        try:
            if not AzureCliAuth.is_azure_cli_logged_in():
                logger.error("Not logged in to Azure CLI. Please run 'az login' first.")
                return False
            
            # Get account information
            account_info = AzureCliAuth.get_current_user_info()
            if not account_info:
                logger.error("Could not get Azure account information")
                return False
            
            # Set environment variables
            os.environ["AZURE_SUBSCRIPTION_ID"] = account_info.get("id", "")
            os.environ["AZURE_TENANT_ID"] = account_info.get("tenantId", "")
            
            # Get user object ID
            object_id = AzureCliAuth.get_user_object_id()
            if object_id:
                os.environ["AZURE_USER_OBJECT_ID"] = object_id
                logger.info(f"Set user object ID: {object_id}")
            
            logger.info(f"Azure environment configured for subscription: {account_info.get('name')}")
            logger.info(f"Tenant: {account_info.get('tenantId')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Azure environment: {e}")
            return False
    
    @staticmethod
    def login_if_needed() -> bool:
        """Login to Azure CLI if not already logged in."""
        if AzureCliAuth.is_azure_cli_logged_in():
            logger.info("Already logged in to Azure CLI")
            return True
        
        try:
            logger.info("Logging in to Azure CLI...")
            result = subprocess.run(
                [get_az_command(), "login"],
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to login to Azure CLI: {e}")
            return False


def setup_azure_auth_for_local_dev() -> bool:
    """
    Set up Azure authentication for local development.
    This function should be called during application startup.
    """
    logger.info("Setting up Azure authentication for local development...")
    
    # Try to set up environment variables
    if AzureCliAuth.setup_environment_variables():
        logger.info("✅ Azure authentication configured successfully")
        
        # Check storage account permissions
        storage_account_name = "releasenotegeneratorappm"
        logger.info(f"Checking permissions for storage account: {storage_account_name}")
        
        if AzureCliAuth.check_storage_account_permissions(storage_account_name):
            logger.info("✅ Storage account permissions verified")
        else:
            logger.warning("⚠️  Storage account permissions need to be configured")
            logger.info("Your Azure administrator needs to grant you the following roles:")
            logger.info("- Storage Blob Data Contributor")
            logger.info("- Storage Queue Data Contributor") 
            logger.info("- Storage Table Data Contributor")
            logger.info(f"On storage account: {storage_account_name}")
        
        return True
    else:
        logger.warning("⚠️  Azure authentication setup failed")
        logger.info("To fix this, please run: az login")
        return False


if __name__ == "__main__":
    # Test the authentication setup
    setup_azure_auth_for_local_dev()
