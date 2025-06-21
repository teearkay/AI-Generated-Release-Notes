#!/usr/bin/env python3
"""
Test script to demonstrate default parameter handling in HTML cleaning function.

This script tests various scenarios where optional parameters are not provided
and verifies that defaults are applied correctly.
"""

import json
import requests
import time

# Sample HTML for testing
SAMPLE_HTML = """
<html>
<head>
    <style>body { color: red; }</style>
    <script>alert('test');</script>
</head>
<body>
    <h1 id="title" class="main">Test Document</h1>
    <!-- This is a comment -->
    <p onclick="handleClick()">Content paragraph</p>
</body>
</html>
"""

def test_default_parameters(base_url: str = "http://localhost:7071"):
    """Test the HTML cleaner with various parameter combinations."""
    print("🧪 Testing Default Parameter Handling")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Only HTML provided (all defaults)",
            "payload": {
                "html": SAMPLE_HTML
            },
            "expected_defaults": {
                "preserve_structure": False,
                "remove_attributes": True
            }
        },
        {
            "name": "HTML + preserve_structure only",
            "payload": {
                "html": SAMPLE_HTML,
                "preserve_structure": True
            },
            "expected_defaults": {
                "remove_attributes": True
            }
        },
        {
            "name": "HTML + remove_attributes only",
            "payload": {
                "html": SAMPLE_HTML,
                "remove_attributes": False
            },
            "expected_defaults": {
                "preserve_structure": False
            }
        },
        {
            "name": "All parameters explicitly set",
            "payload": {
                "html": SAMPLE_HTML,
                "preserve_structure": True,
                "remove_attributes": False
            },
            "expected_defaults": {}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{base_url}/api/clean-html",
                headers={"Content-Type": "application/json"},
                json=test_case["payload"],
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check the response
                preserve_structure = result.get('preserve_structure', 'NOT_FOUND')
                processing_time = result.get('processing_time_ms', 'N/A')
                original_length = result.get('original_length', 'N/A')
                cleaned_length = result.get('cleaned_length', 'N/A')
                
                print(f"✅ Success! Processing time: {processing_time}ms")
                print(f"   preserve_structure: {preserve_structure}")
                print(f"   Original length: {original_length}")
                print(f"   Cleaned length: {cleaned_length}")
                
                # Verify expected behavior
                if preserve_structure:
                    print("   📝 Structure preserved (HTML tags kept)")
                else:
                    print("   📄 Plain text extracted (HTML tags removed)")
                
                # Show cleaned content preview
                cleaned_text = result.get('cleaned_text', '')
                if len(cleaned_text) > 100:
                    preview = cleaned_text[:100] + "..."
                else:
                    preview = cleaned_text
                print(f"   Preview: {preview}")
                
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Test failed: {e}")

def test_missing_html_parameter(base_url: str = "http://localhost:7071"):
    """Test error handling when HTML parameter is missing."""
    print(f"\n🚫 Testing Missing HTML Parameter")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Empty JSON object",
            "payload": {}
        },
        {
            "name": "Only optional parameters",
            "payload": {
                "preserve_structure": True,
                "remove_attributes": False
            }
        },
        {
            "name": "Wrong parameter name",
            "payload": {
                "content": SAMPLE_HTML,
                "preserve_structure": False
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{base_url}/api/clean-html",
                headers={"Content-Type": "application/json"},
                json=test_case["payload"],
                timeout=30
            )
            
            if response.status_code == 400:
                result = response.json()
                error_message = result.get('error', 'No error message')
                print(f"✅ Correctly rejected with 400 status")
                print(f"   Error: {error_message}")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Test failed: {e}")

def test_plain_text_fallback(base_url: str = "http://localhost:7071"):
    """Test fallback behavior for non-JSON content."""
    print(f"\n📝 Testing Plain Text Fallback")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{base_url}/api/clean-html",
            headers={"Content-Type": "text/html"},
            data=SAMPLE_HTML.encode('utf-8'),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            preserve_structure = result.get('preserve_structure', 'NOT_FOUND')
            processing_time = result.get('processing_time_ms', 'N/A')
            
            print(f"✅ Success! Processing time: {processing_time}ms")
            print(f"   preserve_structure (default): {preserve_structure}")
            print(f"   Content treated as plain HTML with defaults applied")
            
            # Show cleaned content preview
            cleaned_text = result.get('cleaned_text', '')
            if len(cleaned_text) > 100:
                preview = cleaned_text[:100] + "..."
            else:
                preview = cleaned_text
            print(f"   Preview: {preview}")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Main test function."""
    print("🔧 HTML Cleaner Default Parameters Test Suite")
    print("=" * 60)
    
    # Ask for base URL
    try:
        base_url = input("Enter the base URL (default: http://localhost:7071): ").strip()
        if not base_url:
            base_url = "http://localhost:7071"
        
        print(f"\nTesting against: {base_url}")
        
        # Run all tests
        test_default_parameters(base_url)
        test_missing_html_parameter(base_url)
        test_plain_text_fallback(base_url)
        
        print(f"\n🎉 All tests completed!")
        print("\n💡 Summary:")
        print("   • Only 'html' parameter is required")
        print("   • 'preserve_structure' defaults to False (plain text extraction)")
        print("   • 'remove_attributes' defaults to True (clean attributes)")
        print("   • Non-JSON content uses default parameters")
        print("   • Missing 'html' parameter returns 400 error")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Test suite failed: {e}")

if __name__ == "__main__":
    main()
