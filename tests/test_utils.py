"""Tests for utility functions"""

import pytest
from scraper.utils.hash import compute_content_hash


def test_content_hash_consistency():
    """Test that same content produces same hash"""
    text1 = "This is a test sentence."
    text2 = "This is a test sentence."
    
    hash1 = compute_content_hash(text1)
    hash2 = compute_content_hash(text2)
    
    assert hash1 == hash2


def test_content_hash_normalization():
    """Test that whitespace variations produce same hash"""
    text1 = "This   is   a   test"
    text2 = "This is a test"
    
    hash1 = compute_content_hash(text1)
    hash2 = compute_content_hash(text2)
    
    assert hash1 == hash2


def test_content_hash_case_insensitive():
    """Test that case differences produce same hash"""
    text1 = "This Is A Test"
    text2 = "this is a test"
    
    hash1 = compute_content_hash(text1)
    hash2 = compute_content_hash(text2)
    
    assert hash1 == hash2


def test_different_content_different_hash():
    """Test that different content produces different hash"""
    text1 = "This is test one"
    text2 = "This is test two"
    
    hash1 = compute_content_hash(text1)
    hash2 = compute_content_hash(text2)
    
    assert hash1 != hash2


def test_hash_format():
    """Test that hash is in expected format"""
    text = "Test content"
    hash_value = compute_content_hash(text)
    
    # MD5 hash should be 32 characters
    assert len(hash_value) == 32
    # Should be hexadecimal
    assert all(c in '0123456789abcdef' for c in hash_value)
