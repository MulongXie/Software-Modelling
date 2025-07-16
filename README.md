# WebExplorer - Advanced Web Software Analysis

A sophisticated web exploration system that addresses key limitations of traditional web crawlers by implementing **intelligent element prioritization** and **dynamic content handling** with Playwright.

## 🎯 Key Features

### 1. **Smart Element Prioritization** ✅
- **Navigation elements** (nav buttons, menus) get highest priority
- **Action elements** (buttons, forms) get medium-high priority  
- **Content elements** get lower priority
- **Semantic analysis** based on HTML structure, CSS classes, and text content
- **Global element tracking** across all pages

### 2. **Dynamic Content Handling** ✅  
- **Playwright integration** for modern SPAs and dynamic sites
- **Smart waiting** for network idle and content loading
- **JavaScript execution** support for React/Vue/Angular apps
- **Login support** with customizable selectors

### 3. **Comprehensive Analysis**
- Clean HTML parsing with noise reduction
- Element classification and prioritization
- Link discovery and exploration
- Performance metrics and load time tracking
- Screenshot capture for visual analysis

### 4. **Extensible Architecture**
- **WebExplorer**: Main orchestrator managing global state
- **WebCrawler**: Playwright-based browser automation
- **HTMLParser**: Content processing and element extraction
- **ElementPrioritizer**: Semantic importance scoring

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
playwright install  # Install browser binaries
```

### Basic Usage
```python
from web_explorer import WebExplorer

# Create explorer instance
explorer = WebExplorer(
    company_name="my_company",
    start_urls=["https://example.com"],
    allowed_domains=["https://example.com"],
    max_state_no=5,
    headless=True
)

# Start exploration
results = explorer.start_exploration()

# Access global elements
nav_elements = explorer.get_global_navigation_elements()
action_elements = explorer.get_global_action_elements()
```

### With Authentication
```python
explorer = WebExplorer(
    company_name="secure_site",
    start_urls=["https://app.example.com/login"],
    allowed_domains=["https://app.example.com"],
    login_credentials={
        'username': 'your_username',
        'password': 'your_password'
    },
    headless=False  # Show browser for debugging
)

results = explorer.start_exploration()
```

### Run Examples
```bash
# Run integrated system demo
python example_integrated.py

# Install Playwright browsers first
playwright install
```

## 📁 New Project Structure

```
├── web_explorer.py          # Main orchestrator class
├── crawler/
│   └── crawler.py           # Playwright-based web crawler
├── parser/
│   ├── page.py              # Page and PageElement classes
│   ├── html_parser.py       # HTML cleaning and parsing
│   └── element_prioritizer.py # Element prioritization logic
├── ref/                     # Reference implementations
├── example_integrated.py    # Integrated system examples
├── requirements.txt         # Dependencies (includes Playwright)
└── README.md               # This file
```

## 🧩 Architecture Overview

```
WebExplorer (Orchestrator)
├── WebCrawler (Playwright-based)
│   ├── Browser automation
│   ├── Dynamic content handling
│   ├── Login support
│   └── Link extraction
├── HTMLParser (Content Processing)
│   ├── HTML cleaning
│   ├── Element extraction
│   └── Link discovery
├── ElementPrioritizer (Intelligence)
│   ├── Semantic scoring
│   ├── Type classification
│   └── Priority ranking
└── Page Objects (Storage)
    ├── Individual page data
    ├── Element collections
    └── Metadata
```

## 🎯 Problem-Solution Mapping

### ✅ Problem 1: Element Prioritization 
**Traditional Issue**: All elements treated equally
**Our Solution**: 
- Semantic scoring based on multiple factors
- Global element tracking across pages  
- Explainable prioritization with detailed scoring

### ✅ Problem 2: Dynamic Content Handling
**Traditional Issue**: URL-based crawling misses dynamic content
**Our Solution**:
- Playwright integration for JavaScript execution
- Smart waiting for network idle and content loading
- State change detection without URL changes

## 🔧 Example Output

```
🚀 Starting exploration for my_company
📁 Output directory: Output/dynamic_crawling/my_company

🔍 Exploring URL 1/5: https://example.com
✅ Successfully analyzed https://example.com
   📊 Elements found: 45
   🔗 Links discovered: 12
   ⏱️ Load time: 1.23s

📈 Analyzing global patterns across 3 pages...
   🧭 Global navigation elements: 8
   ⚙️ Global settings elements: 3
   🎯 Global action elements: 15

📋 Exploration Complete!
   📄 Pages explored: 3
   🎯 Total elements: 127
   🧭 Navigation elements: 8
   ⚙️ Settings elements: 3
   🎯 Action elements: 15
```

## 📊 Key Advantages Over Traditional Crawlers

| Feature | Traditional Crawlers | WebExplorer |
|---------|---------------------|-------------|
| **Element Priority** | ❌ All equal | ✅ Semantic scoring |
| **Dynamic Content** | ❌ URLs only | ✅ JavaScript execution |
| **Modern SPAs** | ❌ Limited support | ✅ Full support |
| **Global Analysis** | ❌ Page-by-page | ✅ Cross-page patterns |
| **Login Support** | ❌ Manual setup | ✅ Built-in automation |
| **Performance** | ❌ Slow (Selenium) | ✅ Fast (Playwright) |

## 🛠️ Advanced Usage

### Custom Element Prioritization
```python
# Access detailed priority explanations
prioritizer = ElementPrioritizer()
explanation = prioritizer.get_priority_explanation(element)
print(f"Score: {explanation['total_score']}")
print(f"Reasoning: {explanation['reasoning']}")
```

### Global Element Analysis
```python
# Get elements that appear across multiple pages
nav_elements = explorer.get_global_navigation_elements()
for elem in nav_elements:
    print(f"Navigation: {elem.text} (Score: {elem.priority_score})")
```

### Custom Crawling Logic
```python
# Access the underlying crawler for custom operations
crawler = explorer.crawler
result = crawler.navigate_to_url("https://custom-page.com")
links = crawler.extract_links()
crawler.take_screenshot("custom_screenshot.png")
```

## 🚀 Next Steps & Roadmap

This foundation enables powerful extensions:

1. **Priority Queue Crawling**: Use prioritization for intelligent crawling order
2. **Knowledge Graph Integration**: Export structured data for Q&A systems
3. **ML-Enhanced Classification**: Train models on discovered patterns  
4. **Real-time Monitoring**: Detect site changes and updates
5. **PortalX Integration**: Power advanced interface analysis

## 🤝 Contributing

The modular architecture makes extension straightforward:

1. **Enhance Prioritization**: Modify `ElementPrioritizer.calculate_priority()`
2. **Add Crawler Features**: Extend `WebCrawler` class methods
3. **Custom Analysis**: Create new analysis methods in `WebExplorer`
4. **New Element Types**: Update `HTMLParser._classify_element()`

## 📄 License

This project is part of the PortalX ecosystem for advanced web interface analysis. 