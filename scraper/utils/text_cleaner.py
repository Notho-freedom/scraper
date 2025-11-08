"""Text cleaning utilities for scraped content"""

import re
from typing import List


def fix_concatenation(text: str) -> str:
    """
    Add spaces between concatenated words (e.g., 'InstallationProfessionnelle' -> 'Installation Professionnelle')
    
    Args:
        text: Text with concatenated words
        
    Returns:
        Text with proper spacing
    """
    # Add space before uppercase letter preceded by lowercase
    text = re.sub(r'(?<=[a-zéèàùâêîôûç])(?=[A-ZÉÈÀÙÂÊÎÔÛ])', ' ', text)
    
    # Add space before digit preceded by letter
    text = re.sub(r'(?<=[a-zA-Zéèàùâêîôûç])(?=\d)', ' ', text)
    
    # Add space after digit followed by letter
    text = re.sub(r'(?<=\d)(?=[a-zA-Zéèàùâêîôûç])', ' ', text)
    
    # Add space after special chars (+, -, etc.) followed by letter
    text = re.sub(r'(?<=[+\-*/=])(?=[a-zA-Zéèàùâêîôûç])', ' ', text)
    
    return text


def remove_duplicates(sentences: List[str]) -> List[str]:
    """
    Remove duplicate sentences while preserving order
    
    Args:
        sentences: List of sentences that may contain duplicates
        
    Returns:
        Deduplicated list of sentences
    """
    seen = set()
    result = []
    
    for sentence in sentences:
        # Normalize for comparison (lowercase, strip whitespace)
        normalized = sentence.lower().strip()
        
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(sentence)
    
    return result


def remove_consecutive_duplicates(text: str) -> str:
    """
    Remove consecutive duplicate words from text
    
    Args:
        text: Text with possible consecutive duplicates
        
    Returns:
        Text with consecutive duplicates removed
    """
    # Remove consecutive duplicate words
    text = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', text, flags=re.IGNORECASE)
    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text
    
    Args:
        text: Text with irregular whitespace
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove spaces before punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    # Ensure space after punctuation
    text = re.sub(r'([.,;:!?])(?=[^\s\d])', r'\1 ', text)
    
    return text.strip()


def clean_text(text: str) -> str:
    """
    Apply all text cleaning operations
    
    Args:
        text: Raw text from scraper
        
    Returns:
        Cleaned and normalized text
    """
    # Apply all cleaning operations in order
    text = fix_concatenation(text)
    text = remove_consecutive_duplicates(text)
    text = normalize_whitespace(text)
    
    return text


def clean_sentences(sentences: List[str]) -> List[str]:
    """
    Clean and deduplicate a list of sentences
    
    Args:
        sentences: List of raw sentences
        
    Returns:
        Cleaned and deduplicated sentences
    """
    # Clean each sentence
    cleaned = [clean_text(s) for s in sentences]
    
    # Remove empty sentences
    cleaned = [s for s in cleaned if s]
    
    # Remove duplicates
    cleaned = remove_duplicates(cleaned)
    
    return cleaned
