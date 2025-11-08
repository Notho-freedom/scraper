"""
Recursive Site Downloader - Downloads pages and resources recursively
Supports JavaScript-rendered sites using Playwright
"""

import os
import logging
import hashlib
import asyncio
from pathlib import Path
from typing import Set, Dict, Optional, List
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RecursiveDownloader:
    """Downloads website pages and resources recursively with JavaScript support"""
    
    def __init__(self, base_url: str, output_dir: str = "output/downloaded_site", 
                 max_depth: int = 10, max_pages: int = 100, timeout: int = 15,
                 use_playwright: bool = True):
        """
        Initialize recursive downloader
        
        Args:
            base_url: Starting URL to download
            output_dir: Directory to save downloaded files
            max_depth: Maximum recursion depth
            max_pages: Maximum number of pages to download
            timeout: Request timeout in seconds
            use_playwright: Use Playwright for JavaScript rendering (default: True)
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.use_playwright = use_playwright
        
        # Parse base URL
        parsed = urlparse(base_url)
        self.domain = parsed.netloc
        self.scheme = parsed.scheme
        
        # Tracking
        self.visited_urls: Set[str] = set()
        self.downloaded_files: Dict[str, str] = {}  # URL -> local path
        self.pages_downloaded: List[Dict] = []  # Order of page downloads
        
        # Playwright browser instance (lazy init)
        self.browser = None
        self.playwright = None
        
        # Create output directories
        self.pages_dir = self.output_dir / "pages"
        self.assets_dir = self.output_dir / "assets"
        self.css_dir = self.assets_dir / "css"
        self.js_dir = self.assets_dir / "js"
        self.images_dir = self.assets_dir / "images"
        
        for directory in [self.pages_dir, self.css_dir, self.js_dir, self.images_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Setup session with retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logging.info(f"RecursiveDownloader initialized for {base_url}")
        logging.info(f"Output: {self.output_dir}, Max depth: {max_depth}, Max pages: {max_pages}")
    
    async def _init_browser(self):
        """Initialize Playwright browser (lazy initialization)"""
        if not self.playwright:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            logging.info("Playwright browser initialized")
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes"""
        parsed = urlparse(url)
        # Remove fragment
        normalized = urlunparse(parsed._replace(fragment=''))
        # Remove trailing slash for consistency
        if normalized.endswith('/') and normalized != f"{self.scheme}://{self.domain}/":
            normalized = normalized[:-1]
        return normalized
    
    def is_internal_link(self, url: str) -> bool:
        """Check if URL is internal (same domain)"""
        parsed = urlparse(url)
        return parsed.netloc == self.domain or parsed.netloc == ''
    
    def get_local_path(self, url: str, resource_type: str = 'page') -> Path:
        """Generate local file path for a URL"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Generate filename from URL
        if not path or path.endswith('/'):
            filename = 'index.html'
        else:
            filename = os.path.basename(path) or 'index.html'
        
        # Ensure HTML extension for pages
        if resource_type == 'page' and not filename.endswith('.html'):
            filename += '.html'
        
        # Create safe filename (hash long paths)
        if len(path) > 100:
            path_hash = hashlib.md5(path.encode()).hexdigest()[:8]
            filename = f"{path_hash}_{filename}"
        
        # Determine directory based on resource type
        if resource_type == 'page':
            base_dir = self.pages_dir
        elif resource_type == 'css':
            base_dir = self.css_dir
        elif resource_type == 'js':
            base_dir = self.js_dir
        elif resource_type == 'image':
            base_dir = self.images_dir
        else:
            base_dir = self.assets_dir
        
        return base_dir / filename
    
    def download_resource(self, url: str, resource_type: str = 'page') -> Optional[str]:
        """
        Download a resource (page, CSS, JS, image)
        
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Normalize URL
            url = self.normalize_url(url)
            
            # Check if already downloaded
            if url in self.downloaded_files:
                logging.debug(f"Cache hit: {url}")
                return self.downloaded_files[url]
            
            # Download
            logging.info(f"Downloading {resource_type}: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Get local path
            local_path = self.get_local_path(url, resource_type)
            
            # Save file
            if resource_type in ['css', 'js', 'page']:
                # Text files - save as UTF-8
                local_path.write_text(response.text, encoding='utf-8')
            else:
                # Binary files (images, etc.)
                local_path.write_bytes(response.content)
            
            # Cache mapping
            self.downloaded_files[url] = str(local_path)
            logging.info(f"Saved to: {local_path}")
            
            return str(local_path)
            
        except Exception as e:
            logging.error(f"Failed to download {url}: {e}")
            return None
    
    def download_page_resources(self, html: str, page_url: str) -> str:
        """
        Download all resources referenced in HTML and rewrite URLs to local paths
        
        Args:
            html: HTML content
            page_url: URL of the page (for resolving relative URLs)
            
        Returns:
            Modified HTML with local resource paths
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Download and rewrite CSS
        for tag in soup.find_all('link', href=True):
            if tag.get('rel') and 'stylesheet' in tag.get('rel'):
                css_url = urljoin(page_url, tag['href'])
                if self.is_internal_link(css_url):
                    local_path = self.download_resource(css_url, 'css')
                    if local_path:
                        # Rewrite to relative path from pages directory
                        relative_path = os.path.relpath(local_path, self.pages_dir)
                        tag['href'] = relative_path.replace('\\', '/')
        
        # Download and rewrite JS
        for tag in soup.find_all('script', src=True):
            js_url = urljoin(page_url, tag['src'])
            if self.is_internal_link(js_url):
                local_path = self.download_resource(js_url, 'js')
                if local_path:
                    relative_path = os.path.relpath(local_path, self.pages_dir)
                    tag['src'] = relative_path.replace('\\', '/')
        
        # Download and rewrite images
        for tag in soup.find_all('img', src=True):
            img_url = urljoin(page_url, tag['src'])
            if self.is_internal_link(img_url):
                local_path = self.download_resource(img_url, 'image')
                if local_path:
                    relative_path = os.path.relpath(local_path, self.pages_dir)
                    tag['src'] = relative_path.replace('\\', '/')
        
        # Handle srcset for responsive images
        for tag in soup.find_all('img', srcset=True):
            srcset_parts = []
            for part in tag['srcset'].split(','):
                part = part.strip()
                if ' ' in part:
                    url, descriptor = part.rsplit(' ', 1)
                    img_url = urljoin(page_url, url.strip())
                    if self.is_internal_link(img_url):
                        local_path = self.download_resource(img_url, 'image')
                        if local_path:
                            relative_path = os.path.relpath(local_path, self.pages_dir)
                            srcset_parts.append(f"{relative_path.replace(chr(92), '/')} {descriptor}")
                        else:
                            srcset_parts.append(part)
                    else:
                        srcset_parts.append(part)
                else:
                    srcset_parts.append(part)
            if srcset_parts:
                tag['srcset'] = ', '.join(srcset_parts)
        
        return str(soup)
    
    def extract_internal_links(self, html: str, page_url: str) -> List[str]:
        """Extract all internal links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            
            # Skip anchors and special protocols
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Resolve relative URL
            absolute_url = urljoin(page_url, href)
            
            # Check if internal
            if self.is_internal_link(absolute_url):
                normalized = self.normalize_url(absolute_url)
                links.append(normalized)
        
        return links
    
    def download_page(self, url: str, depth: int = 0) -> bool:
        """
        Recursively download a page and all linked internal pages
        
        Args:
            url: URL to download
            depth: Current recursion depth
            
        Returns:
            True if successful, False otherwise
        """
        # Normalize URL
        url = self.normalize_url(url)
        
        # Check limits
        if depth > self.max_depth:
            logging.info(f"Max depth reached for {url}")
            return False
        
        if len(self.visited_urls) >= self.max_pages:
            logging.info(f"Max pages reached ({self.max_pages})")
            return False
        
        if url in self.visited_urls:
            logging.debug(f"Already visited: {url}")
            return False
        
        # Mark as visited
        self.visited_urls.add(url)
        
        try:
            # Download page
            logging.info(f"[Depth {depth}] Downloading page: {url}")
            
            # Use Playwright for JavaScript rendering if enabled
            if self.use_playwright:
                # Get or create event loop for this thread
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                html = loop.run_until_complete(self._download_page_with_playwright(url))
            else:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                html = response.text
            
            # Download resources and rewrite URLs
            html_with_local_resources = self.download_page_resources(html, url)
            
            # Save page
            local_path = self.get_local_path(url, 'page')
            local_path.write_text(html_with_local_resources, encoding='utf-8')
            self.downloaded_files[url] = str(local_path)
            
            # Track download order
            self.pages_downloaded.append({
                'url': url,
                'local_path': str(local_path),
                'depth': depth
            })
            
            logging.info(f"Page saved to: {local_path}")
            
            # Extract internal links
            internal_links = self.extract_internal_links(html, url)
            logging.info(f"Found {len(internal_links)} internal links")
            
            # Recursively download linked pages
            for link in internal_links:
                if len(self.visited_urls) >= self.max_pages:
                    break
                self.download_page(link, depth + 1)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to download page {url}: {e}")
            return False
    
    async def _download_page_with_playwright(self, url: str) -> str:
        """
        Download page content using Playwright for JavaScript rendering
        
        Args:
            url: URL to download
            
        Returns:
            Rendered HTML content
        """
        # Initialize browser if needed
        await self._init_browser()
        
        # Create new page
        page = await self.browser.new_page()
        
        try:
            # Navigate and wait for load (use longer timeout for JavaScript sites)
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait a bit more for dynamic content to load
            await page.wait_for_timeout(2000)
            
            # Get rendered HTML
            html = await page.content()
            
            logging.info(f"Page rendered with Playwright: {url}")
            return html
            
        finally:
            await page.close()
    
    def get_summary(self) -> Dict:
        """Get download summary statistics"""
        return {
            'pages_downloaded': len(self.pages_downloaded),
            'total_files': len(self.downloaded_files),
            'visited_urls': len(self.visited_urls),
            'output_directory': str(self.output_dir),
            'pages_list': self.pages_downloaded
        }
    
    def cleanup(self):
        """Cleanup resources"""
        # Close requests session
        self.session.close()
        
        # Close Playwright browser if initialized
        if self.browser or self.playwright:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self._cleanup_browser())
        
        logging.info("RecursiveDownloader cleanup complete")
    
    async def _cleanup_browser(self):
        """Async cleanup for Playwright browser"""
        try:
            if self.browser:
                await self.browser.close()
                logging.info("Playwright browser closed")
            if self.playwright:
                await self.playwright.stop()
                logging.info("Playwright stopped")
        except Exception as e:
            logging.error(f"Error during browser cleanup: {e}")
