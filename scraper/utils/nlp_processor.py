"""NLP processing utilities for text analysis and structuring"""

import re
import logging
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
from dataclasses import dataclass

# Optional NLP imports with graceful fallback
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available. Install with: pip install nltk")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available. Install with: pip install spacy")


@dataclass
class NLPResult:
    """Structured NLP processing result"""
    sentences: List[str]
    paragraphs: List[str]
    tokens: List[str]
    word_count: int
    unique_words: int
    lemmatized_tokens: List[str]
    named_entities: List[Dict[str, str]]
    keywords: List[str]
    language: str
    readability_score: float
    
    @property
    def sentence_count(self) -> int:
        """Number of sentences"""
        return len(self.sentences)
    
    @property
    def paragraph_count(self) -> int:
        """Number of paragraphs"""
        return len(self.paragraphs)


class NLPProcessor:
    """Advanced NLP processor with NLTK and spaCy support"""
    
    def __init__(self, language: str = 'french', use_spacy: bool = True):
        """
        Initialize NLP processor.
        
        Args:
            language: Target language ('french', 'english')
            use_spacy: Try to use spaCy if available (more accurate but slower)
        """
        self.language = language
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        
        # Initialize NLTK components
        if NLTK_AVAILABLE:
            self._ensure_nltk_data()
            self.stemmer = PorterStemmer()
            self.lemmatizer = WordNetLemmatizer()
            
            # Load stopwords
            lang_map = {'french': 'french', 'english': 'english'}
            try:
                self.stopwords = set(stopwords.words(lang_map.get(language, 'english')))
            except Exception as e:
                logging.warning(f"Could not load stopwords: {e}")
                self.stopwords = set()
        
        # Initialize spaCy model
        self.nlp_model = None
        if self.use_spacy:
            try:
                model_map = {
                    'french': 'fr_core_news_sm',
                    'english': 'en_core_web_sm'
                }
                model_name = model_map.get(language, 'en_core_web_sm')
                self.nlp_model = spacy.load(model_name)
                logging.info(f"spaCy model '{model_name}' loaded successfully")
            except Exception as e:
                logging.warning(f"Could not load spaCy model: {e}")
                logging.info("Install with: python -m spacy download fr_core_news_sm")
                self.use_spacy = False
    
    @staticmethod
    def _ensure_nltk_data():
        """Ensure required NLTK data is downloaded"""
        required_data = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        
        for data_name in required_data:
            try:
                nltk.data.find(f'tokenizers/{data_name}')
            except LookupError:
                try:
                    nltk.download(data_name, quiet=True)
                except Exception as e:
                    logging.warning(f"Could not download NLTK data '{data_name}': {e}")
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text: lowercase, remove extra spaces, fix punctuation.
        
        Args:
            text: Raw text
            
        Returns:
            Normalized text
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix punctuation spacing
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])(\w)', r'\1 \2', text)
        
        # Normalize quotes
        text = re.sub(r'[""]', '"', text)
        text = re.sub(r"['']", "'", text)
        
        return text.strip()
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if self.use_spacy and self.nlp_model:
            doc = self.nlp_model(text)
            return [sent.text.strip() for sent in doc.sents]
        
        elif NLTK_AVAILABLE:
            return sent_tokenize(text, language=self.language)
        
        else:
            # Fallback: simple regex
            sentences = re.split(r'[.!?]+\s+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def tokenize_words(self, text: str, remove_stopwords: bool = False) -> List[str]:
        """
        Split text into words/tokens.
        
        Args:
            text: Input text
            remove_stopwords: Remove common stopwords
            
        Returns:
            List of tokens
        """
        if self.use_spacy and self.nlp_model:
            doc = self.nlp_model(text)
            tokens = [token.text for token in doc if not token.is_punct and not token.is_space]
        
        elif NLTK_AVAILABLE:
            tokens = word_tokenize(text, language=self.language)
            # Remove punctuation
            tokens = [t for t in tokens if re.match(r'\w', t)]
        
        else:
            # Fallback: simple split
            tokens = re.findall(r'\b\w+\b', text)
        
        # Remove stopwords if requested
        if remove_stopwords and self.stopwords:
            tokens = [t for t in tokens if t.lower() not in self.stopwords]
        
        return tokens
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """
        Lemmatize tokens (reduce to base form).
        
        Args:
            tokens: List of tokens
            
        Returns:
            Lemmatized tokens
        """
        if self.use_spacy and self.nlp_model:
            text = ' '.join(tokens)
            doc = self.nlp_model(text)
            return [token.lemma_ for token in doc if not token.is_punct]
        
        elif NLTK_AVAILABLE:
            return [self.lemmatizer.lemmatize(token.lower()) for token in tokens]
        
        else:
            # Fallback: lowercase only
            return [token.lower() for token in tokens]
    
    def extract_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Input text
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines, tabs, or <p> tags
        paragraphs = re.split(r'\n\s*\n|\t+|</?p>', text)
        
        # Clean and filter
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Minimum length filter (avoid single words)
        paragraphs = [p for p in paragraphs if len(p.split()) >= 5]
        
        return paragraphs
    
    def remove_duplicates(self, items: List[str], case_sensitive: bool = False) -> List[str]:
        """
        Remove duplicate items while preserving order.
        
        Args:
            items: List of strings
            case_sensitive: Consider case in comparison
            
        Returns:
            Deduplicated list
        """
        seen: Set[str] = set()
        result = []
        
        for item in items:
            key = item if case_sensitive else item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result
    
    def extract_named_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract named entities (persons, locations, organizations).
        
        Args:
            text: Input text
            
        Returns:
            List of entities with type
        """
        if not self.use_spacy or not self.nlp_model:
            return []
        
        doc = self.nlp_model(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        return entities
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract most important keywords using TF-IDF-like approach.
        
        Args:
            text: Input text
            top_n: Number of keywords to return
            
        Returns:
            List of keywords
        """
        # Tokenize and lemmatize
        tokens = self.tokenize_words(text, remove_stopwords=True)
        lemmatized = self.lemmatize(tokens)
        
        # Filter by length and frequency
        filtered = [t for t in lemmatized if len(t) > 3]
        
        # Count occurrences
        counter = Counter(filtered)
        
        # Return top N
        return [word for word, _ in counter.most_common(top_n)]
    
    def calculate_readability(self, text: str) -> float:
        """
        Calculate simple readability score (0-100).
        Based on average sentence length and word length.
        
        Args:
            text: Input text
            
        Returns:
            Readability score (higher = easier to read)
        """
        sentences = self.tokenize_sentences(text)
        words = self.tokenize_words(text)
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(w) for w in words) / len(words)
        
        # Simplified Flesch reading ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 5)
        
        # Clamp to 0-100
        return max(0.0, min(100.0, score))
    
    def process(self, text: str, deduplicate: bool = True) -> NLPResult:
        """
        Full NLP processing pipeline.
        
        Args:
            text: Raw text
            deduplicate: Remove duplicate sentences
            
        Returns:
            NLPResult with structured data
        """
        # Normalize
        normalized_text = self.normalize_text(text)
        
        # Extract sentences
        sentences = self.tokenize_sentences(normalized_text)
        if deduplicate:
            sentences = self.remove_duplicates(sentences)
        
        # Extract paragraphs
        paragraphs = self.extract_paragraphs(text)
        
        # Tokenize
        tokens = self.tokenize_words(normalized_text)
        unique_tokens = set(t.lower() for t in tokens)
        
        # Lemmatize
        lemmatized = self.lemmatize(tokens)
        
        # Named entities
        entities = self.extract_named_entities(normalized_text)
        
        # Keywords
        keywords = self.extract_keywords(normalized_text)
        
        # Readability
        readability = self.calculate_readability(normalized_text)
        
        return NLPResult(
            sentences=sentences,
            paragraphs=paragraphs,
            tokens=tokens,
            word_count=len(tokens),
            unique_words=len(unique_tokens),
            lemmatized_tokens=lemmatized,
            named_entities=entities,
            keywords=keywords,
            language=self.language,
            readability_score=round(readability, 2)
        )


def process_text_with_nlp(text: str, language: str = 'french', use_spacy: bool = True) -> Dict:
    """
    Convenience function to process text with NLP.
    
    Args:
        text: Input text
        language: Language code
        use_spacy: Use spaCy if available
        
    Returns:
        Dictionary with processed data
    """
    processor = NLPProcessor(language=language, use_spacy=use_spacy)
    result = processor.process(text)
    
    return {
        'sentences': result.sentences,
        'sentence_count': len(result.sentences),
        'paragraphs': result.paragraphs,
        'paragraph_count': len(result.paragraphs),
        'word_count': result.word_count,
        'unique_words': result.unique_words,
        'vocabulary_richness': round(result.unique_words / max(result.word_count, 1), 3),
        'keywords': result.keywords,
        'named_entities': result.named_entities,
        'readability_score': result.readability_score,
        'language': result.language
    }
