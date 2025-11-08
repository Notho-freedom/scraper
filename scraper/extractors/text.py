"""Text extraction from HTML"""

from selectolax.parser import HTMLParser
import re
from collections import Counter
from typing import Dict


def extract_text(html: str) -> Dict:
    """Extract and analyze text content from HTML"""
    parser = HTMLParser(html)
    
    # Remove script and style elements
    for elem in parser.css("script, style, nav, footer, header"):
        elem.decompose()
    
    # Extract main content
    main_content = parser.css_first("main, article, .content, #content")
    if main_content:
        texts = [node.text(strip=True) for node in main_content.css("*") if node.text(strip=True)]
    else:
        texts = [node.text(strip=True) for node in parser.css("body *") if node.text(strip=True)]
    
    raw_text = " ".join(texts)
    raw_text = re.sub(r"\s+", " ", raw_text)
    
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text) if s.strip()]
    
    # Word analysis
    words = raw_text.split()
    word_count = len(words)
    unique_words = len(set(w.lower() for w in words if len(w) > 3))
    
    # Extract keywords (simple frequency analysis)
    word_freq = Counter(w.lower() for w in words if len(w) > 4 and w.isalpha())
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
