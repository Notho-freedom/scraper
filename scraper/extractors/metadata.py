"""Metadata extraction from HTML"""

from selectolax.parser import HTMLParser
import json
from typing import Dict


def extract_metadata(html: str) -> Dict:
    """Extract metadata from HTML content"""
    parser = HTMLParser(html)
    
    meta = {
        "title": None,
        "description": None,
        "keywords": None,
        "author": None,
        "canonical": None,
        "language": None,
        "og": {},
        "twitter": {},
        "json_ld": [],
        "h1": [],
        "h2": [],
        "h3": []
    }
    
    # Title
    title_node = parser.css_first("title")
    if title_node:
        meta["title"] = title_node.text(strip=True)
    
    # Headings
    for h1 in parser.css("h1"):
        if h1.text(strip=True):
            meta["h1"].append(h1.text(strip=True))
    for h2 in parser.css("h2"):
        if h2.text(strip=True):
            meta["h2"].append(h2.text(strip=True))
    for h3 in parser.css("h3"):
        if h3.text(strip=True):
            meta["h3"].append(h3.text(strip=True))
    
    # Meta tags
    for tag in parser.css("meta"):
        name = tag.attributes.get("name", "").lower()
        prop = tag.attributes.get("property", "").lower()
        content = tag.attributes.get("content", "").strip()
        
        if not content:
            continue
        
        if name == "description":
            meta["description"] = content
        elif name == "keywords":
            meta["keywords"] = content
        elif name == "author":
            meta["author"] = content
        elif name == "language" or name == "lang":
            meta["language"] = content
        elif prop.startswith("og:"):
            meta["og"][prop[3:]] = content
        elif name.startswith("twitter:") or prop.startswith("twitter:"):
            key = name[8:] if name.startswith("twitter:") else prop[8:]
            meta["twitter"][key] = content
    
    # Canonical URL
    canonical = parser.css_first('link[rel="canonical"]')
    if canonical:
        meta["canonical"] = canonical.attributes.get("href")
    
    # Language from html tag
    html_tag = parser.css_first("html")
    if html_tag and not meta["language"]:
        meta["language"] = html_tag.attributes.get("lang")
    
    # JSON-LD structured data
    for script in parser.css('script[type="application/ld+json"]'):
        try:
            json_ld = json.loads(script.text())
            meta["json_ld"].append(json_ld)
        except Exception:
            pass
    
    return meta
