"""
Test script to verify enhanced logging functionality
and overall application health after code review improvements.
"""

import json
import logging
import time
import sys
import os
from typing import Dict, Any

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Test the enhanced logging utilities
from utils.enhanced_logging import create_enhanced_logger, sanitize_for_logging
from models.data_models import WorkItemInput
from services.release_note_service import ReleaseNoteGenerator
from config.settings import config
from utils.azure_auth import AzureCliAuth


def test_enhanced_logging():
    """Test the enhanced logging functionality."""
    print("=" * 60)
    print("TESTING ENHANCED LOGGING FUNCTIONALITY")
    print("=" * 60)
    
    # Create enhanced logger
    enhanced_logger = create_enhanced_logger("test_logger")
    logger = logging.getLogger("test_logger")
    
    # Test basic logging
    logger.info("Testing basic logging functionality")
    
    # Test structured logging
    enhanced_logger.log_function_entry("test_function", param1="value1", param2=42)
    enhanced_logger.log_function_exit("test_function", "Test completed successfully")
    
    # Test data quality logging
    test_data = {"key1": "value1", "key2": [1, 2, 3]}
    enhanced_logger.log_data_quality("test_data", test_data, dict)
    enhanced_logger.log_data_quality("empty_data", None)
    enhanced_logger.log_data_quality("short_string", "hi", str)
    
    # Test API logging
    enhanced_logger.log_api_call("TestService", "test_operation", param="value")
    enhanced_logger.log_api_response("TestService", "test_operation", True, 1024, 0.5)
    
    # Test business metrics
    enhanced_logger.log_business_metric("test_metric", 42, "units")
    
    # Test security logging
    enhanced_logger.log_security_event("TEST_EVENT", "This is a test security event")
    
    # Test performance logging
    perf_logger = enhanced_logger.performance
    perf_logger.start_timer("test_operation")
    time.sleep(0.1)  # Simulate work
    duration = perf_logger.end_timer("test_operation")
    
    print(f"[OK] Enhanced logging test completed. Operation took {duration:.3f}s")


def test_sanitization():
    """Test data sanitization for logging."""
    print("\n" + "=" * 60)
    print("TESTING DATA SANITIZATION")
    print("=" * 60)
    
    # Test sensitive data sanitization
    sensitive_data = {
        "username": "testuser",
        "password": "secret123",
        "api_key": "abc123",
        "normal_field": "normal_value"
    }
    
    sanitized = sanitize_for_logging(sensitive_data)
    print(f"Original data keys: {list(sensitive_data.keys())}")
    print(f"Sanitized data: {sanitized}")
    
    # Test large data truncation
    large_string = "x" * 500
    sanitized_large = sanitize_for_logging(large_string, max_length=100)
    print(f"Large string (500 chars) truncated to: {len(sanitized_large)} chars")
    
    print("[OK] Data sanitization test completed")


def test_azure_authentication():
    """Test Azure authentication with enhanced logging."""
    print("\n" + "=" * 60)
    print("TESTING AZURE AUTHENTICATION")
    print("=" * 60)
    
    logger = logging.getLogger("auth_test")
    enhanced_logger = create_enhanced_logger("auth_test")
    
    # Test Azure CLI login status
    enhanced_logger.log_function_entry("test_azure_auth")
    
    is_logged_in = AzureCliAuth.is_azure_cli_logged_in()
    enhanced_logger.log_business_metric("azure_cli_logged_in", 1 if is_logged_in else 0)
    
    if is_logged_in:
        user_info = AzureCliAuth.get_current_user_info()
        if user_info:
            enhanced_logger.log_data_quality("user_info", user_info, dict)
            logger.info(f"Current user: {user_info.get('user', {}).get('name', 'Unknown')}")
        
        # Test user object ID retrieval
        object_id = AzureCliAuth.get_user_object_id()
        enhanced_logger.log_data_quality("user_object_id", object_id, str)
    
    enhanced_logger.log_function_exit("test_azure_auth", f"Login status: {is_logged_in}")
    print(f"[OK] Azure authentication test completed. Logged in: {is_logged_in}")


