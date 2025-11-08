"""Logging configuration"""

import logging
import sys


def setup_logging(level: str):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
