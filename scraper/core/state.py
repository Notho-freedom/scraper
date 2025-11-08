"""Crawler state management"""

import time
from typing import Set, Dict, List
from collections import Counter, defaultdict
from urllib.robotparser import RobotFileParser


class CrawlerState:
    """Maintains state for the crawling process"""
    
    def __init__(self):
        self.visited: Set[str] = set()
        self.results: List[Dict] = []
        self.errors: List[Dict] = []
        self.duplicates: Dict[str, List[str]] = defaultdict(list)
        self.stats = {
            "start": time.time(),
            "pages": 0,
            "words": 0,
            "images": 0,
            "scripts": 0,
            "errors": 0,
            "depths": {},
            "response_times": [],
            "content_types": Counter(),
            "status_codes": Counter()
        }
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.content_hashes: Dict[str, str] = {}
    
    def add_visited(self, url: str):
        """Mark a URL as visited"""
        self.visited.add(url)
    
    def is_visited(self, url: str) -> bool:
        """Check if URL has been visited"""
        return url in self.visited
    
    def add_result(self, result: Dict):
        """Add a page result"""
        self.results.append(result)
    
    def add_error(self, error: Dict):
        """Add an error"""
        self.errors.append(error)
    
    def increment_stat(self, stat: str, value: int = 1):
        """Increment a statistic"""
        self.stats[stat] += value
    
    def add_response_time(self, time_value: float):
        """Add a response time measurement"""
        self.stats["response_times"].append(time_value)
    
    def mark_duplicate(self, content_hash: str, url: str):
        """Mark a URL as duplicate"""
        self.duplicates[content_hash].append(url)
