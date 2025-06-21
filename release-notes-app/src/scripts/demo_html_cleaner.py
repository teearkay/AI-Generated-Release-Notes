#!/usr/bin/env python3
"""
Example script demonstrating HTML cleaning functionality.

This script shows how to use the Azure Function HTML cleaning endpoints
for various HTML cleaning scenarios commonly encountered in web scraping,
document processing, and data cleaning workflows.
"""

import json
import requests
import time
from typing import Dict, Any

def create_sample_scenarios():
    """Create various HTML cleaning test scenarios."""
    
    scenarios = {
        "documentation": """
            <div class="documentation">
                <h1 id="main-title">Product Documentation</h1>
                <div class="nav-menu" style="display: none;">
                    <ul>
                        <li><a href="/docs">Docs</a></li>
                        <li><a href="/api">API</a></li>
                    </ul>
                </div>
                <!-- Release notes section -->
                <section class="release-notes">
                    <h2>Version 2.1.0 Changes</h2>
                    <ul>
                        <li><strong>New Feature:</strong> Enhanced user authentication</li>
                        <li><strong>Bug Fix:</strong> Resolved memory leak in data processing</li>
                        <li><strong>Improvement:</strong> 30% faster query performance</li>
                    </ul>
                    <script>
                        // Analytics tracking
                        gtag('event', 'page_view', {'page_title': 'Release Notes'});
                    </script>
                </section>
                <footer style="margin-top: 50px; color: #666;">
                    <p>Last updated: March 2024</p>
                </footer>
            </div>
        """,
        
        "web_scraping": """
            <!DOCTYPE html>
            <html>
            <head>
                <title>News Article</title>
                <style>
                    .ads { display: block; }
                    .content { font-family: Arial; }
                </style>
            </head>
            <body>
                <div class="header">
                    <nav>Navigation menu</nav>
                </div>
                <main class="content">
                    <h1>Breaking: New Technology Released</h1>
                    <p class="byline">By Reporter Name | March 15, 2024</p>
                    <article>
                        <p>A revolutionary new technology has been announced that will change how we work.</p>
                        <p>The technology promises to deliver <em>significant improvements</em> in productivity.</p>
                        <blockquote>"This is a game changer," said the CEO.</blockquote>
                    </article>
                    <div class="ads">
                        <script>showAds();</script>
                        <p>Advertisement content here</p>
                    </div>
                </main>
                <aside class="sidebar">
                    <h3>Related Articles</h3>
                    <ul>
                        <li><a href="/article1">Article 1</a></li>
                        <li><a href="/article2">Article 2</a></li>
                    </ul>
                </aside>
            </body>
            </html>
        """,
        
        "email_content": """
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: sans-serif; }
                    .header { background: #007ACC; color: white; padding: 20px; }
                    .content { padding: 20px; }
                    .footer { background: #f5f5f5; padding: 10px; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>System Notification</h1>
                </div>
                <div class="content">
                    <p>Dear User,</p>
                    <p>Your system has been successfully updated to version 3.2.1.</p>
                    <h3>What's New:</h3>
                    <ul>
                        <li>Improved security protocols</li>
                        <li>Enhanced user interface</li>
                        <li>Bug fixes and performance improvements</li>
                    </ul>
                    <p>Please <a href="https://example.com/login" onclick="trackClick()">log in</a> to see the changes.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply.</p>
                    <p>&copy; 2024 Company Name. All rights reserved.</p>
                    <img src="tracking-pixel.gif" width="1" height="1" alt="">
                </div>
                <script>
                    function trackClick() {
                        console.log('Link clicked');
                    }
                </script>
            </body>
            </html>
        """
    }
    
    return scenarios

def clean_html_scenarios(base_url: str = "http://localhost:7071"):
    """Test different HTML cleaning scenarios."""
    
    print("🧹 HTML Cleaning Scenarios Demo")
    print("=" * 50)
    
    scenarios = create_sample_scenarios()
    
    for scenario_name, html_content in scenarios.items():
        print(f"\n📄 Scenario: {scenario_name.title()}")
        print("-" * 30)
        
        # Test 1: Plain text extraction
        print("1️⃣ Plain Text Extraction:")
        try:
            payload = {
                "html": html_content,
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
                cleaned_text = result.get('cleaned_text', '')
                
                # Show first 200 characters
                preview = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                print(f"✅ Text extracted ({result.get('cleaned_length', 0)} chars)")
                print(f"Preview: {preview}")
                print(f"Processing time: {result.get('processing_time_ms', 0)}ms")
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Structure preservation
        print("\n2️⃣ Structure Preservation:")
        try:
            payload = {
                "html": html_content,
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
                cleaned_html = result.get('cleaned_text', '')
                
                # Count tags to show structure preservation
                tag_count = cleaned_html.count('<')
                print(f"✅ Structure preserved ({tag_count} HTML tags)")
                print(f"Processing time: {result.get('processing_time_ms', 0)}ms")
                
                # Show HTML structure preview
                lines = cleaned_html.split('\n')
                structure_preview = '\n'.join(lines[:5])
                print(f"Structure preview:\n{structure_preview}")
                
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "─" * 50)

def benchmark_html_cleaning(base_url: str = "http://localhost:7071"):
    """Benchmark HTML cleaning performance."""
    
    print("\n⚡ Performance Benchmark")
    print("=" * 30)
    
    # Create test HTML of different sizes
    test_cases = {
        "Small (1KB)": "<div>" + "<p>Test content</p>" * 10 + "</div>",
        "Medium (10KB)": "<div>" + "<p>Test content with more text here</p>" * 100 + "</div>",
        "Large (50KB)": "<div>" + "<section><h2>Section</h2><p>Content paragraph with significant text</p></section>" * 200 + "</div>"
    }
    
    for size_name, html_content in test_cases.items():
        print(f"\n📊 Testing {size_name}: {len(html_content)} bytes")
        
        try:
            payload = {
                "html": html_content,
                "preserve_structure": False,
                "remove_attributes": True
            }
            
            start_time = time.time()
            response = requests.post(
                f"{base_url}/api/clean-html",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                server_time = result.get('processing_time_ms', 0)
                
                print(f"✅ Success!")
                print(f"   Server processing: {server_time}ms")
                print(f"   Total round-trip: {total_time*1000:.1f}ms")
                print(f"   Original size: {result.get('original_length', 0)} chars")
                print(f"   Cleaned size: {result.get('cleaned_length', 0)} chars")
                print(f"   Compression ratio: {(1 - result.get('cleaned_length', 0) / result.get('original_length', 1)) * 100:.1f}%")
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main demonstration function."""
    
    print("🚀 HTML Cleaning Function Demonstration")
    print("=" * 60)
    
    # Check if function is running
    base_url = "http://localhost:7071"
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Function app is running at {base_url}")
        else:
            print(f"❌ Function app health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to function app: {e}")
        print("Please ensure the Azure Function is running locally with 'func start'")
        return
    
    # Run demonstrations
    clean_html_scenarios(base_url)
    benchmark_html_cleaning(base_url)
    
    print("\n🎉 Demo completed!")
    print("\nUsage Tips:")
    print("• Use preserve_structure=False for pure text extraction")
    print("• Use preserve_structure=True to keep HTML formatting")
    print("• Use /api/clean-html-file for uploaded file processing")
    print("• All scripts and styles are automatically removed")
    print("• Comments and unwanted attributes are cleaned")

if __name__ == "__main__":
    main()
