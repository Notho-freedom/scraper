"""Text extraction from HTML"""

from selectolax.parser import HTMLParser
import re
from collections import Counter
from typing import Dict, Optional


def extract_text(html: str, enable_nlp: bool = False, nlp_config: Dict = None, 
                enable_correction: bool = False) -> Dict:
    """
    Extract and analyze text content from HTML.
    
    Args:
        html: HTML content
        enable_nlp: Enable advanced NLP processing
        nlp_config: NLP configuration dict (language, use_spacy)
        enable_correction: Enable grammar/spelling correction
    
    Returns:
        Dictionary with text analysis
    """
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
    
    # Base result
    result = {
        "sentences": sentences[:100],  # Limit for storage
        "word_count": word_count,
        "unique_words": unique_words,
        "char_count": len(raw_text),
        "sentence_count": len(sentences),
        "keywords": top_keywords,
        "avg_sentence_length": word_count / len(sentences) if sentences else 0
    }
    
    # Add NLP processing if enabled
    if enable_nlp:
        try:
            from ..utils.nlp_processor import process_text_with_nlp
            
            nlp_config = nlp_config or {}
            language = nlp_config.get('language', 'french')
            use_spacy = nlp_config.get('use_spacy', True)
            
            nlp_result = process_text_with_nlp(raw_text, language=language, use_spacy=use_spacy)
            
            # Merge NLP results (NLP versions replace basic ones)
            result.update({
                "sentences": nlp_result['sentences'][:100],
                "sentence_count": nlp_result['sentence_count'],
                "paragraphs": nlp_result['paragraphs'][:50],
                "paragraph_count": nlp_result['paragraph_count'],
                "keywords": nlp_result['keywords'],
                "named_entities": nlp_result['named_entities'][:20],
                "vocabulary_richness": nlp_result['vocabulary_richness'],
                "readability_score": nlp_result['readability_score'],
                "nlp_enabled": True,
                "nlp_language": nlp_result['language']
            })
            
        except Exception as e:
            import logging
            logging.warning(f"NLP processing failed: {e}")
            result["nlp_enabled"] = False
            result["nlp_error"] = str(e)
    else:
        result["nlp_enabled"] = False
    
    # Add correction if enabled
    if enable_correction:
        try:
            from ..utils.text_corrector import TextCorrector
            from ..utils.grammar_checker import GrammarChecker
            
            nlp_config = nlp_config or {}
            language = nlp_config.get('language', 'french')
            
            # Use singleton instances to avoid re-initialization
            checker = GrammarChecker.get_instance(language=language)
            corrector = TextCorrector.get_instance(language=language)
            
            paragraphs_to_correct = result.get('paragraphs', []) or [raw_text]
            corrected_paragraphs = []
            all_errors = []
            total_corrections = 0
            corrections_by_type = {}
            
            for para in paragraphs_to_correct:
                # Check for errors
                check_result = checker.check_text(para)
                
                # Correct text
                corr_result = corrector.correct_text(para)
                
                corrected_paragraphs.append({
                    'original_text': para,
                    'corrected_text': corr_result.corrected_text,
                    'corrections': [c.to_dict() for c in corr_result.corrections],
                    'quality_score': corr_result.quality_score
                })
                
                # Aggregate statistics
                all_errors.extend([e.to_dict() for e in check_result.errors])
                total_corrections += corr_result.correction_count
                
                for etype, count in corr_result.corrections_by_type.items():
                    corrections_by_type[etype] = corrections_by_type.get(etype, 0) + count
            
            # Calculate average quality
            avg_quality = sum(p['quality_score'] for p in corrected_paragraphs) / len(corrected_paragraphs) if corrected_paragraphs else 100.0
            
            result["correction_enabled"] = True
            result["corrections"] = {
                "corrected_paragraphs": corrected_paragraphs,
                "all_errors": all_errors[:50],  # Limit errors
                "correction_count": total_corrections,
                "corrections_by_type": corrections_by_type,
                "average_quality": avg_quality
            }
            
        except Exception as e:
            import logging
            logging.warning(f"Correction processing failed: {e}")
            result["correction_enabled"] = False
            result["correction_error"] = str(e)
    else:
        result["correction_enabled"] = False
    
    return result
