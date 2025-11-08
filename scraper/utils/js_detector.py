"""JavaScript detection utility"""

import re
from typing import Tuple


def needs_javascript(html: str, url: str = "") -> Tuple[bool, str]:
    """
    Detect if a page requires JavaScript to render content.
    
    Returns:
        Tuple of (needs_js: bool, reason: str)
    """
    html_lower = html.lower()
    
    # Common indicators that JS is required
    indicators = [
        # Explicit messages
        (r'please enable javascript', 'Explicit JS enable message'),
        (r'javascript is required', 'Explicit JS required message'),
        (r'javascript must be enabled', 'Explicit JS enable instruction'),
        (r'this site requires javascript', 'Explicit site requirement'),
        (r'enable javascript to continue', 'JS enable to continue message'),
        
        # Framework signatures with empty content
        (r'<div[^>]*id=["\']root["\'][^>]*>\s*</div>', 'React root div empty'),
        (r'<div[^>]*id=["\']app["\'][^>]*>\s*</div>', 'Vue app div empty'),
        (r'<noscript>', 'NoScript tag present'),
    ]
    
    for pattern, reason in indicators:
        if re.search(pattern, html_lower):
            return True, reason
    
    # Check if page is suspiciously empty
    # Remove common tags and whitespace
    clean_html = re.sub(r'<(script|style|link|meta|title)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean_html = re.sub(r'<[^>]+>', '', clean_html)
    clean_html = re.sub(r'\s+', ' ', clean_html).strip()
    
    # If very little text content, might be JS-rendered
    if len(clean_html) < 100:
        # But check if there are script tags (likely SPA)
        script_count = len(re.findall(r'<script[^>]*>', html, re.IGNORECASE))
        if script_count > 2:  # More than basic analytics
            return True, f'Very little content ({len(clean_html)} chars) but {script_count} scripts'
    
    # Check for common SPA frameworks
    spa_indicators = [
        r'__NEXT_DATA__',  # Next.js
        r'__NUXT__',       # Nuxt.js
        r'ng-version',     # Angular
        r'data-reactroot', # React
        r'data-vue-',      # Vue
    ]
    
    for indicator in spa_indicators:
        if re.search(indicator, html):
            # If SPA marker found but little content, likely needs rendering
            if len(clean_html) < 200:
                return True, f'SPA framework detected ({indicator}) with minimal content'
    
    return False, 'Sufficient static content'


def is_spa_url(url: str) -> bool:
    """
    Check if URL pattern suggests a Single Page Application.
    
    Args:
        url: The URL to check
        
    Returns:
        True if URL suggests SPA, False otherwise
    """
    spa_domains = [
        'vercel.app',
        'netlify.app',
        'herokuapp.com',
        'firebase.app',
        'web.app',
    ]
    
    return any(domain in url.lower() for domain in spa_domains)
