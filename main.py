#!/usr/bin/env python3
"""
Minimal test script to verify the basic WebExplorer functionality.
Tests the core navigation and HTML cleaning.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_explorer import WebExplorer


def test_minimal_exploration():
    """Test basic exploration functionality"""
    print("🧪 Testing Minimal WebExplorer")
    print("=" * 50)
    
    # Configuration
    company_name = "test_site"
    start_urls = ["https://httpbin.org/html"]  # Simple test site
    allowed_domains = ["https://httpbin.org"]
    
    # Create WebExplorer instance
    explorer = WebExplorer(
        company_name=company_name,
        start_urls=start_urls,
        allowed_domains=allowed_domains,
        max_state_no=1,  # Just test one page
        headless=True    # Run in headless mode
    )
    
    # Start exploration
    results = explorer.start_exploration()
    
    # Display results
    print(f"\n✅ Test Results:")
    print(f"   Company: {results['company_name']}")
    print(f"   Pages processed: {results['pages_processed']}")
    print(f"   Output directory: {results['output_dir']}")
    
    # Check if screenshot was created
    expected_screenshot = f"{results['output_dir']}/screenshot_1.png"
    if os.path.exists(expected_screenshot):
        print(f"   📸 Screenshot created: {expected_screenshot}")
    else:
        print(f"   ⚠️ Screenshot not found: {expected_screenshot}")
    
    print(f"\n🎉 Basic functionality test completed!")


if __name__ == "__main__":
    try:
        test_minimal_exploration()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 