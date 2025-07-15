import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import signals
import json
import os
from os.path import join as pjoin
from datetime import datetime, timedelta
from urllib.parse import urlparse
import base64
from v1.Crawler.html_parser import HTMLParser
from multiprocessing import Process
import logging
from logging.handlers import RotatingFileHandler

# Configure logging with rotation
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler(
    'Output/logs/crawler.log',
    maxBytes=10*1024*1024,  # 10MB per file
    backupCount=5  # Keep 5 backup files
)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger('crawler')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

def standalone_screenshot(url, output_path):
    """
    Standalone function for capturing screenshots
    Args:
        url (str): URL to capture
        output_path (str): Path to save the screenshot
    """
    from playwright.sync_api import sync_playwright
    
    try:
        with sync_playwright() as p:
            # First try to launch with default settings
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                logger.warning(f"Standard browser launch failed, trying with additional arguments: {e}")
                # Try with additional arguments for Linux environments
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
            
            # Rest of the screenshot logic remains the same
            context = browser.new_context(
                viewport={'width': 1366, 'height': 1536},
                screen={'width': 1366, 'height': 1536}
            )
            page = context.new_page()
            
            page.goto(url, wait_until='networkidle')
            page.screenshot(path=output_path, full_page=False)
            logger.info(f'=== Successfully saved screenshot to {output_path} ===')
            
            context.close()
            browser.close()
            
    except Exception as e:
        logger.error(f'!!! Error capturing screenshot: {e} !!!')


