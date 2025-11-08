"""Tests for resource extraction"""

import pytest
from scraper.extractors.resources import extract_resources


def test_extract_images(sample_html, sample_url):
    """Test image extraction"""
    resources = extract_resources(sample_html, sample_url)
    assert len(resources["images"]) > 0
    assert any("image.jpg" in img["url"] for img in resources["images"])


def test_extract_image_alt_text(sample_html, sample_url):
    """Test image alt text extraction"""
    resources = extract_resources(sample_html, sample_url)
    assert any(img["alt"] == "Test Image" for img in resources["images"])


def test_extract_scripts(sample_html, sample_url):
    """Test script extraction"""
    resources = extract_resources(sample_html, sample_url)
    assert len(resources["scripts"]) > 0
    assert any("script.js" in script for script in resources["scripts"])


def test_resource_url_normalization(sample_html, sample_url):
    """Test that relative URLs are properly converted to absolute"""
    resources = extract_resources(sample_html, sample_url)
    
    # All image URLs should be absolute
    for img in resources["images"]:
        assert img["url"].startswith("http")
    
    # All script URLs should be absolute
    for script in resources["scripts"]:
        assert script.startswith("http")


def test_email_extraction():
    """Test email extraction from content"""
    html = "<html><body><p>Contact us at test@example.com</p></body></html>"
    resources = extract_resources(html, "https://example.com")
    assert "test@example.com" in resources["emails"]


def test_no_resources():
    """Test with HTML containing no resources"""
    html = "<html><body><p>Just text</p></body></html>"
    resources = extract_resources(html, "https://example.com")
    assert len(resources["images"]) == 0
    assert len(resources["scripts"]) == 0
    assert len(resources["stylesheets"]) == 0
