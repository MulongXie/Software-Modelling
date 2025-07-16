from typing import Dict, List, Set
from .page import PageElement
import re


class ElementPrioritizer:
    """
    Prioritizes page elements based on semantic importance and functionality.
    This addresses the first key limitation mentioned - recognizing primary elements.
    """
    
    def __init__(self):
        # Priority weights for different element types
        self.element_type_weights = {
            'navigation': 0.9,
            'button': 0.8,
            'link': 0.7,
            'form': 0.75,
            'header': 0.6,
            'content': 0.4,
            'media': 0.5,
            'unknown': 0.1
        }
        
        # Keywords that indicate importance
        self.important_keywords = {
            'navigation': ['nav', 'menu', 'navigation', 'navbar', 'header'],
            'action': ['login', 'signup', 'register', 'submit', 'search', 'buy', 'purchase', 'order', 'checkout'],
            'settings': ['settings', 'config', 'preferences', 'options', 'account', 'profile'],
            'primary': ['main', 'primary', 'hero', 'featured', 'important', 'key'],
            'content': ['content', 'article', 'text', 'body', 'description']
        }
        
        # Class names that indicate importance
        self.priority_classes = {
            'high': ['nav', 'navbar', 'navigation', 'menu', 'header', 'btn-primary', 'main-nav', 'primary-nav'],
            'medium': ['btn', 'button', 'link', 'menu-item', 'nav-item', 'settings'],
            'low': ['footer', 'sidebar', 'aside', 'advertisement', 'ad']
        }
    
    def calculate_priority(self, element: PageElement) -> float:
        """
        Calculate priority score for a page element.
        
        Args:
            element: PageElement to prioritize
            
        Returns:
            Priority score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score from element type
        score += self.element_type_weights.get(element.element_type, 0.1)
        
        # Boost score based on text content
        score += self._analyze_text_content(element.text)
        
        # Boost score based on attributes
        score += self._analyze_attributes(element.attributes)
        
        # Boost score based on tag hierarchy
        score += self._analyze_tag_importance(element.tag)
        
        # Normalize score to [0, 1]
        return min(1.0, max(0.0, score))
    
    def _analyze_text_content(self, text: str) -> float:
        """
        Analyze text content for importance indicators.
        
        Args:
            text: Text content of the element
            
        Returns:
            Score boost based on text content
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        boost = 0.0
        
        # Check for important keywords
        for category, keywords in self.important_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category == 'navigation':
                        boost += 0.3
                    elif category == 'action':
                        boost += 0.25
                    elif category == 'settings':
                        boost += 0.2
                    elif category == 'primary':
                        boost += 0.15
                    else:
                        boost += 0.1
        
        # Shorter, concise text often indicates actions/navigation
        if len(text) <= 20 and text.strip():
            boost += 0.1
        
        # All caps text often indicates importance
        if text.isupper() and len(text) > 2:
            boost += 0.1
        
        return min(0.5, boost)  # Cap at 0.5
    
    def _analyze_attributes(self, attributes: Dict[str, str]) -> float:
        """
        Analyze element attributes for importance indicators.
        
        Args:
            attributes: Dictionary of element attributes
            
        Returns:
            Score boost based on attributes
        """
        boost = 0.0
        
        # Check class names
        class_names = attributes.get('class', '').lower()
        if class_names:
            for priority_level, classes in self.priority_classes.items():
                for cls in classes:
                    if cls in class_names:
                        if priority_level == 'high':
                            boost += 0.3
                        elif priority_level == 'medium':
                            boost += 0.2
                        elif priority_level == 'low':
                            boost -= 0.1
        
        # Check ID
        element_id = attributes.get('id', '').lower()
        if element_id:
            if any(keyword in element_id for keyword in ['nav', 'menu', 'header', 'main']):
                boost += 0.2
        
        # Check role attribute
        role = attributes.get('role', '').lower()
        if role:
            if role in ['navigation', 'menu', 'menubar', 'button']:
                boost += 0.25
            elif role in ['main', 'primary']:
                boost += 0.2
        
        # Check for href (links)
        if 'href' in attributes:
            href = attributes['href'].lower()
            if href and not href.startswith('#'):
                boost += 0.15
        
        # Check for data attributes that might indicate importance
        for attr, value in attributes.items():
            if attr.startswith('data-'):
                if any(keyword in value.lower() for keyword in ['nav', 'menu', 'action', 'button']):
                    boost += 0.1
        
        return min(0.4, boost)  # Cap at 0.4
    
    def _analyze_tag_importance(self, tag: str) -> float:
        """
        Analyze HTML tag for inherent importance.
        
        Args:
            tag: HTML tag name
            
        Returns:
            Score boost based on tag type
        """
        tag_lower = tag.lower()
        
        # High importance tags
        if tag_lower in ['nav', 'header', 'main']:
            return 0.2
        
        # Medium importance tags
        if tag_lower in ['button', 'a', 'form', 'input']:
            return 0.15
        
        # Header tags with decreasing importance
        if tag_lower in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            header_level = int(tag_lower[1])
            return 0.2 - (header_level * 0.02)
        
        # Other structural tags
        if tag_lower in ['article', 'section', 'aside']:
            return 0.1
        
        return 0.0
    
    def get_priority_explanation(self, element: PageElement) -> Dict:
        """
        Get detailed explanation of how priority was calculated.
        
        Args:
            element: PageElement to explain
            
        Returns:
            Dictionary with priority calculation details
        """
        explanation = {
            'total_score': self.calculate_priority(element),
            'base_score': self.element_type_weights.get(element.element_type, 0.1),
            'text_boost': self._analyze_text_content(element.text),
            'attribute_boost': self._analyze_attributes(element.attributes),
            'tag_boost': self._analyze_tag_importance(element.tag),
            'element_type': element.element_type,
            'reasoning': []
        }
        
        # Add reasoning
        if element.element_type in ['navigation', 'button', 'link']:
            explanation['reasoning'].append(f"Element type '{element.element_type}' has high importance")
        
        if 'nav' in element.attributes.get('class', '').lower():
            explanation['reasoning'].append("Contains navigation-related CSS class")
        
        if element.text and len(element.text) <= 20:
            explanation['reasoning'].append("Short text content suggests action/navigation element")
        
        return explanation
    
    def sort_elements_by_priority(self, elements: List[PageElement]) -> List[PageElement]:
        """
        Sort elements by priority score.
        
        Args:
            elements: List of PageElement objects
            
        Returns:
            List sorted by priority (highest first)
        """
        return sorted(elements, key=lambda x: x.priority_score, reverse=True) 