class UTASpider(scrapy.Spider):
    """
    Scrapy spider for crawling websites and saving cleaned HTML content.
    Args:
        start_urls (list): Initial URLs to start crawling from
        company_name (str): Name of the company being crawled
        domain_limit (str): Optional domain restriction for crawling
    """
    name = 'UTASpider'

    def __init__(self, output_dir, start_urls=['https://www.bmw.com/en-au/index.html'], company_name='bmw', 
                 domain_limit:list[str]=None, exclude_domains:list[str]=None, max_total_urls=1000, screenshot=True,
                 resume_crawl=True, *args, **kwargs):
        super(UTASpider, self).__init__(*args, **kwargs)
        self.html_parser = HTMLParser()
        self.last_parse_time = datetime.now()
        self.timeout_threshold = 60

        # Website info
        self.name = company_name
        self.start_urls = start_urls  # Keep this for display purposes
        self.crawl_urls = start_urls.copy()  # New attribute for actual crawling
        self.company_name = company_name 
        self.domain_limit = domain_limit    # List of domains subpaths to crawl
        self.exclude_domains = exclude_domains  # List of domains to exclude

        # Crawling parameters
        self.max_depth = 10
        self.max_urls_per_domain = max_total_urls
        self.max_total_urls = max_total_urls
        self.screenshot = screenshot  # Whether to capture screenshot of the first page

        # Crawling state
        self.crawl_finished = False
        self.crawl_failed = False
        self.all_pages_visited = False
        self.domain_page_num = {}
        self.visited_urls = set()
        self.failed_urls = set()
        self.all_urls = set()

        # Output
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = pjoin(output_dir, self.company_name)
        os.makedirs(self.output_dir, exist_ok=True)

        # Resume crawling if requested
        if resume_crawl:
            self.resume_from_previous_crawl()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        Connects the spider_closed signal to the spider_closed method
        """
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    
    """
    ********************
    *** Main parsing ***
    ********************
    """
    def parse(self, response, depth=0):
        """
        Main parsing function that processes each webpage and extracts links.
        Args:
            response (scrapy.Response): The response object containing the webpage
            depth (int): Current depth level of crawling
        Returns:
            Generator of scrapy.Request objects for found URLs
        """
        self.last_parse_time = datetime.now()
        
        # Check if max total urls reached
        if len(self.visited_urls) >= self.max_total_urls:
            self.terminate()
            return
        # Check if max urls per domain reached
        if depth >= self.max_depth:
            return
        # Skip if not a valid URL
        if not self.is_valid_url(response.url):
            return
        # Check if max urls per domain reached
        domain = urlparse(response.url).netloc
        if domain not in self.domain_page_num:
            self.domain_page_num[domain] = 0
        if self.domain_page_num[domain] >= self.max_urls_per_domain:
            return
        
        # Process and save current page
        try:
            if self.screenshot:
                self.take_screenshot(response.url)
                self.screenshot = False  # Only capture the first page screenshot

            logger.info(f'Processing {response.url} ({len(self.visited_urls) + 1})')
            soup = self.html_parser.clean_html(response.text, response.url, self.all_urls)
            self.visited_urls.add(response.url)
            self.domain_page_num[domain] += 1
            self.save_page_content(response.url, soup)
            self.save_website_info()

            all_page_urls = response.css('a::attr(href)').getall()
            self.all_urls.update(all_page_urls)
            # Extract and follow links
            for link in all_page_urls:
                absolute_url = response.urljoin(link)
                # Scrape the next page if it's valid
                if self.is_valid_url(absolute_url):
                    yield scrapy.Request(
                        absolute_url,
                        callback=self.parse,
                        cb_kwargs={'depth': depth + 1},
                        errback=self.handle_error
                    )
        except Exception as e:
            logger.error(f'!!!Error processing {response.url}: {e} !!!')
            self.failed_urls.add((response.url, str(e)))

    def terminate(self):
        """
        Terminates the crawling process manually.
        """
        self.crawler.engine.slot.inprogress.clear()
        self.crawler.engine.close_spider(self, 'Terminate Process')

    def spider_closed(self, spider, reason=''):
        """
        Handler for spider_closed signal to perform cleanup tasks.
        Args:
            spider (UTASpider): The spider instance that was closed
            reason (str): The reason why the spider was closed
        """
        self.crawl_finished = True
        
        # Check if spider was closed due to timeout
        if reason == 'closespider_timeout':
            self.crawl_failed = True
            logger.error(f'!!! Crawler timed out for {self.company_name} after 60 seconds !!!')
        elif len(self.visited_urls) == 0:
            self.crawl_failed = True
            logger.error(f'!!! Failed for {self.company_name}, reason: {reason} !!!')
        else:
            # Check if all pages are visited by checking if there are any requests in progress
            engine = getattr(self, 'crawler', None).engine
            if engine and hasattr(engine, 'slot'):
                self.all_pages_visited = len(engine.slot.inprogress) == 0
            
            status = "All pages visited" if self.all_pages_visited else "Partially crawled"
            logger.info(f'!!! {status} for {self.company_name} with {len(self.visited_urls)} pages !!!')
            
        self.save_website_info()  # Save final state

    """
    *********************
    *** URL filtering ***
    *********************
    """
    def is_valid_url(self, url):
        """
        Determines if a URL should be crawled based on various criteria.
        Args:
            url (str): URL to evaluate
        Returns:
            bool: True if URL is valid, False otherwise
        """
        # Skip if it's just a page anchor
        if url.startswith('#'):
            return False
            
        # Skip if not a valid URL format
        if not url.startswith(('http://', 'https://')):
            return False
            
        parsed = urlparse(url)
        
        # Skip if already visited
        if url in self.visited_urls:
            return False
            
        # Skip if domain limit is set and URL doesn't match any of the allowed domains
        if self.domain_limit:
            url_matches_domain = False
            for domain_limit in self.domain_limit:
                parsed_domain_limit = urlparse(domain_limit)
                
                # Compare domains and paths
                if parsed.netloc != parsed_domain_limit.netloc:
                    continue
                    
                # If domain limit includes a path, check if URL path starts with domain limit path
                if parsed_domain_limit.path:
                    domain_limit_path = parsed_domain_limit.path.rstrip('/')
                    url_path = parsed.path.rstrip('/')
                    if url_path.startswith(domain_limit_path):
                        url_matches_domain = True
                        break
                else:
                    url_matches_domain = True
                    break
            
            if not url_matches_domain:
                return False

        # Skip if domain is in excluded domains
        if self.exclude_domains:
            for excluded in self.exclude_domains:
                if excluded in url:
                    return False
            
        # Skip if not HTML file (allow only .html and paths without extensions)
        path = parsed.path.lower()
        if '.' in path and not path.endswith('.html'):
            return False
            
        return True

    def handle_error(self, failure):
        """
        Handles failed requests during crawling.
        Args:
            failure (Failure): The failure object containing error details
        """
        failed_url = failure.request.url
        error_message = str(failure.value)
        self.failed_urls.add((failed_url, error_message))
        self.logger.error(f'Request failed: {failed_url}')

    """
    *******************
    *** File saving ***
    *******************
    """
    def filename_from_url(self, url):
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
        # Add query string if it exists, with safe encoding
        if parsed_url.query:
            encoded_query = base64.urlsafe_b64encode(parsed_url.query.encode()).decode()
            path = f'{path}_{encoded_query}'
            
        # Create full directory path and ensure it exists
        full_path = f'{domain_dir}/{path}'.replace('.html', '')
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def save_page_content(self, url, soup):
        """
        Saves cleaned HTML content to a file.
        Args:
            url (str): Source URL of the content
            soup (BeautifulSoup): Cleaned HTML content
        """
        # Get the filename from the URL
        file_path = f'{self.filename_from_url(url)}.html'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        # logger.info(f'Saved cleaned HTML to {file_path}')

    def save_website_info(self):
        """
        Saves website information to a JSON file.
        """
        data = {
            'company_name': self.company_name,
            'start_urls': self.start_urls,
            'domain_limit': self.domain_limit,
            'domain_page_num': self.domain_page_num,
            'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'crawl_finished': self.crawl_finished,
            'crawl_failed': self.crawl_failed,
            'all_pages_visited': self.all_pages_visited,
            'visited_urls': list(self.visited_urls),
            'failed_urls': list(self.failed_urls)
        }
        with open(f'{self.output_dir}/website_info.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        # logger.info(f'Saved website info to {self.output_dir}/website_info.json')

    def take_screenshot(self, url):
        """
        Non-blocking screenshot capture using multiprocessing
        """
        try:
            screenshot_path = f'{self.output_dir}/homepage_screenshot.png'
            # Create and start screenshot process with standalone function
            screenshot_process = Process(
                target=standalone_screenshot,
                args=(url, screenshot_path)
            )
            screenshot_process.start()
            # Don't wait for it to complete - let it run in background
            logger.info(f'=== Screenshot process started for {url} ===')
        except Exception as e:
            logger.error(f'!!! Error starting screenshot process: {e} !!!')

    """
    ********************
    *** Resume crawl ***
    ********************
    """
    def extract_links_from_file(self, file_path):
        """
        Extracts links from either HTML or Markdown file
        Args:
            file_path (str): Path to the file to extract links from
        Returns:
            set: Set of extracted URLs
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            extracted_urls = set()
            
            # Check if file is markdown (based on content structure)
            is_markdown = '<html>' not in content[:100] or file_path.endswith('.md')
            
            if is_markdown:
                # Extract markdown style links [text](url)
                import re
                # Match both [text](url) and bare urls
                markdown_patterns = [
                    r'\[([^\]]+)\]\(([^)]+)\)',  # [text](url)
                    r'<([^>]+)>',  # <url>
                    r'(?<!\[)(?<!\()http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'  # bare urls
                ]
                
                for pattern in markdown_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        if '](/' in match.group():  # relative url in markdown
                            url = match.group(2)
                        elif match.group().startswith('http'):  # absolute url
                            url = match.group()
                        else:  # relative url in angle brackets
                            url = match.group(1)
                        
                        if url.startswith('/'):  # Convert relative to absolute
                            domain = urlparse(self.start_urls[0]).netloc
                            url = f'https://{domain}{url}'
                            
                        extracted_urls.add(url)
            else:
                # Use BeautifulSoup for HTML files
                soup = self.html_parser.BeautifulSoup(content, 'html.parser')
                for link in soup.find_all('a', href=True):
                    url = link['href']
                    if url.startswith('/'):  # Convert relative to absolute
                        domain = urlparse(self.start_urls[0]).netloc
                        url = f'https://{domain}{url}'
                    extracted_urls.add(url)
                    
            return extracted_urls
            
        except Exception as e:
            logger.error(f'Error extracting links from {file_path}: {e}')
            return set()

    def resume_from_previous_crawl(self):
        """
        Loads the previous crawl state and prepares for resuming the crawl.
        Returns:
            bool: True if successfully loaded previous state, False otherwise
        """
        try:
            info_path = f'{self.output_dir}/website_info.json'
            if not os.path.exists(info_path):
                logger.warning(f"*** No previous crawl state found at {info_path}, start crawling from scratch ***")
                return False

            with open(info_path, 'r') as f:
                website_info = json.load(f)

            # Restore crawling state
            self.domain_page_num = website_info.get('domain_page_num', {})
            self.visited_urls = set(website_info.get('visited_urls', []))
            self.failed_urls = set(tuple(x) for x in website_info.get('failed_urls', []))
            
            # Update crawl_urls to include unvisited URLs from the domain
            unvisited_urls = set()
            found_unvisited = False
            
            for domain, urls in self.domain_page_num.items():
                if found_unvisited:
                    break
                domain_path = f'{self.output_dir}/{domain}'
                if os.path.exists(domain_path):
                    # Scan the domain directory for all HTML and MD files
                    for root, _, files in os.walk(domain_path):
                        if found_unvisited:
                            break
                        for file in files:
                            if file.endswith(('.html', '.md')):
                                file_path = os.path.join(root, file)
                                extracted_urls = self.extract_links_from_file(file_path)
                                # Add valid unvisited URLs
                                for url in extracted_urls:
                                    if self.is_valid_url(url) and url not in self.visited_urls:
                                        unvisited_urls.add(url)
                                        found_unvisited = True
                                # Break if we found any unvisited URLs
                                if found_unvisited:
                                    break

            # Check if all pages are visited
            self.crawl_urls = list(unvisited_urls)
            if not self.crawl_urls:
                self.all_pages_visited = True
                logger.info("!!! All pages visited, no unvisited URLs found to resume crawling !!!")
                return False

            # Reset crawl state
            self.crawl_finished = False
            self.crawl_failed = False
            self.all_pages_visited = False
            self.save_website_info()
            logger.info(f"*** Found {len(self.crawl_urls)} unvisited URLs to resume crawling with {len(self.visited_urls)} visited URLs ***")
            return True

        except Exception as e:
            logger.error(f"Error loading previous crawl state: {e}")
            return False

    """
    *********************
    *** Timeout check ***
    *********************
    """
    def check_timeout(self):
        """Check if crawler is stuck by monitoring parse activity"""
        if datetime.now() - self.last_parse_time > timedelta(seconds=self.timeout_threshold):
            logger.error(f'!!! Crawler timed out for {self.company_name} - no parsing activity for {self.timeout_threshold} seconds !!!')
            self.crawl_failed = True
            self.terminate()
        
    def start_requests(self):
        """Override start_requests to add periodic timeout checking"""
        from twisted.internet import reactor
        reactor.callLater(5, self.periodic_timeout_check)
        for url in self.crawl_urls:
            yield scrapy.Request(url, callback=self.parse)
        
    def periodic_timeout_check(self):
        """Periodically check for timeout"""
        self.check_timeout()
        from twisted.internet import reactor
        if not self.crawl_finished:  # Only schedule next check if crawler is still running
            reactor.callLater(5, self.periodic_timeout_check)


if __name__ == "__main__":
    # web_urls = 'https://www.tum.de/en/'
    # company_name = 'tum'
    # domain_limit = 'https://www.tum.de/en/' # None or specific domain, such as 'www.bmw.com/en-au'

    web_urls = 'https://www.unitree.com/'
    company_name = 'unitree'
    domain_limit = ['https://www.unitree.com/', 'https://www.unitree.com/products/']  # Now accepts a list of domains

    # Configure and start the crawler
    process = CrawlerProcess({
        'LOG_ENABLED': True,
        'LOG_LEVEL': 'ERROR',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1,
        'DOWNLOAD_TIMEOUT': 10,
        'CLOSESPIDER_TIMEOUT': 60  # Close spider after 60 seconds
    })
    process.crawl(UTASpider, start_urls=[web_urls], company_name=company_name, domain_limit=domain_limit, resume_crawl=True)
    process.start()
