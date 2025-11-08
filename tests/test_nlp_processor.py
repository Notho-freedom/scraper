"""Tests for NLP processor"""

import pytest
from scraper.utils.nlp_processor import (
    NLPProcessor,
    process_text_with_nlp,
    NLTK_AVAILABLE,
    SPACY_AVAILABLE
)


@pytest.fixture
def sample_text_fr():
    return """
    Multi-Tess est votre partenaire de confiance pour tous vos projets d'ascenseurs.
    En tant que principal fournisseur national, nous concevons et fabriquons une gamme complète.
    Notre expertise couvre la conception sur mesure, l'installation professionnelle et la maintenance préventive.
    Chaque projet Multi-Tess est une histoire unique de défi technique et de solution innovante.
    """


@pytest.fixture
def sample_text_en():
    return """
    Multi-Tess is your trusted partner for all elevator projects.
    As the leading national supplier, we design and manufacture a complete range.
    Our expertise covers custom design, professional installation, and preventive maintenance.
    Each Multi-Tess project is a unique story of technical challenge and innovative solution.
    """


def test_normalize_text():
    """Test text normalization"""
    processor = NLPProcessor(language='french')
    
    text = "Ceci  est   un    test .Avec ponctuation bizarre ."
    normalized = processor.normalize_text(text)
    
    assert "  " not in normalized
    assert " ." not in normalized
    assert normalized.count('.') == 2


def test_tokenize_sentences_french(sample_text_fr):
    """Test sentence tokenization for French"""
    processor = NLPProcessor(language='french', use_spacy=False)
    sentences = processor.tokenize_sentences(sample_text_fr)
    
    assert len(sentences) >= 3
    assert any('Multi-Tess' in s for s in sentences)


def test_tokenize_words_french(sample_text_fr):
    """Test word tokenization"""
    processor = NLPProcessor(language='french', use_spacy=False)
    tokens = processor.tokenize_words(sample_text_fr)
    
    assert len(tokens) > 10
    assert 'Multi-Tess' in tokens or 'Multi' in tokens


def test_tokenize_words_remove_stopwords(sample_text_fr):
    """Test stopword removal"""
    if not NLTK_AVAILABLE:
        pytest.skip("NLTK not available")
    
    processor = NLPProcessor(language='french', use_spacy=False)
    
    tokens_with_stopwords = processor.tokenize_words(sample_text_fr, remove_stopwords=False)
    tokens_without_stopwords = processor.tokenize_words(sample_text_fr, remove_stopwords=True)
    
    assert len(tokens_without_stopwords) < len(tokens_with_stopwords)


def test_extract_paragraphs(sample_text_fr):
    """Test paragraph extraction"""
    processor = NLPProcessor(language='french')
    
    text_with_paragraphs = sample_text_fr.replace('. ', '.\n\n')
    paragraphs = processor.extract_paragraphs(text_with_paragraphs)
    
    assert len(paragraphs) >= 1  # At least one paragraph
    assert all(len(p.split()) >= 5 for p in paragraphs)  # Each has minimum 5 words


def test_remove_duplicates():
    """Test duplicate removal"""
    processor = NLPProcessor(language='french')
    
    items = ["Test 1", "Test 2", "test 1", "Test 3", "TEST 2"]
    
    # Case insensitive
    result = processor.remove_duplicates(items, case_sensitive=False)
    assert len(result) == 3
    
    # Case sensitive
    result_cs = processor.remove_duplicates(items, case_sensitive=True)
    assert len(result_cs) >= 4


def test_extract_keywords(sample_text_fr):
    """Test keyword extraction"""
    processor = NLPProcessor(language='french', use_spacy=False)
    keywords = processor.extract_keywords(sample_text_fr, top_n=5)
    
    assert len(keywords) <= 5
    assert len(keywords) > 0


def test_calculate_readability(sample_text_fr):
    """Test readability score calculation"""
    processor = NLPProcessor(language='french')
    score = processor.calculate_readability(sample_text_fr)
    
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_full_processing_french(sample_text_fr):
    """Test full NLP processing pipeline"""
    processor = NLPProcessor(language='french', use_spacy=False)
    result = processor.process(sample_text_fr, deduplicate=True)
    
    assert result.sentence_count > 0
    assert result.word_count > 0
    assert result.unique_words > 0
    assert len(result.sentences) > 0
    assert len(result.keywords) > 0
    assert result.language == 'french'
    assert 0 <= result.readability_score <= 100


def test_full_processing_english(sample_text_en):
    """Test full NLP processing pipeline for English"""
    processor = NLPProcessor(language='english', use_spacy=False)
    result = processor.process(sample_text_en, deduplicate=True)
    
    assert result.sentence_count > 0
    assert result.word_count > 0
    assert result.language == 'english'


@pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not available")
def test_named_entity_extraction_with_spacy():
    """Test named entity extraction with spaCy"""
    text = "Apple Inc. est basée à Cupertino en Californie. Tim Cook est le PDG."
    
    processor = NLPProcessor(language='french', use_spacy=True)
    entities = processor.extract_named_entities(text)
    
    # Should extract at least some entities
    assert isinstance(entities, list)


def test_process_text_with_nlp_convenience_function(sample_text_fr):
    """Test convenience function"""
    result = process_text_with_nlp(sample_text_fr, language='french', use_spacy=False)
    
    assert 'sentences' in result
    assert 'sentence_count' in result
    assert 'word_count' in result
    assert 'keywords' in result
    assert result['word_count'] > 0


def test_lemmatization(sample_text_fr):
    """Test lemmatization"""
    if not NLTK_AVAILABLE:
        pytest.skip("NLTK not available")
    
    processor = NLPProcessor(language='french', use_spacy=False)
    
    tokens = ['travaillons', 'travaillé', 'travailler', 'travail']
    lemmatized = processor.lemmatize(tokens)
    
    assert len(lemmatized) == len(tokens)
    # Should reduce to base forms (though results vary by language)
    assert all(isinstance(t, str) for t in lemmatized)


def test_processor_without_libraries():
    """Test processor works even without NLTK/spaCy (fallback mode)"""
    processor = NLPProcessor(language='french', use_spacy=False)
    
    text = "Phrase 1. Phrase 2. Phrase 3."
    
    # Should still work with regex fallback
    sentences = processor.tokenize_sentences(text)
    assert len(sentences) >= 2
    
    tokens = processor.tokenize_words(text)
    assert len(tokens) > 0
