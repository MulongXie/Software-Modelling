# WebExplorer - Advanced Web Software Analysis

A sophisticated web crawler and analyzer that addresses key limitations of traditional web crawlers by implementing **intelligent element prioritization** and preparing for **dynamic content handling**.

## 🎯 Key Features

### 1. **Smart Element Prioritization**
- **Navigation elements** (nav buttons, menus) get highest priority
- **Action elements** (buttons, forms) get medium-high priority  
- **Content elements** get lower priority
- **Semantic analysis** based on HTML structure, CSS classes, and text content

### 2. **Comprehensive Page Analysis**
- Clean HTML parsing with noise reduction
- Element classification (navigation, buttons, links, content, etc.)
- Link discovery and extraction
- Page caching and state management

### 3. **Extensible Architecture**
- Modular design for easy extension
- Clear separation of concerns
- Ready for dynamic content handling integration

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage
```python
from src import WebExplorer

# Create explorer instance
explorer = WebExplorer(max_pages=5, delay=1.0)

# Analyze a website
page = explorer.analyze_url("https://example.com")

# Get prioritized elements
prioritized_elements = explorer.get_prioritized_elements(page.url)

# Show top navigation elements
nav_elements = explorer.get_prioritized_elements(page.url, "navigation")
```

### Run the Example
```bash
# Test with default URL
python example_usage.py

# Test with custom URL
python example_usage.py https://quotes.toscrape.com/

# Run basic tests
python test_basic.py
```

## 📁 Project Structure

```
├── src/
│   ├── __init__.py           # Package initialization
│   ├── page.py               # Page and PageElement classes
│   ├── html_parser.py        # HTML cleaning and parsing
│   ├── element_prioritizer.py # Element prioritization logic
│   └── web_explorer.py       # Main orchestrator class
├── ref/                      # Reference implementations
├── test_basic.py            # Basic functionality tests
├── example_usage.py         # Usage examples
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## 🧩 Core Components

### 1. **WebExplorer** (Main Orchestrator)
- Manages the entire analysis process
- Handles HTTP requests and session management
- Coordinates all other components

### 2. **Page** (Content Storage)
- Stores page content and metadata
- Caches extracted elements and links
- Provides filtering and querying methods

### 3. **HTMLParser** (Content Processing)
- Cleans HTML by removing noise (scripts, styles, etc.)
- Extracts and classifies elements
- Discovers links and relationships

### 4. **ElementPrioritizer** (Intelligence Layer)
- Calculates semantic importance scores
- Considers element type, position, attributes, and text content
- Provides explainable prioritization

## 🎯 Element Prioritization Logic

The prioritizer uses multiple factors to score elements:

### Base Scores by Type
- **Navigation**: 0.9 (highest priority)
- **Buttons**: 0.8
- **Forms**: 0.75
- **Links**: 0.7
- **Headers**: 0.6
- **Content**: 0.4
- **Media**: 0.5

### Boost Factors
- **Important keywords**: login, signup, menu, settings, etc.
- **CSS classes**: navbar, btn-primary, main-nav, etc.
- **HTML attributes**: role="navigation", aria-label, etc.
- **Element position**: header tags, main content areas
- **Text characteristics**: length, formatting, action words

## 🔧 Example Output

```
🔍 Analyzing website: https://example.com
============================================================

📄 Page Information:
   Title: Example Domain
   URL: https://example.com
   Domain: example.com
   Elements found: 23
   Links found: 1

⭐ Top 10 Priority Elements:
   1. h1 (header) - Score: 0.780
      Text: 'Example Domain'
      
   2. a (link) - Score: 0.850
      Text: 'More information...'
      Classes: 'info-link'
      
   3. p (content) - Score: 0.400
      Text: 'This domain is for use in illustrative examples...'
```

## 🛠️ Next Steps

This foundation is ready for extension with:

1. **Dynamic Content Handling**: Integration with Selenium/Playwright for SPAs
2. **Priority Queue Implementation**: For intelligent crawling order
3. **Knowledge Graph Integration**: For Q&A and automation applications
4. **Advanced ML Models**: For even better element classification

## 📊 Technical Approach

### Problem 1: Element Prioritization ✅
- **Solution**: Semantic scoring based on multiple factors
- **Status**: Implemented and working
- **Benefits**: Focuses on important elements first

### Problem 2: Dynamic Content (Future)
- **Solution**: Browser automation integration
- **Status**: Architecture ready for integration
- **Benefits**: Handle modern SPAs and dynamic updates

## 🤝 Contributing

The modular architecture makes it easy to extend:

1. **Add new element types** in `HTMLParser._classify_element()`
2. **Improve prioritization** in `ElementPrioritizer.calculate_priority()`
3. **Add dynamic handling** by extending `WebExplorer`

## 📄 License

This project is part of the PortalX ecosystem for advanced web interface analysis. 