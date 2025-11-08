"""Playwright-based headless fetcher for JavaScript-heavy sites"""

import asyncio
import logging
from typing import Optional, Dict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class PlaywrightFetcher:
    """Manages Playwright browser instances for JavaScript rendering"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize Playwright and browser (lazy initialization)"""
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
                    ]
                )
                
                # Create a persistent context with optimizations
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                self._initialized = True
                logging.info("Playwright browser initialized")
                
            except Exception as e:
                logging.error(f"Failed to initialize Playwright: {e}")
                raise
    
    async def fetch(self, url: str, timeout: int = 30000, wait_for: str = 'domcontentloaded') -> Optional[str]:
        """
        Fetch URL with JavaScript rendering.
        
        Args:
            url: URL to fetch
            timeout: Timeout in milliseconds (default: 30000)
            wait_for: Wait strategy - 'domcontentloaded', 'load', or 'networkidle'
            
        Returns:
            HTML content or None on error
        """
        if not self._initialized:
            await self.initialize()
        
        page: Optional[Page] = None
        try:
            page = await self.context.new_page()
            
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
            
            # Additional wait for dynamic content
            await page.wait_for_timeout(1000)
            
            # Wait for main content to be visible (if present)
            try:
                await page.wait_for_selector("main, article, section, .content", timeout=5000)
            except Exception:
                pass  # Continue if selector not found
            
            # Get rendered HTML
            html = await page.content()
            
            logging.info(f"Successfully fetched with Playwright: {url}")
            return html
            
        except Exception as e:
            logging.error(f"Playwright fetch error for {url}: {e}")
            return None
            
        finally:
            if page:
                await page.close()
    
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
        """Clean up browser resources"""
        async with self._lock:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self._initialized = False
            logging.info("Playwright browser closed")
    
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


async def get_fetcher() -> PlaywrightFetcher:
    """Get or create global Playwright fetcher instance"""
    global _global_fetcher
    
    async with _fetcher_lock:
        if _global_fetcher is None:
            _global_fetcher = PlaywrightFetcher()
            await _global_fetcher.initialize()
        return _global_fetcher


async def fetch_with_js(url: str, timeout: int = 30000) -> Optional[str]:
    """
    Convenience function to fetch URL with JavaScript rendering.
    
    Args:
        url: URL to fetch
        timeout: Timeout in milliseconds
        
    Returns:
        Rendered HTML or None on error
    """
    fetcher = await get_fetcher()
    return await fetcher.fetch(url, timeout=timeout)


async def cleanup_fetcher():
    """Cleanup global fetcher (call on application shutdown)"""
    global _global_fetcher
    
    async with _fetcher_lock:
        if _global_fetcher:
            await _global_fetcher.close()
            _global_fetcher = None
