"""Tests for text cleaning utilities"""

import pytest
from scraper.utils.text_cleaner import (
    fix_concatenation,
    remove_duplicates,
    remove_consecutive_duplicates,
    normalize_whitespace,
    clean_text,
    clean_sentences
)


def test_fix_concatenation():
    """Test fixing concatenated words"""
    assert fix_concatenation("InstallationProfessionnelle") == "Installation Professionnelle"
    assert fix_concatenation("ServicesExcellence") == "Services Excellence"
    assert fix_concatenation("500+Projets") == "500+ Projets"
    assert fix_concatenation("Années15+") == "Années 15+"


def test_remove_duplicates():
    """Test removing duplicate sentences"""
    sentences = [
        "First sentence.",
        "Second sentence.",
        "First sentence.",  # duplicate
        "Third sentence."
    ]
    result = remove_duplicates(sentences)
    assert len(result) == 3
    assert result == ["First sentence.", "Second sentence.", "Third sentence."]


def test_remove_consecutive_duplicates():
    """Test removing consecutive duplicate words"""
    text = "This is is a test test test."
    result = remove_consecutive_duplicates(text)
    assert result == "This is a test."


def test_normalize_whitespace():
    """Test whitespace normalization"""
    text = "Text  with   multiple    spaces"
    assert normalize_whitespace(text) == "Text with multiple spaces"
    
    text = "Text ,with bad punctuation ."
    assert normalize_whitespace(text) == "Text, with bad punctuation."


def test_clean_text():
    """Test complete text cleaning"""
    text = "InstallationProfessionnelle  is  is  excellent"
    result = clean_text(text)
    assert result == "Installation Professionnelle is excellent"


def test_clean_sentences():
    """Test cleaning sentence lists"""
    sentences = [
        "InstallationProfessionnelle",
        "InstallationProfessionnelle",  # duplicate
        "  Another  sentence  ",
        "",  # empty
        "Final sentence"
    ]
    result = clean_sentences(sentences)
    assert len(result) == 3
    assert "Installation Professionnelle" in result
    assert "Another sentence" in result
    assert "Final sentence" in result


def test_fix_concatenation_with_accents():
    """Test concatenation fix with French accents"""
    assert fix_concatenation("ÉquipementsÉlectriques") == "Équipements Électriques"
    assert fix_concatenation("SystèmesAutomatisés") == "Systèmes Automatisés"
