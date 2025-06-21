#!/usr/bin/env python3
"""
Integration test for Azure Functions Release Notes Generator.
Tests the complete orchestration flow including HTTP trigger and durable functions.

Usage:
  python tests/integration/test_orchestration.py
  python -m pytest tests/integration/test_orchestration.py -v
"""

import requests
import json
import time
import sys
from typing import Dict, Any


def log_print(message: str) -> None:
    """Print and flush message for real-time output."""
    print(message)
    sys.stdout.flush()


def get_test_payload() -> Dict[str, Any]:
    """Get standardized test payload for work item processing."""
    return {
        "single": True,
        "payload": {
            "Id": "4349057",
            "Title": "Make HF and test for the HM Migration False Positive bug, also the ACIS addition to correct existing phone numbers.",
            "AreaPath": "OneCRM\\CRM\\Service\\OmniChannel\\CMP\\Channel Management",
            "Type": "Task",
            "ReproSteps": "",
            "Comments": "[\"Copied with all links from #4317045\"]"
        }
    }


def test_health_endpoint() -> bool:
    """Test the health check endpoint."""
    base_url = "http://localhost:7071"
    
    try:
        log_print("[HEALTH] Testing health endpoint...")
        response = requests.get(f"{base_url}/api/health", timeout=30)
        
        if response.status_code == 200:
            log_print("[OK] Health check passed")
            return True
        else:
            log_print(f"[ERROR] Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        log_print(f"[ERROR] Health check exception: {str(e)}")
        return False


def test_orchestration_flow() -> bool:
    """Test the complete orchestration flow with proper status handling."""
    base_url = "http://localhost:7071"
    test_data = get_test_payload()
    
    try:
        log_print("[TEST] Testing release note orchestration...")
        log_print(f"[SEND] Sending payload for work item: {test_data['payload']['Id']}")
        log_print(f"[SEND] Work item title: {test_data['payload']['Title'][:60]}...")
        
        # Start orchestration
        url = f"{base_url}/api/orchestrators/release_note_orchestrator"
        headers = {"Content-Type": "application/json"}
        
        log_print(f"[REQUEST] POST {url}")
        response = requests.post(url, json=test_data, headers=headers, timeout=90)
        
        if response.status_code == 202:
            # Expected response for durable function orchestration
            log_print("[OK] Orchestration started successfully (HTTP 202)")
            data = response.json()
            
            # Extract status query URI
            status_uri = data.get("statusQueryGetUri")
            if status_uri:
                log_print(f"[MONITOR] Status URI: {status_uri}")
                return monitor_orchestration_status(status_uri)
            else:
                log_print("[ERROR] No statusQueryGetUri in response")
                log_print(f"[DEBUG] Response data: {json.dumps(data, indent=2)}")
                return False
                
        elif response.status_code == 200:
            # Immediate completion (less common for orchestrations)
            log_print("[OK] Orchestration completed immediately (HTTP 200)")
            data = response.json()
            log_print(f"[OUTPUT] Immediate result: {json.dumps(data, indent=2)}")
            return True
            
        else:
            log_print(f"[ERROR] Request failed: {response.status_code}")
            log_print(f"[ERROR] Response: {response.text}")
            return False
            
    except Exception as e:
        log_print(f"[ERROR] Exception in orchestration test: {str(e)}")
        return False


def monitor_orchestration_status(status_uri: str) -> bool:
    """Monitor orchestration status until completion with proper 202/200 handling."""
    try:
        start_time = time.time()
        max_wait_time = 300  # 5 minutes
        retry_interval = 5  # seconds
        
        log_print(f"[MONITOR] Starting status monitoring with {max_wait_time}s timeout")
        
        while time.time() - start_time < max_wait_time:
            try:
                status_response = requests.get(status_uri, timeout=30)
                
                # Handle both 200 (completed) and 202 (still running) status codes
                if status_response.status_code in [200, 202]:
                    status_data = status_response.json()
                    status = status_data.get("runtimeStatus", "Unknown")
                    
                    elapsed_time = time.time() - start_time
                    log_print(f"[STATUS] {status} (elapsed: {elapsed_time:.1f}s, http: {status_response.status_code})")
                    
                    if status == "Completed":
                        log_print("[SUCCESS] Orchestration completed successfully!")
                        if "output" in status_data:
                            output = status_data["output"]
                            if output:
                                log_print(f"[OUTPUT] Generated release note: {json.dumps(output, indent=2)}")
                            else:
                                log_print("[WARN] Orchestration completed but no output received")
                        return True
                        
                    elif status == "Failed":
                        log_print("[ERROR] Orchestration failed")
                        if "output" in status_data:
                            log_print(f"[ERROR] Error details: {json.dumps(status_data['output'], indent=2)}")
                        return False
                        
                    elif status == "Terminated":
                        log_print("[ERROR] Orchestration was terminated")
                        return False
                        
                    elif status in ["Running", "Pending"]:
                        log_print(f"[INFO] Orchestration {status.lower()}... waiting {retry_interval}s")
                        time.sleep(retry_interval)
                        continue
                        
                    else:
                        log_print(f"[WARN] Unknown status '{status}', continuing to monitor...")
                        time.sleep(retry_interval)
                        continue
                        
                elif status_response.status_code == 404:
                    log_print("[ERROR] Status endpoint not found - orchestration may have expired")
                    return False
                    
                else:
                    log_print(f"[ERROR] Status check failed with HTTP {status_response.status_code}")
                    log_print(f"[ERROR] Response: {status_response.text}")
                    
                    # For non-2xx responses, wait and retry
                    log_print(f"[RETRY] Retrying status check in {retry_interval}s...")
                    time.sleep(retry_interval)
                    continue
                    
            except requests.exceptions.Timeout:
                log_print("[WARN] Status check timeout, retrying...")
                time.sleep(retry_interval)
                continue
                
            except requests.exceptions.ConnectionError:
                log_print("[WARN] Connection error during status check, retrying...")
                time.sleep(retry_interval)
                continue
        
        log_print(f"[TIMEOUT] Orchestration monitoring timed out after {max_wait_time}s")
        return False
        
    except Exception as e:
        log_print(f"[ERROR] Unexpected error monitoring orchestration: {str(e)}")
        return False


def test_orchestration():
    """Pytest-compatible test function."""
    log_print("[TEST] Running Azure Functions integration tests")
    log_print("=" * 50)
    
    # Test health endpoint first
    health_ok = test_health_endpoint()
    if not health_ok:
        log_print("[FAIL] Health check failed - ensure Functions host is running")
        assert False, "Health check failed"
    
    # Test orchestration
    orchestration_ok = test_orchestration_flow()
    if not orchestration_ok:
        log_print("[FAIL] Orchestration test failed")
        assert False, "Orchestration test failed"
    
    log_print("[SUCCESS] All integration tests passed!")
    return True


def main():
    """Main function for direct script execution."""
    try:
        success = test_orchestration()
        sys.exit(0 if success else 1)
    except Exception as e:
        log_print(f"[ERROR] Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
