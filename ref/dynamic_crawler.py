import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
from urllib.parse import urlparse, urljoin
from datetime import datetime
from Deeptech.v1.Crawler.html_parser import HTMLParser
from bs4 import BeautifulSoup
import base64
import json

from Deeptech.v2.Crawler.UTG.page import Page


class DynamicWebCrawler:
    def __init__(self, company_name, start_urls, allowed_domains, exclude_domains=None, login_credentials=None, max_state_no=100, output_dir="Output/dynamic_crawlling"):
        """
        Initialize the crawler with a starting URL and allowed paths
        
        Args:
            company_name (str): The name of the company to crawl
            start_urls (list): List of starting URLs with authentication token
            allowed_domains (list): List of allowed domains to crawl
            exclude_domains (list): List of excluded domains to crawl
            login_credentials (dict): Dictionary containing login credentials with keys 'username' and 'password'
            output_dir (str): Base directory for storing crawled data
        """
        self.company_name = company_name
        self.start_urls = start_urls
        self.allowed_domains = allowed_domains
        self.exclude_domains = exclude_domains
        self.output_dir = os.path.join(output_dir, self.company_name)
        self.state_no = 0
        self.max_state_no = max_state_no

        # Track visited URLs
        self.visited_urls = set()
        self.failed_urls = set()
        # Login credentials
        self.login_credentials = login_credentials or None  # {'username': 'username', 'password': 'password'}

        # Initialize browser
        self.driver = self.initialize_browser()
        # Initialize HTML parser
        self.html_parser = HTMLParser()
        
    def initialize_browser(self):
        """
        Initialize and return a new browser instance
        """
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        return driver
    
    '''
    *************
    *** Login ***
    *************
    '''
    def login(self, max_retries=3):
        """
        Attempt to login using provided credentials with retries
        
        Args:
            max_retries (int): Maximum number of login attempts
            
        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.login_credentials:
            print("No login credentials provided")
            return False
            
        for attempt in range(max_retries):
            try:
                username_selector = "input[formcontrolname='username']"
                password_selector = "input[formcontrolname='password']"
                login_button_selector = ".login-button"
                print(f"Login attempt {attempt + 1} of {max_retries}")
                
                # Wait for login form elements
                wait = WebDriverWait(self.driver, 10)
                # Find and fill username field
                username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, username_selector)))
                username_input.clear()
                username_input.send_keys(self.login_credentials.get('username'))
                
                # Find and fill password field
                password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, password_selector)))
                password_input.clear()
                password_input.send_keys(self.login_credentials.get('password'))
                
                # Find and click login button
                login_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, login_button_selector)))
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector)))
                
                # Try different methods to click the button
                try:
                    login_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", login_button)
                
                # Wait for login to complete
                time.sleep(3)
                
                # Verify login success
                if "state-login" not in self.driver.page_source or any(marker in self.driver.current_url for marker in ['/app/', '/dashboard']):
                    print("Login successful")
                    return True
                
                print(f"Login verification failed on attempt {attempt + 1}")
                
            except Exception as e:
                print(f"Login attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))  # Exponential backoff
                    continue
                
            # Clear cookies and refresh before retrying
            self.driver.delete_all_cookies()
            self.driver.refresh()
            time.sleep(2)
        
        print("All login attempts failed")
        return False

    '''
    ****************
    *** Crawling ***
    ****************
    '''
    def crawl(self):
        """
        Crawl the website, overriden by child classes
        """
        pass

    def parse_page(self, url, html_content):
        """
        Parse the page content

        Args:
            url (str): The URL of the current page
            html_content (str): The HTML content of the current page
            
        Returns:
            str: The parsed HTML content
        """
        html_content = self.html_parser.clean_html(html_content, url, markdown=False)
        return html_content

    def _is_allowed_url(self, url):
        """
        Check if the URL matches any of the allowed domains
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if the URL is allowed, False otherwise
        """
        if len(self.allowed_domains) == 0:
            return True
        
        # Check if the URL starts with any of the excluded domains
        if self.exclude_domains:
            for domain in self.exclude_domains:
                if url.startswith(domain):
                    return False
        
        # Check if the URL starts with any of the allowed domains
        for domain in self.allowed_domains:
            if url.startswith(domain):
                return True
        return False

    def _extract_links(self):
        """
        Extract all links from the current page that belong to allowed paths
        
        Returns:
            set: A set of all links that belong to allowed paths
        """
        def normalize_url(domain, scheme, url):
            """ 
            Normalize the URL to add domain and remove anchor part

            Args:
                domain (str): The domain of the current page
                scheme (str): The scheme of the current page
                url (str): The URL to normalize

            Returns:
                str: The normalized URL
            """
            if not url:
                return None
            #  Add domain to the URL if it is relative
            if not url.startswith('http'):
                url = urljoin(scheme + '://' + domain, url)
            # Remove anchor part from URL
            url_split = url.split('#')
            # Avoid case where there is a / in the anchor part https://portal.azure.com/#browse/Microsoft.Web%2Fsites/kind/functionapp
            if len(url_split) > 1 and '/' not in url_split[1]:
                return url_split[0]
            else:
                return url

        links = set()
        try:
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            domain = urlparse(self.driver.current_url).netloc
            scheme = urlparse(self.driver.current_url).scheme
            for element in elements:
                try:
                    href = normalize_url(domain, scheme, element.get_attribute("href"))
                    if href and self._is_allowed_url(href):
                        links.add(href)
                except StaleElementReferenceException:
                    continue
        except Exception as e:
            print(f"Error extracting links: {str(e)}")
        return links

    '''
    **************
    *** Saving ***
    **************
    '''
    def save_page(self, url, html_content):
        """
        Save the page content and screenshot with organized structure
        
        Args:
            url (str): The URL of the current page
            html_content (str): The HTML content of the current page
        """
        try:
            # Save HTML content
            title = html_content.find('title').text.strip()
            # Sanitize the title to make it safe for filesystem
            safe_title = self._sanitize_filename(title)
            file_base_dir = self._filename_from_url(url)
            html_file = os.path.join(file_base_dir, f"{self.state_no}_{safe_title}.html")
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(str(html_content))
            print(f"Saved HTML to: {html_file}")
            
            # Save screenshot
            screenshot_file = os.path.join(file_base_dir, f"{self.state_no}_{safe_title}.png")
            self.driver.save_screenshot(screenshot_file)
            print(f"Saved screenshot to: {screenshot_file}")

            self.state_no += 1
        except Exception as e:
            print(f"Error saving page {url}: {str(e)}")

    def save_website_info(self):
        """
        Saves website information to a JSON file.
        """
        data = {
            'company_name': self.company_name,
            'start_urls': self.start_urls,
            'allowed_domains': self.allowed_domains,
            'login_credentials': self.login_credentials,
            'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'output_dir': self.output_dir,
            'state_no': self.state_no,
            'visited_urls': list(self.visited_urls),
            'failed_urls': list(self.failed_urls)
        }
        with open(os.path.join(self.output_dir, "website_info.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _filename_from_url(self, url):
        """
        Generates a filesystem-safe filename from a URL.
        Args:
            url (str): URL to convert to filename
        Returns:
            str: Path where the file should be saved
        """
        # Parse URL and create domain directory
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        domain_dir = f'{self.output_dir}/{domain}'
        
        # Create path for file
        path = parsed_url.path
        if not path or path == '/':
            path = 'root-index'
        else:
            path = path.strip('/')
            # Remove .html or .htm extension if present
            if path.endswith('.html'):
                path = path[:-5]  # remove .html
            elif path.endswith('.htm'):
                path = path[:-4]  # remove .htm
        # Add query string if it exists, with safe encoding
        if parsed_url.query:
            encoded_query = base64.urlsafe_b64encode(parsed_url.query.encode()).decode()
            path = f'{path}_{encoded_query}'
            
        # Create full directory path and ensure it exists
        full_dir = f'{domain_dir}/{path}'
        os.makedirs(full_dir, exist_ok=True)
        return full_dir
    
    def _sanitize_filename(self, filename):
        """
        Sanitize a filename to make it safe for filesystem use.
        Replaces problematic characters with underscores.
        
        Args:
            filename (str): The filename to sanitize
            
        Returns:
            str: Sanitized filename safe for filesystem use
        """
        # Replace problematic characters with underscore
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

