"""Content hashing utility"""

import hashlib
import re


def compute_content_hash(text: str) -> str:
    """Generate hash of main content for duplicate detection"""
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()
