"""Tests for metadata extraction"""

import pytest
from scraper.extractors.metadata import extract_metadata


def test_extract_title(sample_html):
    """Test title extraction"""
    meta = extract_metadata(sample_html)
    assert meta["title"] == "Test Page"


def test_extract_description(sample_html):
    """Test description extraction"""
    meta = extract_metadata(sample_html)
    assert meta["description"] == "This is a test page"


def test_extract_keywords(sample_html):
    """Test keywords extraction"""
    meta = extract_metadata(sample_html)
    assert meta["keywords"] == "test, sample, page"


def test_extract_og_tags(sample_html):
    """Test Open Graph tags extraction"""
    meta = extract_metadata(sample_html)
    assert meta["og"]["title"] == "Test OG Title"
    assert meta["og"]["description"] == "Test OG Description"


def test_extract_headings(sample_html):
    """Test heading extraction"""
    meta = extract_metadata(sample_html)
    assert "Main Heading" in meta["h1"]
    assert "Subheading One" in meta["h2"]
    assert "Subheading Two" in meta["h2"]
    assert len(meta["h2"]) == 2


def test_extract_language(sample_html):
    """Test language extraction"""
    meta = extract_metadata(sample_html)
    assert meta["language"] == "en"
