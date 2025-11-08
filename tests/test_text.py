"""Tests for text extraction"""

import pytest
from scraper.extractors.text import extract_text


def test_extract_sentences(sample_html):
    """Test sentence extraction"""
    text_data = extract_text(sample_html)
    assert len(text_data["sentences"]) > 0
    assert text_data["sentence_count"] > 0


def test_word_count(sample_html):
    """Test word counting"""
    text_data = extract_text(sample_html)
    assert text_data["word_count"] > 0
    assert text_data["unique_words"] > 0


def test_character_count(sample_html):
    """Test character counting"""
    text_data = extract_text(sample_html)
    assert text_data["char_count"] > 0


def test_keywords_extraction(sample_html):
    """Test keyword extraction"""
    text_data = extract_text(sample_html)
    assert isinstance(text_data["keywords"], list)
    assert len(text_data["keywords"]) > 0


def test_average_sentence_length(sample_html):
    """Test average sentence length calculation"""
    text_data = extract_text(sample_html)
    assert text_data["avg_sentence_length"] > 0
    expected_avg = text_data["word_count"] / text_data["sentence_count"]
    assert text_data["avg_sentence_length"] == expected_avg
