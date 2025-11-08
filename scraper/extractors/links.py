"""Link extraction from HTML"""

from selectolax.parser import HTMLParser
from urllib.parse import urlparse, urljoin
from url_normalize import url_normalize
from collections import defaultdict
from typing import Dict, Set


def extract_links(html: str, base_url: str) -> Dict:
    """Extract and categorize links from HTML"""
    parser = HTMLParser(html)
    domain = urlparse(base_url).netloc
    
    links = {
        "internal": set(),
        "external": set(),
        "anchor_texts": defaultdict(list)
    }
    
    for tag in parser.css("a[href]"):
        href = tag.attributes.get("href")
        anchor_text = tag.text(strip=True)
        
        if href:
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            
            # Clean URL (remove fragments and some query params)
            clean_url = url_normalize(parsed.scheme + "://" + parsed.netloc + parsed.path)
            
            if parsed.netloc == domain:
                links["internal"].add(clean_url)
                if anchor_text:
                    links["anchor_texts"][clean_url].append(anchor_text)
            elif parsed.scheme in ['http', 'https']:
                links["external"].add(full)
    
    return links
