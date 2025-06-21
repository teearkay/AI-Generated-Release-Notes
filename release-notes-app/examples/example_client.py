"""
Example client for testing the refactored release notes generator.
This script demonstrates how to call the Azure Function endpoints.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
FUNCTION_APP_URL = "http://localhost:7071"  # Local development URL
# FUNCTION_APP_URL = "https://your-function-app.azurewebsites.net"  # Production URL

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{FUNCTION_APP_URL}/api/health")
        
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")

def test_single_work_item():
    """Test single work item processing."""
    print("\n🔍 Testing single work item processing...")
    
    # Sample work item data
    work_item_data = {
        "single": True,
        "payload": {
            "workItemId": "12345",
            "title": "Fix authentication timeout issue",
            "description": "Users are experiencing timeout issues when logging in through SSO. The authentication service needs to be updated to handle longer response times.",
            "type": "Bug",
            "assignedTo": "dev-team@company.com",
            "comments": [
                "Initial investigation shows timeout after 30 seconds",
                "Need to increase timeout threshold",
                "Updated authentication service configuration"
            ],
            "labels": ["authentication", "sso", "timeout", "critical"]
        },
        "documentation": None  # Use default semantic configuration
    }
    
    try:
        # Start orchestration
        response = requests.post(
            f"{FUNCTION_APP_URL}/api/orchestrators/release_note_orchestrator",
            json=work_item_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 202:
            print("✅ Orchestration started successfully")
            orchestration_urls = response.json()
            
            # Poll for completion
            print("⏳ Waiting for completion...")
            status_url = orchestration_urls.get("statusQueryGetUri")
            
            if status_url:
                result = poll_for_completion(status_url)
                if result:
                    print("✅ Release note generated:")
                    print(f"   {result}")
                else:
                    print("❌ Failed to get result")
            else:
                print("❌ No status URL provided")
        else:
            print(f"❌ Failed to start orchestration: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

def test_bulk_work_items():
    """Test bulk work item processing."""
    print("\n🔍 Testing bulk work item processing...")
    
    # Sample bulk data
    bulk_data = {
        "single": False,
        "payload": [
            {
                "id": "WI-001",
                "title": "Improve dashboard loading speed",
                "type": "Enhancement",
                "impact": "Faster user experience"
            },
            {
                "id": "WI-002", 
                "title": "Fix email notification bug",
                "type": "Bug Fix",
                "impact": "Reliable email delivery"
            },
            {
                "id": "WI-003",
                "title": "Add new user permission system",
                "type": "New Feature", 
                "impact": "Better security and access control"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{FUNCTION_APP_URL}/api/orchestrators/release_note_orchestrator",
            json=bulk_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 202:
            print("✅ Bulk orchestration started successfully")
            orchestration_urls = response.json()
            
            # Poll for completion
            print("⏳ Waiting for completion...")
            status_url = orchestration_urls.get("statusQueryGetUri")
            
            if status_url:
                result = poll_for_completion(status_url)
                if result:
                    print("✅ Bulk release notes generated:")
                    print(f"   {result}")
                else:
                    print("❌ Failed to get result")
            else:
                print("❌ No status URL provided")
        else:
            print(f"❌ Failed to start bulk orchestration: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

def poll_for_completion(status_url: str, max_attempts: int = 10) -> str:
    """Poll the orchestration status until completion."""
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(status_url)
            
            if response.status_code == 200:
                status_data = response.json()
                runtime_status = status_data.get("runtimeStatus")
                
                if runtime_status == "Completed":
                    return status_data.get("output", "No output available")
                elif runtime_status == "Failed":
                    print(f"❌ Orchestration failed: {status_data.get('output', 'Unknown error')}")
                    return None
                elif runtime_status in ["Running", "Pending"]:
                    print(f"   Status: {runtime_status}, waiting...")
                    time.sleep(2)
                else:
                    print(f"❌ Unexpected status: {runtime_status}")
                    return None
            else:
                print(f"❌ Error checking status: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error polling status: {e}")
            return None
    
    print("❌ Timeout waiting for completion")
    return None

def test_invalid_input():
    """Test error handling with invalid input."""
    print("\n🔍 Testing error handling...")
    
    # Invalid input - missing required fields
    invalid_data = {
        "invalid": "data"
    }
    
    try:
        response = requests.post(
            f"{FUNCTION_APP_URL}/api/orchestrators/release_note_orchestrator",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print("✅ Error handling works correctly")
            print(f"   Error message: {response.text}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Refactored Release Notes Generator")
    print("=" * 50)
    
    # Run tests
    test_health_check()
    test_single_work_item()
    test_bulk_work_items()
    test_invalid_input()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")
    print("\nNote: These tests require the Azure Function to be running.")
    print("Start the function with: func host start")
