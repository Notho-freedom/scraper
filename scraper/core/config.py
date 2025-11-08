"""Configuration dataclass for the scraper"""

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for the web scraper"""
    max_depth: int = 30
    max_pages: int = 500
    concurrent_tasks: int = 50
    timeout: int = 15
    retry_attempts: int = 3
    rate_limit: float = 0.1  # seconds between requests
    user_agent: str = "UltracoreReaper/2.0"
    respect_robots: bool = True
    extract_images: bool = True
    extract_scripts: bool = True
    analyze_sentiment: bool = False
    detect_duplicates: bool = True
    save_format: str = "json"  # json, csv, sqlite, all
    output_dir: str = "output"
    log_level: str = "INFO"
