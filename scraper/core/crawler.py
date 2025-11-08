"""Main crawler implementation"""

import asyncio
import aiohttp
import logging
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional

from .config import Config
from .state import CrawlerState
from ..extractors import extract_metadata, extract_text, extract_links, extract_resources
from ..utils import compute_content_hash, can_fetch, needs_javascript, is_spa_url, fetch_with_js, get_fetcher


class Crawler:
    """Main crawler class with optimized Playwright pooling"""
    
    def __init__(self, config: Config, state: CrawlerState):
        self.config = config
        self.state = state
        self._playwright_fetcher = None
    
    async def _get_playwright_fetcher(self):
        """Get or initialize Playwright fetcher with config settings"""
        if self._playwright_fetcher is None:
            self._playwright_fetcher = await get_fetcher(
                pool_size=self.config.playwright_pool_size,
                cache_enabled=self.config.playwright_cache_enabled,
                cache_ttl=self.config.playwright_cache_ttl
            )
        return self._playwright_fetcher
    
    async def fetch(self, session, url: str) -> Optional[tuple]:
        """Fetch URL with retry logic, metrics, and JS fallback"""
        import time
        
        # Try standard HTTP fetch first
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                async with session.get(url, timeout=self.config.timeout) as response:
                    elapsed = time.time() - start_time
                    self.state.add_response_time(elapsed)
                    self.state.stats["status_codes"][response.status] += 1
                    
                    content_type = response.headers.get("content-type", "")
                    self.state.stats["content_types"][content_type.split(';')[0]] += 1
                    
                    if response.status == 200 and "text/html" in content_type:
                        html = await response.text()
                        
                        # Check if page needs JavaScript rendering
                        js_needed, reason = needs_javascript(html, url)
                        
                        if js_needed or is_spa_url(url):
                            logging.info(f"JS rendering needed for {url}: {reason}")
                            
                            # Fallback to Playwright with optimized pooling
                            try:
                                start_js = time.time()
                                fetcher = await self._get_playwright_fetcher()
                                js_html = await fetcher.fetch(
                                    url, 
                                    timeout=self.config.playwright_timeout
                                )
                                elapsed_js = time.time() - start_js
                                
                                if js_html:
                                    logging.info(f"Successfully rendered with Playwright: {url} ({elapsed_js:.2f}s)")
                                    self.state.add_response_time(elapsed_js)
                                    return js_html, elapsed_js
                                else:
                                    logging.warning(f"Playwright rendering failed for {url}, using static HTML")
                                    return html, elapsed
                                    
                            except Exception as e:
                                logging.error(f"Playwright error for {url}: {e}, falling back to static HTML")
                                return html, elapsed
                        
                        return html, elapsed
                    else:
                        logging.warning(f"Non-200 or non-HTML response for {url}: {response.status}")
                        return None, elapsed
                        
            except asyncio.TimeoutError:
                logging.warning(f"Timeout on {url} (attempt {attempt + 1}/{self.config.retry_attempts})")
                if attempt == self.config.retry_attempts - 1:
                    self.state.add_error({
                        "url": url, 
                        "error": "timeout", 
                        "time": datetime.now().isoformat()
                    })
            except Exception as e:
                logging.error(f"Error fetching {url}: {str(e)}")
                if attempt == self.config.retry_attempts - 1:
                    self.state.add_error({
                        "url": url, 
                        "error": str(e), 
                        "time": datetime.now().isoformat()
                    })
            
            await asyncio.sleep(self.config.rate_limit * (attempt + 1))
        
        self.state.increment_stat("errors")
        return None, 0
    
    async def crawl(self, url: str, session, depth: int = 0, sem=None, pbar=None):
        """Main recursive crawling function"""
        
        # Check limits
        if (self.state.is_visited(url) or 
            depth > self.config.max_depth or 
            len(self.state.visited) >= self.config.max_pages):
            return
        
        async with sem:
            # Check robots.txt
            if self.config.respect_robots:
                if not await can_fetch(session, url, self.state, self.config.user_agent):
                    logging.info(f"Blocked by robots.txt: {url}")
                    return
            
            self.state.add_visited(url)
            
            # Fetch page
            result = await self.fetch(session, url)
            if not result or not result[0]:
                return
            
            html, response_time = result
            
            # Extract all data
            metadata = extract_metadata(html)
            text_data = extract_text(
                html, 
                enable_nlp=self.config.enable_nlp,
                nlp_config={
                    'language': self.config.nlp_language,
                    'use_spacy': self.config.nlp_use_spacy
                },
                enable_correction=self.config.enable_correction
            )
            resources = extract_resources(html, url)
            link_data = extract_links(html, url)
            
            # Duplicate detection
            content_hash = compute_content_hash(" ".join(text_data["sentences"]))
            is_duplicate = False
            if self.config.detect_duplicates:
                if content_hash in self.state.content_hashes:
                    is_duplicate = True
                    self.state.mark_duplicate(content_hash, url)
                    logging.info(f"Duplicate content detected: {url}")
                else:
                    self.state.content_hashes[content_hash] = url
            
            # Update stats
            self.state.increment_stat("pages")
            self.state.increment_stat("words", text_data["word_count"])
            self.state.increment_stat("images", len(resources["images"]))
            self.state.increment_stat("scripts", len(resources["scripts"]))
            self.state.stats["depths"].setdefault(depth, 0)
            self.state.stats["depths"][depth] += 1
            
            # Store result with HTML snapshot for reconstruction
            page_result = {
                "url": url,
                "depth": depth,
                "timestamp": datetime.now().isoformat(),
                "response_time": round(response_time, 3),
                "is_duplicate": is_duplicate,
                "content_hash": content_hash,
                "html_snapshot": html,  # Store original HTML for reconstruction
                "metadata": metadata,
                "text": text_data,
                "resources": resources,
                "links": {
                    "internal_count": len(link_data["internal"]),
                    "external_count": len(link_data["external"]),
                    "external_domains": list(set(urlparse(u).netloc for u in link_data["external"]))[:20]
                }
            }
            
            self.state.add_result(page_result)
            
            # Update progress bar
            if pbar:
                pbar.update(1)
                from colorama import Fore, Style
                path = urlparse(url).path[:50] or "/"
                pbar.set_description(f"{Fore.CYAN}{path:<50}{Style.RESET_ALL}")
            
            # Rate limiting
            await asyncio.sleep(self.config.rate_limit)
            
            # Crawl child links
            if depth < self.config.max_depth:
                tasks = []
                for link in link_data["internal"]:
                    if not self.state.is_visited(link) and len(self.state.visited) < self.config.max_pages:
                        task = asyncio.create_task(
                            self.crawl(link, session, depth + 1, sem, pbar)
                        )
                        tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
