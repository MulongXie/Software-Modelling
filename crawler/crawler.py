from playwright.sync_api import sync_playwright, Browser, Page as PlaywrightPage
from typing import Optional, Dict, List
import time
from urllib.parse import urlparse


class WebCrawler:
    """
    Playwright-based web crawler helper class.
    Handles browser automation and page navigation.
    Does NOT store data - just returns content to WebExplorer.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Args:
            headless: Whether to run browser in headless mode
            timeout: Page load timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[PlaywrightPage] = None
    
    '''
    ***************
    *** Browser ***
    ***************
    '''
    def start_browser(self):
        """
        Initialize Playwright browser.
        """
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            self.page = self.browser.new_page()
            
            # Set timeout and viewport
            self.page.set_default_timeout(self.timeout * 1000)
            self.page.set_viewport_size({"width": 1366, "height": 1536})
    
    def close_browser(self):
        """
        Clean up browser resources.
        """
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
        self.page = None
        self.browser = None
        self.playwright = None

    def take_screenshot(self, path: str) -> bool:
        """
        Take a screenshot of the current page.
        
        Args:
            path: File path to save screenshot
            
        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            return False
        
        try:
            self.page.screenshot(path=path, full_page=False)
            print(f"Screenshot saved: {path}")
            return True
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return False
    
    '''
    ****************
    *** Crawling ***
    ****************
    '''
    def login(self, login_credentials: Dict[str, str], login_selectors: Dict[str, str] = None) -> bool:
        """
        Perform login using provided credentials.
        
        Args:
            login_credentials: Dict with 'username' and 'password'
            login_selectors: Dict with custom selectors for login form
            
        Returns:
            True if login successful, False otherwise
        """
        if not self.page or not login_credentials:
            return False
        
        # Default selectors
        default_selectors = {
            'username': "input[name='username'], input[name='email'], input[type='email'], input[formcontrolname='username']",
            'password': "input[name='password'], input[type='password'], input[formcontrolname='password']",
            'submit': "button[type='submit'], input[type='submit'], .login-button, .btn-login"
        }
        
        selectors = login_selectors or default_selectors
        
        try:
            print("Attempting login...")
            
            # Fill username
            username_field = self.page.locator(selectors['username']).first
            username_field.fill(login_credentials['username'])
            
            # Fill password  
            password_field = self.page.locator(selectors['password']).first
            password_field.fill(login_credentials['password'])
            
            # Click submit
            submit_button = self.page.locator(selectors['submit']).first
            submit_button.click()
            
            # Wait for navigation or page change
            self.page.wait_for_load_state('networkidle')
            
            # Simple login verification - check if we're no longer on login page
            current_url = self.page.url
            if 'login' not in current_url.lower():
                print("Login successful")
                return True
            else:
                print("Login verification failed")
                return False
                
        except Exception as e:
            print(f"Login failed: {e}")
            return False
        
    def navigate_to_url(self, url: str) -> Dict:
        """
        Navigate to a URL and return page content.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Dict with page content and metadata
        """
        if not self.page:
            self.start_browser()
        
        try:
            print(f"Navigating to: {url}")
            
            # Navigate to the URL
            response = self.page.goto(url, wait_until='networkidle')
            
            # Wait for page to be ready
            self.page.wait_for_load_state('networkidle')
            
            return {
                'url': self.page.url,
                'html_content': self.page.content(),
                'title': self.page.title(),
                'load_time': self._measure_load_time(),
                'status_code': response.status if response else None,
                'success': True,
                'error': None
            }
            
        except Exception as e:
            print(f"Failed to navigate to {url}: {e}")
            return {
                'url': url,
                'html_content': None,
                'title': None,
                'load_time': None,
                'status_code': None,
                'success': False,
                'error': str(e)
            }
    
    def _measure_load_time(self) -> float:
        """
        Measure page load time using Performance API.
        
        Returns:
            Load time in seconds
        """
        try:
            # Get navigation timing from browser
            load_time = self.page.evaluate("""
                () => {
                    const timing = performance.getEntriesByType('navigation')[0];
                    return timing ? (timing.loadEventEnd - timing.navigationStart) / 1000 : 0;
                }
            """)
            return load_time
        except:
            return 0.0
    
    '''
    ************************
    *** Helper Functions ***
    ************************
    '''  
    def extract_links(self) -> List[str]:
        """
        Extract all links from the current page.
        
        Returns:
            List of URLs found on the page
        """
        if not self.page:
            return []
        
        try:
            # Get all links
            links = self.page.locator('a[href]').all()
            urls = []
            
            for link in links:
                href = link.get_attribute('href')
                if href and not href.startswith('#'):
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        base_url = f"{urlparse(self.page.url).scheme}://{urlparse(self.page.url).netloc}"
                        href = base_url + href
                    elif not href.startswith('http'):
                        href = self.page.url.rstrip('/') + '/' + href.lstrip('/')
                    urls.append(href)
            
            return list(set(urls))  # Remove duplicates
            
        except Exception as e:
            print(f"Failed to extract links: {e}")
            return []

    def is_url_allowed(self, url: str, allowed_domains: List[str], exclude_domains: List[str] = None) -> bool:
        """
        Check if URL is allowed for crawling.
        
        Args:
            url: URL to check
            allowed_domains: List of allowed domains
            exclude_domains: List of excluded domains
            
        Returns:
            True if URL is allowed, False otherwise
        """
        if not allowed_domains:
            return True
        
        # Check exclusions first
        if exclude_domains:
            for excluded in exclude_domains:
                if excluded in url:
                    return False
        
        # Check if URL matches any allowed domain
        for domain in allowed_domains:
            if url.startswith(domain):
                return True
        
        return False
    