"""Resource extraction from HTML"""

from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import re
from typing import Dict


def extract_resources(html: str, base_url: str) -> Dict:
    """Extract resources like images, scripts, stylesheets from HTML"""
    parser = HTMLParser(html)
    
    resources = {
        "images": [],
        "scripts": [],
        "stylesheets": [],
        "links_external": [],
        "emails": [],
        "phones": []
    }
    
    # Images
    for img in parser.css("img[src]"):
        src = img.attributes.get("src")
        alt = img.attributes.get("alt", "")
        if src:
            full_url = urljoin(base_url, src)
            resources["images"].append({"url": full_url, "alt": alt})
    
    # Scripts
    for script in parser.css("script[src]"):
        src = script.attributes.get("src")
        if src:
            full_url = urljoin(base_url, src)
            resources["scripts"].append(full_url)
    
    # Stylesheets
    for link in parser.css('link[rel="stylesheet"]'):
        href = link.attributes.get("href")
        if href:
            full_url = urljoin(base_url, href)
            resources["stylesheets"].append(full_url)
    
    # Extract emails and phones from text
    body_text = parser.body.text() if parser.body else ""
    resources["emails"] = list(set(re.findall(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
        body_text
    )))
    resources["phones"] = list(set(re.findall(
        r'\b(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b', 
        body_text
    )))
    
    return resources
