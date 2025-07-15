from bs4 import BeautifulSoup, Comment
import re
import os
from dataclasses import dataclass
from Deeptech.v1.Crawler.markdown_parser import MarkdownParser
import json

@dataclass
class ParsedContent:
    """Data class to hold both HTML and markdown versions of parsed content"""
    html_soup: BeautifulSoup
    markdown: str

class HTMLParser:
    def __init__(self):
        self.markdown_parser = MarkdownParser()

    """
    *********************
    *** HTML cleaning ***
    *********************
    """
    def clean_html(self, html_content, url, existing_urls=None, markdown=True, save_id=True, special_rules_path=None):
        """
        Cleans and simplifies HTML content by removing unnecessary elements and attributes,
        then converts it to markdown format while preserving the BeautifulSoup structure.
        Args:
            html_content (str): The HTML content to clean
            url (str): The URL of the webpage
            existing_urls (set): Set of all URLs that have been discovered
            markdown (bool): Whether to convert the HTML to markdown
            save_id (bool): Whether to save the id attributes
            special_rules_path (str): The path to the special rules file
        Returns:
            BeautifulSoup: Soup object containing markdown content
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Clean elements with special rules if provided
        if special_rules_path:
            self.clean_elements_with_special_rules(soup, url, special_rules_path)

        # Clean head
        self.clean_head(soup)
        # Clean elements
        self.clean_elements(soup, save_id=save_id)

        # Remove existing link elements
        self.remove_existing_link_elements(soup, existing_urls)
        # Remove empty elements
        self.remove_empty_elements(soup)
        # Remove redundant divs
        # self.remove_redundant_divs(soup)

        # # Add title
        self.add_title(soup, url)
        
        # Remove excessive whitespace while preserving basic structure
        cleaned_html = soup.prettify(formatter='html5')
        cleaned_html = '\n'.join(line.strip() for line in cleaned_html.splitlines())
        cleaned_soup = BeautifulSoup(cleaned_html, 'html.parser')
        
        if markdown:
            # Convert to markdown
            markdown_content = self.markdown_parser.html_to_markdown(cleaned_soup)
            # Create a new soup with markdown content wrapped in pre tags to preserve formatting
            cleaned_soup = BeautifulSoup(markdown_content, 'html.parser')
        
        return cleaned_soup

    def clean_head(self, soup):
        """
        Cleans and simplifies HTML content by removing unnecessary elements and attributes.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
        Returns:
            None (modifies soup object in place)
        """
        # Clean head section
        head = soup.find('head')
        if head:
            # Remove all elements from head except title
            for tag in head.find_all():
                if tag.name != 'title':
                    tag.decompose()

    def clean_elements(self, soup, save_id=False):
        """
        Cleans and simplifies HTML content by removing unnecessary elements and attributes.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
        Returns:
            None (modifies soup object in place)
        """
        # Remove script, style, and source tags
        for tag in soup.find_all(['script', 'style', 'source', 'path']):
            tag.decompose()

        # Remove elements with role="tooltip"
        for tag in soup.find_all(attrs={'role': 'tooltip'}):
            tag.decompose()

        # Remove unused attributes
        allowed_attrs = ['href', 'src', 'type']
        if save_id:
            allowed_attrs += ['id', 'class', 'role', 'name', 'title', 'aria-expanded', 'aria-label', 'data-icon']
        
        for tag in soup.find_all():
            # Special handling for <i> tags
            if tag.name == 'i':
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in allowed_attrs + ['class', 'data-icon']:
                        del tag[attr]
            # Special handling for <img> tags - remove src attribute
            elif tag.name == 'img' or tag.name == 'svg':
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in allowed_attrs or attr == 'src':
                        del tag[attr]
            else:
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in allowed_attrs:
                        del tag[attr]

        # Remove all HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

    def clean_elements_with_special_rules(self, soup, url, special_rules_path):
        """
        Cleans and simplifies HTML content by removing unnecessary elements and attributes.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
            special_rules_path (str): The path to the special rules file 
            "page_cleaning": {
                "exclude":[
                    {
                        "page_url": "https://portal.azure.com/#home",
                        "remove_elements": [
                            ".fxs-home-target"
                        ]
                    }
                ]
            }
        """
        if not os.path.exists(special_rules_path):
            return
        # Read the special rules file
        with open(special_rules_path, 'r', encoding='utf-8') as f:
            special_rules = json.load(f)['page_cleaning']

        # Clean elements with special rules
        exclude_elements = special_rules.get('exclude', [])
        for exclude_element in exclude_elements:
            if exclude_element['page_url'] != url:
                for element in exclude_element['remove_elements']:
                    for tag in soup.select(element):
                        tag.decompose()

    def remove_existing_link_elements(self, soup, existing_urls):
        """
        Removes <a> tags that point to discovered URLs.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
            existing_urls (set): Set of all URLs that have been discovered
        Returns:
            None (modifies soup object in place)
        """
        # Remove <a> tags that point to discovered URLs
        if existing_urls and len(existing_urls) > 0:
            for a_tag in soup.find_all('a'):
                href = a_tag.get('href')
                if href and href in existing_urls:
                    a_tag.decompose()

    def remove_empty_elements(self, soup):
        """
        Removes empty elements from HTML.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
        Returns:
            None (modifies soup object in place)
        """
        # Tags that should be kept even when empty
        preserve_tags = {'hr', 'br', 'img', 'video', 'input', 'meta', 'link', 'textarea'}
        
        # Recursively remove empty elements
        while True:
            removed = False
            for element in soup.find_all():
                # Skip if element should be preserved
                if element.name in preserve_tags:
                    continue
                # Skip if element has attributes
                if element.attrs:
                    continue
                # Get content (excluding whitespace)
                content = ''.join(str(child) for child in element.contents).strip()
                # Remove if empty (no content and no attributes)
                if not content:
                    element.decompose()
                    removed = True
                    break
            if not removed:
                break

    def remove_redundant_divs(self, soup):
        """
        Removes unnecessary nested div elements from HTML.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
        Returns:
            None (modifies soup object in place)
        """
        while True:
            redundant_found = False
            for div in soup.find_all('div'):
                # Get all children, excluding empty whitespace
                children = list(div.children)
                children = [c for c in children if not isinstance(c, str) or c.strip()]
                # Remove div if it's empty or has only one child
                if len(children) == 0:
                    div.decompose()
                    redundant_found = True
                    break
                elif len(children) == 1:
                    div.replace_with(children[0])
                    redundant_found = True
                    break
            if not redundant_found:
                break

    def add_title(self, soup, page_url):
        """
        Adds a title to the HTML.
        """
        # Add source URL and title stamp at the beginning of body
        body = soup.find('body')
        if body:
            title_text = soup.find('title').string if soup.find('title') else "No title"
            stamp_html = f'''
            <div class="cleaned-html-title">
                <h1 class="source">{page_url}</h1>
                <h1 class="title">{title_text}</h1>
                <hr>
            </div>
            '''
            body.insert(0, BeautifulSoup(stamp_html, 'html.parser'))

if __name__ == "__main__":
    # Path to the account.html file
    html_file_path = os.path.join("Deeptech/v1/Crawler/Data", "azure.html")
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Process the HTML
    parser = HTMLParser()
    cleaned_soup = parser.clean_html(html_content=html_content, url="https://portal.azure.com/#home", markdown=False, save_id=True)
    # Save the cleaned HTML to a new file
    output_path = os.path.join("Deeptech/v1/Crawler/Data", "azure_clean.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(cleaned_soup))
    print(f"Successfully processed HTML. Cleaned version saved to: {output_path}")

