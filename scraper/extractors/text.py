"""Text extraction from HTML"""

from selectolax.parser import HTMLParser
import re
from collections import Counter
from typing import Dict


def extract_text(html: str) -> Dict:
    """Extract and analyze text content from HTML"""
    parser = HTMLParser(html)
    
    # Remove script, style, and navigation elements
    for elem in parser.css("script, style, nav, footer, header, noscript"):
        elem.decompose()
    
    # Try to find main content first
    main_selectors = ["main", "article", ".content", "#content", ".main-content", "section"]
    main_content = None
    
    for selector in main_selectors:
        main_content = parser.css_first(selector)
        if main_content:
            break
    
    # Extract text from visible elements with proper spacing
    if main_content:
        elements = main_content.css("p, h1, h2, h3, h4, h5, h6, li, td, th, div, span")
    else:
        elements = parser.css("body p, body h1, body h2, body h3, body h4, body h5, body h6, body li, body td, body th")
    
    # Get unique text blocks (avoid duplicates from nested elements)
    seen_texts = set()
    texts = []
    
    for elem in elements:
        text = elem.text(strip=True)
        if text and text not in seen_texts:
            seen_texts.add(text)
            texts.append(text)
    
    # Join with proper spacing
    raw_text = " ".join(texts)
    
    # Clean up whitespace
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()
    
    # Split into sentences with better regex
    # Match sentence endings followed by space and capital letter, or end of string
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-ZÉÈÀÙ])|(?<=[.!?])$'
    sentences = [s.strip() for s in re.split(sentence_pattern, raw_text) if s.strip()]
    
    # Additional cleaning: remove very short "sentences" that are likely noise
    sentences = [s for s in sentences if len(s) > 10]
    
    # Remove exact duplicates while preserving order
    seen_sentences = set()
    unique_sentences = []
    for s in sentences:
        s_lower = s.lower()
        if s_lower not in seen_sentences:
            seen_sentences.add(s_lower)
            unique_sentences.append(s)
    
    sentences = unique_sentences
    
    # Word analysis
    words = raw_text.split()
    word_count = len(words)
    unique_words = len(set(w.lower() for w in words if len(w) > 3))
    
    # Extract keywords (simple frequency analysis, excluding common words)
    common_words = {'dans', 'pour', 'avec', 'nous', 'vous', 'plus', 'tout', 'tous', 
                   'être', 'cette', 'sont', 'mais', 'leur', 'peut', 'fait', 'très',
                   'aussi', 'comme', 'notre', 'votre', 'entre', 'sans', 'sous'}
    
    word_freq = Counter(w.lower() for w in words 
                       if len(w) > 4 and w.isalpha() and w.lower() not in common_words)
    top_keywords = [word for word, _ in word_freq.most_common(10)]
    
    return {
        "sentences": sentences[:100],  # Limit for storage
        "word_count": word_count,
        "unique_words": unique_words,
        "char_count": len(raw_text),
        "sentence_count": len(sentences),
        "keywords": top_keywords,
        "avg_sentence_length": word_count / len(sentences) if sentences else 0
    }
