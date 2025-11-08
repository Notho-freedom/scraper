"""Playwright-based headless fetcher for JavaScript-heavy sites"""

import asyncio
import logging
import time
import hashlib
import gzip
from typing import Optional, Dict, List, Tuple
from collections import defaultdict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class PlaywrightFetcher:
    """Manages Playwright browser with advanced pooling and caching"""
    
    def __init__(self, pool_size: int = 5, cache_enabled: bool = True, cache_ttl: int = 3600):
        """
        Args:
            pool_size: Number of browser contexts to maintain in pool
            cache_enabled: Enable HTML caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: List[BrowserContext] = []
        self.pool_size = pool_size
        self._lock = asyncio.Lock()
        self._initialized = False
        self._context_semaphore = None
        
        # Caching system
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[bytes, float]] = {}  # url -> (compressed_html, timestamp)
        self._cache_lock = asyncio.Lock()
        
        # Performance monitoring
        self.metrics = {
            'total_fetches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'active_pages': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Initialize Playwright browser with context pool"""
        async with self._lock:
            if self._initialized:
                return
            
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
                        '--disable-software-rasterizer',
                    ]
                )
                
                # Create context pool
                for _ in range(self.pool_size):
                    context = await self.browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        ignore_https_errors=True,
                        java_script_enabled=True,
                    )
                    self.contexts.append(context)
                
                # Semaphore to control concurrent context usage
                self._context_semaphore = asyncio.Semaphore(self.pool_size)
                
                self._initialized = True
                logging.info(f"Playwright browser initialized with {self.pool_size} contexts")
                
            except Exception as e:
                logging.error(f"Failed to initialize Playwright: {e}")
                raise
    
    async def _check_cache(self, url: str) -> Optional[str]:
        """Check if URL is in cache and not expired"""
        if not self.cache_enabled:
            return None
        
        async with self._cache_lock:
            if url in self._cache:
                compressed_html, timestamp = self._cache[url]
                if time.time() - timestamp < self.cache_ttl:
                    self.metrics['cache_hits'] += 1
                    return gzip.decompress(compressed_html).decode('utf-8')
                else:
                    # Expired, remove from cache
                    del self._cache[url]
        
        self.metrics['cache_misses'] += 1
        return None
    
    async def _store_cache(self, url: str, html: str):
        """Store HTML in cache with compression"""
        if not self.cache_enabled:
            return
        
        async with self._cache_lock:
            compressed = gzip.compress(html.encode('utf-8'))
            self._cache[url] = (compressed, time.time())
    
    async def fetch(self, url: str, timeout: int = 15000, wait_for: str = 'domcontentloaded') -> Optional[str]:
        """
        Fetch URL with JavaScript rendering (cache-aware, pooled).
        
        Args:
            url: URL to fetch
            timeout: Timeout in milliseconds (default: 15000)
            wait_for: Wait strategy - 'domcontentloaded', 'load', or 'networkidle'
            
        Returns:
            HTML content or None on error
        """
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        cached = await self._check_cache(url)
        if cached:
            logging.debug(f"Cache hit for {url}")
            return cached
        
        # Acquire semaphore (limit concurrent pages)
        async with self._context_semaphore:
            start_time = time.time()
            page: Optional[Page] = None
            
            try:
                # Get context from pool (round-robin)
                context_idx = self.metrics['total_fetches'] % self.pool_size
                context = self.contexts[context_idx]
                
                page = await context.new_page()
                self.metrics['active_pages'] += 1
                
                # Disable animations for cleaner rendering
                await page.add_style_tag(content="""
                    * {
                        transition: none !important;
                        animation: none !important;
                        animation-duration: 0s !important;
                    }
                """)
                
                # Block unnecessary resources for performance
                await page.route("**/*", self._route_handler)
                
                # Navigate and wait
                await page.goto(url, timeout=timeout, wait_until=wait_for)
                
                # Adaptive wait based on page complexity
                await page.wait_for_timeout(500)  # Reduced from 1000ms
                
                # Wait for main content to be visible (if present)
                try:
                    await page.wait_for_selector("main, article, section, .content, [role='main']", timeout=3000)
                except Exception:
                    pass  # Continue if selector not found
                
                # Get rendered HTML
                html = await page.content()
                
                # Store in cache
                await self._store_cache(url, html)
                
                # Update metrics
                elapsed = time.time() - start_time
                self.metrics['total_fetches'] += 1
                self.metrics['total_time'] += elapsed
                self.metrics['avg_time'] = self.metrics['total_time'] / self.metrics['total_fetches']
                
                logging.info(f"Successfully fetched with Playwright: {url} ({elapsed:.2f}s)")
                return html
                
            except Exception as e:
                logging.error(f"Playwright fetch error for {url}: {e}")
                self.metrics['errors'] += 1
                return None
                
            finally:
                if page:
                    await page.close()
                    self.metrics['active_pages'] -= 1
    
    async def fetch_multiple(self, urls: List[str], timeout: int = 15000) -> Dict[str, Optional[str]]:
        """
        Fetch multiple URLs in parallel using context pool.
        
        Args:
            urls: List of URLs to fetch
            timeout: Timeout per URL in milliseconds
            
        Returns:
            Dictionary mapping URL to HTML content
        """
        if not self._initialized:
            await self.initialize()
        
        # Process URLs in batches matching pool size for optimal performance
        results = {}
        
        async def fetch_one(url: str):
            html = await self.fetch(url, timeout=timeout)
            return url, html
        
        # Execute in parallel batches
        tasks = [fetch_one(url) for url in urls]
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for item in completed:
            if isinstance(item, tuple):
                url, html = item
                results[url] = html
            elif isinstance(item, Exception):
                logging.error(f"Batch fetch error: {item}")
        
        return results
    
    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        cache_hit_rate = 0.0
        if self.metrics['total_fetches'] > 0:
            cache_hit_rate = self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses']) * 100
        
        return {
            **self.metrics,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cache_size': len(self._cache),
            'pool_size': self.pool_size
        }
    
    async def clear_cache(self):
        """Clear the HTML cache"""
        async with self._cache_lock:
            self._cache.clear()
            logging.info("Playwright cache cleared")
    
    @staticmethod
    async def _route_handler(route):
        """Block unnecessary resources to improve performance"""
        resource_type = route.request.resource_type
        
        # Block images, fonts, media, and other heavy resources
        if resource_type in ['image', 'font', 'media', 'stylesheet']:
            await route.abort()
        else:
            await route.continue_()
    
    async def close(self):
        """Clean up browser resources and display metrics"""
        async with self._lock:
            # Close all contexts in pool
            for context in self.contexts:
                try:
                    await context.close()
                except Exception as e:
                    logging.warning(f"Error closing context: {e}")
            
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self._initialized = False
            
            # Log final metrics
            metrics = self.get_metrics()
            logging.info(f"Playwright browser closed - Metrics: {metrics}")
    
    async def __aenter__(self):
        """Context manager support"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        await self.close()


# Global instance for reuse across requests
_global_fetcher: Optional[PlaywrightFetcher] = None
_fetcher_lock = asyncio.Lock()


async def get_fetcher(pool_size: int = 5, cache_enabled: bool = True, cache_ttl: int = 3600) -> PlaywrightFetcher:
    """Get or create global Playwright fetcher instance with configuration"""
    global _global_fetcher
    
    async with _fetcher_lock:
        if _global_fetcher is None:
            _global_fetcher = PlaywrightFetcher(
                pool_size=pool_size,
                cache_enabled=cache_enabled,
                cache_ttl=cache_ttl
            )
            await _global_fetcher.initialize()
        return _global_fetcher


async def fetch_with_js(url: str, timeout: int = 15000, pool_size: int = 5) -> Optional[str]:
    """
    Convenience function to fetch URL with JavaScript rendering.
    
    Args:
        url: URL to fetch
        timeout: Timeout in milliseconds
        pool_size: Browser context pool size
        
    Returns:
        Rendered HTML or None on error
    """
    fetcher = await get_fetcher(pool_size=pool_size)
    return await fetcher.fetch(url, timeout=timeout)


async def fetch_multiple_with_js(urls: List[str], timeout: int = 15000, pool_size: int = 5) -> Dict[str, Optional[str]]:
    """
    Fetch multiple URLs in parallel with JavaScript rendering.
    
    Args:
        urls: List of URLs to fetch
        timeout: Timeout per URL in milliseconds
        pool_size: Browser context pool size
        
    Returns:
        Dictionary mapping URL to HTML content
    """
    fetcher = await get_fetcher(pool_size=pool_size)
    return await fetcher.fetch_multiple(urls, timeout=timeout)


async def cleanup_fetcher():
    """Cleanup global fetcher (call on application shutdown)"""
    global _global_fetcher
    
    async with _fetcher_lock:
        if _global_fetcher:
            await _global_fetcher.close()
            _global_fetcher = None
