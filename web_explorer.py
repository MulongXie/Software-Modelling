import requests
from typing import Dict, List, Optional, Set
from parser.page import Page, PageElement
from parser.parser import HTMLParser
from crawler.crawler import WebCrawler
import time
import os


class WebExplorer:
    """
    Main orchestrator class for web exploration and analysis.
    Manages global elements, coordinates crawler and parser, and stores analysis results.
    """
    
    def __init__(self, company_name, start_urls, allowed_domains, exclude_domains=None, 
                 login_credentials=None, max_state_no=100, output_base_dir="data/crawling"):
        """
        Initialize the WebExplorer.
        Args:
            company_name (str): The name of the company to crawl
            start_urls (list): List of starting URLs
            allowed_domains (list): List of allowed domains to crawl
            exclude_domains (list): List of excluded domains to crawl
            login_credentials (dict): Dictionary containing login credentials
            max_state_no (int): Maximum number of states/pages to analyze
            output_base_dir (str): Base directory for storing crawled data
        """
        # Configuration
        self.company_name = company_name
        self.start_urls = start_urls
        self.allowed_domains = allowed_domains or []
        self.exclude_domains = exclude_domains or []
        self.login_credentials = login_credentials
        self.max_state_no = max_state_no
        self.output_dir = os.path.join(output_base_dir, self.company_name)
        
        # Components
        self.html_parser = HTMLParser()
        self.crawler = WebCrawler()
        
        # State management
        self.state_no = 0
        self.visited_pages: Dict[str, Page] = {}
        self.failed_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        
        # Global elements (nav, settings, etc.) - aggregated across all pages
        self.global_navigation_elements: List[PageElement] = []
        self.global_settings_elements: List[PageElement] = []
        
        # Analysis statistics
        self.total_load_time = 0.0
        self.total_elements_found = 0
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def start_exploration(self) -> Dict:
        """
        Start the web exploration process.
        
        Returns:
            Dict with exploration results and statistics
        """
        print(f"Starting exploration for {self.company_name}, Output directory: {self.output_dir}")
        
        try:
            # Initialize browser
            self.crawler.start_browser()
            
            # Perform login if credentials provided
            if self.login_credentials and self.start_urls:
                login_success = self.crawler.login(self.login_credentials)
                if not login_success:
                    print("Login failed, proceeding without authentication")
            
            # Process starting URLs
            for url in self.start_urls:
                # Check if it is valid to proceed
                if self.state_no >= self.max_state_no or not self.crawler.is_url_allowed(url, self.allowed_domains, self.exclude_domains):
                    break
                    
                # Navigate to URL
                print(f"*** Exploring URL {self.state_no + 1}/{self.max_state_no}: {url} ***")
                page_result = self.crawler.navigate_to_url(url)
                
                # Process page
                if page_result['success']:
                    file_name = f"{page_result['title']}_{self.state_no}.html"
                    # Take screenshot
                    self.crawler.take_screenshot(f"{self.output_dir}/{file_name}.png")
                    # Clean HTML
                    self.html_parser.clean_html(page_result['html_content'], url, f"{self.output_dir}/{file_name}")
                    print(f"Successfully processed {url}")
                else:
                    print(f"Failed to load {url}: {page_result['error']}")
                
                self.state_no += 1
            
            # Return basic results
            return {
                'company_name': self.company_name,
                'pages_processed': self.state_no,
                'output_dir': self.output_dir
            }
            
        finally:
            # Clean up
            self.crawler.close_browser()
