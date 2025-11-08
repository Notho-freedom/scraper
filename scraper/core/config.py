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
    
    # Playwright optimization settings
    playwright_pool_size: int = 5  # Number of browser contexts in pool
    playwright_cache_enabled: bool = True  # Enable HTML caching
    playwright_cache_ttl: int = 3600  # Cache TTL in seconds (1 hour)
    playwright_timeout: int = 15000  # Timeout in milliseconds
    playwright_batch_size: int = 10  # Process URLs in batches for parallel fetching
    
    # NLP processing settings
    enable_nlp: bool = False  # Enable advanced NLP processing
    nlp_language: str = "french"  # Language for NLP (french, english)
    nlp_use_spacy: bool = True  # Use spaCy if available (more accurate)
    
    # Correction settings
    enable_correction: bool = False  # Enable grammar/spelling correction
    correction_aggressive: bool = False  # Use aggressive correction mode
    generate_corrected_html: bool = False  # Generate corrected HTML pages
    generate_pdf_report: bool = False  # Generate PDF report with corrections
