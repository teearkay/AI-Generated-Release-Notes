#!/usr/bin/env python3
"""
Test script for the HTML cleaning Azure Function.

This script demonstrates how to use the HTML cleaning endpoints
and validates their functionality with sample HTML content.
"""

import json
import requests
import time
from typing import Dict, Any

# Sample HTML content for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample Document</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .highlight { background-color: yellow; }
    </style>
    <script>
        function showAlert() {
            alert('This is a script!');
        }
    </script>
</head>
<body>
    <h1 class="main-title" id="title">Release Notes</h1>
    <!-- This is a comment -->
    <div class="content" style="margin: 20px;">
        <p>This is the main content of the document.</p>
        <ul>
            <li>Feature 1: New user interface</li>
            <li>Feature 2: Improved performance</li>
            <li>Bug fix: Fixed login issue</li>
        </ul>
        <script>showAlert();</script>
    </div>
    <footer onclick="handleClick()">
        <p>Copyright 2024</p>
    </footer>
</body>
</html>
"""

def test_html_cleaner_local():
    """Test the HTML cleaner function locally using BeautifulSoup directly."""
    print("=== Testing HTML Cleaner Locally ===")
    
    try:
        from bs4 import BeautifulSoup
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(SAMPLE_HTML, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()        # Remove comments
        from bs4 import Comment
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
        
        # Get plain text
        plain_text = soup.get_text()
        lines = (line.strip() for line in plain_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
        
        print(f"Original HTML length: {len(SAMPLE_HTML)} characters")
        print(f"Cleaned text length: {len(cleaned_text)} characters")
        print(f"Cleaned text preview: {cleaned_text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Local test failed: {e}")
        return False

def test_html_cleaner_api(base_url: str = "http://localhost:7071"):
    """Test the HTML cleaner API endpoints."""
    print(f"\n=== Testing HTML Cleaner API at {base_url} ===")
    
    # Test 1: Clean HTML with JSON payload
    print("\n1. Testing /api/clean-html endpoint with JSON...")
    
    try:
        payload = {
            "html": SAMPLE_HTML,
            "preserve_structure": False,
            "remove_attributes": True
        }
        
        response = requests.post(
            f"{base_url}/api/clean-html",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Processing time: {result.get('processing_time_ms', 'N/A')}ms")
            print(f"Original length: {result.get('original_length', 'N/A')}")
            print(f"Cleaned length: {result.get('cleaned_length', 'N/A')}")
            print(f"Cleaned text preview: {result.get('cleaned_text', '')[:200]}...")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Test 2: Clean HTML with structure preservation
    print("\n2. Testing /api/clean-html endpoint with structure preservation...")
    
    try:
        payload = {
            "html": SAMPLE_HTML,
            "preserve_structure": True,
            "remove_attributes": False
        }
        
        response = requests.post(
            f"{base_url}/api/clean-html",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Processing time: {result.get('processing_time_ms', 'N/A')}ms")
            print(f"Structure preserved: {result.get('preserve_structure', 'N/A')}")
            print(f"Cleaned HTML preview: {result.get('cleaned_text', '')[:200]}...")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    # Test 3: Clean HTML file endpoint
    print("\n3. Testing /api/clean-html-file endpoint...")
    
    try:
        response = requests.post(
            f"{base_url}/api/clean-html-file",
            headers={"Content-Type": "text/html"},
            data=SAMPLE_HTML.encode('utf-8'),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Processing time: {result.get('processing_time_ms', 'N/A')}ms")
            print(f"Original length: {result.get('original_length', 'N/A')}")
            print(f"Cleaned HTML length: {result.get('cleaned_html_length', 'N/A')}")
            print(f"Plain text length: {result.get('plain_text_length', 'N/A')}")
            print(f"Plain text preview: {result.get('plain_text', '')[:200]}...")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_health_check(base_url: str = "http://localhost:7071"):
    """Test the health check endpoint."""
    print(f"\n=== Testing Health Check at {base_url} ===")
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check passed: {result}")
        else:
            print(f"❌ Health check failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check request failed: {e}")
    except Exception as e:
        print(f"❌ Health check test failed: {e}")

def main():
    """Main test function."""
    print("HTML Cleaner Function Test Suite")
    print("=" * 50)
    
    # Test locally first
    local_success = test_html_cleaner_local()
    
    if not local_success:
        print("❌ Local test failed. Please check BeautifulSoup installation.")
        return
    
    # Test API endpoints
    print("\nTo test the API endpoints, make sure your Azure Function is running locally:")
    print("1. Run: func start")
    print("2. The function should be available at http://localhost:7071")
    print("3. Run this script again to test the API endpoints")
    
    # Ask user if they want to test API
    try:
        test_api = input("\nDo you want to test the API endpoints now? (y/n): ").lower().strip()
        if test_api == 'y':
            base_url = input("Enter the base URL (default: http://localhost:7071): ").strip()
            if not base_url:
                base_url = "http://localhost:7071"
            
            test_health_check(base_url)
            test_html_cleaner_api(base_url)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
