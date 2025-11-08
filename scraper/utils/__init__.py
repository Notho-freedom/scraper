"""Utility functions"""

from .hash import compute_content_hash
from .robots import can_fetch
from .logger import setup_logging
from .js_detector import needs_javascript, is_spa_url
from .playwright_fetcher import fetch_with_js, get_fetcher, cleanup_fetcher
from .text_cleaner import clean_text, clean_sentences, fix_concatenation, remove_duplicates

__all__ = [
    'compute_content_hash', 
    'can_fetch', 
    'setup_logging',
    'needs_javascript',
    'is_spa_url',
    'fetch_with_js',
    'get_fetcher',
    'cleanup_fetcher',
    'clean_text',
    'clean_sentences',
    'fix_concatenation',
    'remove_duplicates'
]
