"""Tests for link extraction"""

import pytest
from scraper.extractors.links import extract_links


def test_extract_internal_links(sample_html, sample_url):
    """Test internal link extraction"""
    links = extract_links(sample_html, sample_url)
    assert len(links["internal"]) > 0
    # Should contain the normalized internal link
    assert any("example.com/internal-link" in link for link in links["internal"])


def test_extract_external_links(sample_html, sample_url):
    """Test external link extraction"""
    links = extract_links(sample_html, sample_url)
    assert len(links["external"]) > 0
    assert any("external.com" in link for link in links["external"])


def test_link_categorization(sample_html, sample_url):
    """Test that links are properly categorized"""
    links = extract_links(sample_html, sample_url)
    
    # Check that internal and external are separate
    for internal_link in links["internal"]:
        assert "example.com" in internal_link
    
    for external_link in links["external"]:
        assert "example.com" not in external_link


def test_no_links():
    """Test with HTML containing no links"""
    html = "<html><body><p>No links here</p></body></html>"
    links = extract_links(html, "https://example.com")
    assert len(links["internal"]) == 0
    assert len(links["external"]) == 0