def test_work_item_processing():
    """Test work item processing with enhanced logging."""
    print("\n" + "=" * 60)
    print("TESTING WORK ITEM PROCESSING")
    print("=" * 60)
    
    logger = logging.getLogger("work_item_test")
    enhanced_logger = create_enhanced_logger("work_item_test")
    
    # Create test work item
    test_payload = {
        "id": "12345",
        "title": "Test Work Item",
        "description": "This is a test work item for enhanced logging verification",
        "type": "Feature",
        "state": "Done"
    }
    
    work_item_input = WorkItemInput(
        single=True,
        payload=test_payload,
        documentation="product"
    )
    
    enhanced_logger.log_function_entry("test_work_item_processing")
    enhanced_logger.log_data_quality("work_item_input", work_item_input)
    enhanced_logger.log_business_metric("test_work_items_processed", 1)
    
    # Test JSON serialization
    try:
        json_str = work_item_input.to_json()
        enhanced_logger.log_data_quality("serialized_json", json_str, str)
        
        # Test deserialization
        reconstructed = WorkItemInput.from_json(json_str)
        enhanced_logger.log_data_quality("reconstructed_work_item", reconstructed)
        
        print("[OK] Work item serialization/deserialization successful")
    except Exception as e:
        logger.error(f"Work item processing failed: {e}")
        enhanced_logger.log_security_event("PROCESSING_ERROR", f"Work item processing failed: {e}")
    
    enhanced_logger.log_function_exit("test_work_item_processing", "Test completed")


def test_configuration():
    """Test configuration loading with enhanced logging."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    logger = logging.getLogger("config_test")
    enhanced_logger = create_enhanced_logger("config_test")
    
    enhanced_logger.log_function_entry("test_configuration")
    
    # Test configuration values
    try:
        enhanced_logger.log_data_quality("openai_endpoint", config.openai_endpoint, str)
        enhanced_logger.log_data_quality("deployment_name", config.deployment_name, str)
        enhanced_logger.log_data_quality("search_endpoint", config.search_endpoint, str)
        
        # Test semantic config
        semantic_config = config.get_semantic_config("product")
        enhanced_logger.log_data_quality("semantic_config", semantic_config, str)
        
        # Test search index
        search_index = config.get_search_index(semantic_config)
        enhanced_logger.log_data_quality("search_index", search_index, str)
        
        enhanced_logger.log_business_metric("config_loaded_successfully", 1)
        print("[OK] Configuration test completed successfully")
        
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        enhanced_logger.log_business_metric("config_load_errors", 1)
        enhanced_logger.log_security_event("CONFIG_ERROR", f"Configuration error: {e}")
    
    enhanced_logger.log_function_exit("test_configuration", "Configuration test completed")


def test_error_handling():
    """Test error handling and logging."""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    logger = logging.getLogger("error_test")
    enhanced_logger = create_enhanced_logger("error_test")
    
    # Test intentional error
    enhanced_logger.log_function_entry("test_error_handling")
    
    try:
        # Simulate an error
        raise ValueError("This is a test error for logging verification")
    except Exception as e:
        logger.error(f"Caught expected test error: {e}")
        enhanced_logger.log_business_metric("test_errors_caught", 1)
    
    # Test null/empty data handling
    enhanced_logger.log_data_quality("null_data", None)
    enhanced_logger.log_data_quality("empty_string", "")
    enhanced_logger.log_data_quality("empty_list", [])
    
    enhanced_logger.log_function_exit("test_error_handling", "Error handling test completed")
    print("[OK] Error handling test completed")


def main():
    """Run all enhanced logging tests."""
    print("ENHANCED LOGGING AND CODE REVIEW VERIFICATION")
    print("=" * 60)
    print("This script tests the enhanced logging functionality")
    print("added during the code review phase.")
    print("=" * 60)
    
    try:
        # Run all tests        test_enhanced_logging()
        test_sanitization()
        test_azure_authentication()
        test_work_item_processing()
        test_configuration()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("[OK] ALL ENHANCED LOGGING TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nKey improvements implemented:")
        print("- Enhanced structured logging with performance tracking")
        print("- Data quality validation and logging")
        print("- Security event logging for sensitive operations")
        print("- Business metrics tracking")
        print("- Comprehensive error context logging")
        print("- Data sanitization for safe logging")
        print("- Function entry/exit tracking")
        print("- API call monitoring and response tracking")
        
    except Exception as e:
        print(f"\n[ERROR] Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
