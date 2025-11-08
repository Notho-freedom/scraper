"""Tests for configuration"""

import pytest
from scraper.core.config import Config


def test_default_config():
    """Test default configuration values"""
    config = Config()
    
    assert config.max_depth == 30
    assert config.max_pages == 500
    assert config.concurrent_tasks == 50
    assert config.timeout == 15
    assert config.respect_robots == True
    assert config.save_format == "json"


def test_custom_config():
    """Test custom configuration values"""
    config = Config(
        max_depth=5,
        max_pages=100,
        concurrent_tasks=20,
        timeout=10,
        respect_robots=False,
        save_format="csv"
    )
    
    assert config.max_depth == 5
    assert config.max_pages == 100
    assert config.concurrent_tasks == 20
    assert config.timeout == 10
    assert config.respect_robots == False
    assert config.save_format == "csv"


def test_config_immutability():
    """Test that config values can be modified"""
    config = Config()
    config.max_pages = 1000
    assert config.max_pages == 1000
