"""Tests for state management"""

import pytest
from scraper.core.state import CrawlerState


def test_initial_state():
    """Test initial state values"""
    state = CrawlerState()
    
    assert len(state.visited) == 0
    assert len(state.results) == 0
    assert len(state.errors) == 0
    assert state.stats["pages"] == 0
    assert state.stats["words"] == 0


def test_add_visited():
    """Test adding visited URLs"""
    state = CrawlerState()
    
    state.add_visited("https://example.com")
    assert state.is_visited("https://example.com")
    assert not state.is_visited("https://other.com")


def test_add_result():
    """Test adding results"""
    state = CrawlerState()
    
    result = {"url": "https://example.com", "data": "test"}
    state.add_result(result)
    
    assert len(state.results) == 1
    assert state.results[0] == result


def test_add_error():
    """Test adding errors"""
    state = CrawlerState()
    
    error = {"url": "https://example.com", "error": "timeout"}
    state.add_error(error)
    
    assert len(state.errors) == 1
    assert state.errors[0] == error


def test_increment_stat():
    """Test incrementing statistics"""
    state = CrawlerState()
    
    state.increment_stat("pages")
    assert state.stats["pages"] == 1
    
    state.increment_stat("pages", 5)
    assert state.stats["pages"] == 6


def test_add_response_time():
    """Test adding response times"""
    state = CrawlerState()
    
    state.add_response_time(0.5)
    state.add_response_time(0.3)
    
    assert len(state.stats["response_times"]) == 2
    assert 0.5 in state.stats["response_times"]
    assert 0.3 in state.stats["response_times"]


def test_mark_duplicate():
    """Test marking duplicates"""
    state = CrawlerState()
    
    hash_value = "abc123"
    state.mark_duplicate(hash_value, "https://example.com")
    state.mark_duplicate(hash_value, "https://duplicate.com")
    
    assert len(state.duplicates[hash_value]) == 2
    assert "https://example.com" in state.duplicates[hash_value]
    assert "https://duplicate.com" in state.duplicates[hash_value]
