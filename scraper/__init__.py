"""
ULTRACORE REAPER v2.0 - Advanced Web Scraper & Analyzer
"""

__version__ = "2.0.0"
__author__ = "ULTRACORE"

from .core.config import Config
from .core.state import CrawlerState
from .core.crawler import Crawler

__all__ = ['Config', 'CrawlerState', 'Crawler']
