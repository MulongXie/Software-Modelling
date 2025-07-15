#!/usr/bin/env python3
"""
Example usage of WebExplorer with a real website.
This demonstrates the core functionality of the web analysis system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_explorer import WebExplorer


def analyze_website(url):
    """
    Analyze a website and display the results.
    
    Args:
        url: URL to analyze
    """
    print(f"🔍 Analyzing website: {url}")
    print("=" * 60)
    
    # Create WebExplorer instance
    explorer = WebExplorer(max_pages=1, delay=1.0)
    
    # Analyze the URL
    page = explorer.analyze_url(url)
    
    if not page:
        print("❌ Failed to analyze the website")
        return
    
    # Display basic information
    print(f"\n📄 Page Information:")
    print(f"   Title: {page.title}")
    print(f"   URL: {page.url}")
    print(f"   Domain: {page.domain}")
    print(f"   Elements found: {len(page.elements)}")
    print(f"   Links found: {len(page.links)}")
    
    # Show page summary
    summary = explorer.get_page_summary(url)
    if summary:
        print(f"\n📊 Page Summary:")
        print(f"   Total elements: {summary['total_elements']}")
        print(f"   High priority elements: {summary['high_priority_elements']}")
        print(f"   Processing time: {summary['load_time']:.2f}s")
        
        print(f"\n🏷️ Elements by type:")
        for element_type, count in summary['elements_by_type'].items():
            print(f"   {element_type}: {count}")
    
    # Show top priority elements
    print(f"\n⭐ Top 10 Priority Elements:")
    prioritized = explorer.get_prioritized_elements(url)
    for i, element in enumerate(prioritized[:10]):
        print(f"   {i+1}. {element.tag} ({element.element_type}) - Score: {element.priority_score:.3f}")
        text_preview = element.text[:50] + "..." if len(element.text) > 50 else element.text
        print(f"      Text: '{text_preview}'")
        if element.attributes.get('class'):
            print(f"      Classes: {element.attributes['class']}")
        print()
    
    # Show navigation elements specifically
    nav_elements = explorer.get_prioritized_elements(url, "navigation")
    if nav_elements:
        print(f"\n🧭 Navigation Elements:")
        for i, element in enumerate(nav_elements):
            print(f"   {i+1}. {element.tag} - Score: {element.priority_score:.3f}")
            print(f"      Text: '{element.text}'")
            print(f"      Attributes: {element.attributes}")
            print()
    
    # Show button elements
    button_elements = explorer.get_prioritized_elements(url, "button")
    if button_elements:
        print(f"\n🔘 Button Elements:")
        for i, element in enumerate(button_elements):
            print(f"   {i+1}. {element.tag} - Score: {element.priority_score:.3f}")
            print(f"      Text: '{element.text}'")
            print(f"      Attributes: {element.attributes}")
            print()
    
    # Show discovered links
    links = explorer.discover_links(url)
    if links:
        print(f"\n🔗 Discovered Links (first 10):")
        for i, link in enumerate(list(links)[:10]):
            print(f"   {i+1}. {link}")
    
    # Show exploration stats
    stats = explorer.get_stats()
    print(f"\n📈 Exploration Statistics:")
    print(f"   Pages analyzed: {stats['pages_analyzed']}")
    print(f"   Failed URLs: {stats['failed_urls']}")
    print(f"   Total elements: {stats['total_elements']}")
    print(f"   Discovered URLs: {stats['discovered_urls']}")
    
    print("\n✅ Analysis complete!")


def main():
    """Main function to run the example"""
    # Example websites to analyze
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://quotes.toscrape.com/",
    ]
    
    if len(sys.argv) > 1:
        # Use URL from command line argument
        url = sys.argv[1]
        analyze_website(url)
    else:
        # Use default test URL
        print("🌐 WebExplorer Example Usage")
        print("=" * 60)
        print("This example will analyze a website and show prioritized elements.")
        print("Usage: python example_usage.py <URL>")
        print("Or run without arguments to use default test URL")
        print()
        
        # Use first test URL as default
        url = test_urls[0]
        analyze_website(url)


if __name__ == "__main__":
    main() 