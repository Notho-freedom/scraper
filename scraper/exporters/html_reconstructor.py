"""HTML Reconstruction Module - Injects corrections into original HTML"""

import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin, urlparse


class HTMLReconstructor:
    """Reconstructs original HTML with correction annotations"""
    
    # Styles for correction annotations
    DEL_STYLE = "text-decoration: line-through; color: #dc3545; background-color: #f8d7da;"
    INS_STYLE = "color: #28a745; background-color: #d4edda; font-weight: 500;"
    
    def __init__(self):
        """Initialize HTML reconstructor"""
        pass
    
    def fix_relative_urls(self, html: str, base_url: str) -> str:
        """
        Convert all relative URLs to absolute URLs in HTML.
        
        Args:
            html: HTML content with relative URLs
            base_url: Base URL of the website (e.g., https://example.com)
            
        Returns:
            HTML with absolute URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Fix href attributes (links, stylesheets)
        for tag in soup.find_all(href=True):
            original_url = tag['href']
            # Skip if already absolute or anchor/javascript
            if not original_url.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                tag['href'] = urljoin(base_url, original_url)
        
        # Fix src attributes (images, scripts)
        for tag in soup.find_all(src=True):
            original_url = tag['src']
            if not original_url.startswith(('data:', 'javascript:')):
                tag['src'] = urljoin(base_url, original_url)
        
        # Fix srcset attributes (responsive images)
        for tag in soup.find_all(srcset=True):
            srcset_parts = []
            for part in tag['srcset'].split(','):
                part = part.strip()
                if ' ' in part:
                    url, descriptor = part.rsplit(' ', 1)
                    url = urljoin(base_url, url.strip())
                    srcset_parts.append(f"{url} {descriptor}")
                else:
                    url = urljoin(base_url, part)
                    srcset_parts.append(url)
            tag['srcset'] = ', '.join(srcset_parts)
        
        # Helper function to replace URLs in CSS
        def replace_css_url(match):
            url = match.group(1).strip('\'"')
            if not url.startswith(('data:', 'http://', 'https://', '#')):
                url = urljoin(base_url, url)
            return f'url("{url}")'
        
        # Fix inline style attributes
        for tag in soup.find_all(style=True):
            style = tag['style']
            tag['style'] = re.sub(r'url\(["\']?([^"\'()]+)["\']?\)', replace_css_url, style)
        
        # Fix <style> tags
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                style_tag.string = re.sub(r'url\(["\']?([^"\'()]+)["\']?\)', replace_css_url, style_tag.string)
        
        return str(soup)
    
    def reconstruct_with_corrections(self, html: str, corrections_data: Dict) -> str:
        """
        Inject corrections into original HTML.
        
        Args:
            html: Original HTML content
            corrections_data: Correction data from text analysis
            
        Returns:
            HTML with <del> and <ins> tags for corrections
        """
        if not corrections_data or not corrections_data.get('corrected_paragraphs'):
            return html
        
        soup = BeautifulSoup(html, 'html.parser')
        corrected_paragraphs = corrections_data['corrected_paragraphs']
        
        # Map corrections by original text for matching
        correction_map = {}
        for para_data in corrected_paragraphs:
            original = para_data['original_text']
            corrected = para_data['corrected_text']
            corrections = para_data.get('corrections', [])
            
            if original != corrected and corrections:
                correction_map[original] = {
                    'corrected': corrected,
                    'corrections': corrections
                }
        
        # Find and annotate text elements
        text_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'span', 'div', 'a']
        
        for tag in text_tags:
            elements = soup.find_all(tag)
            for elem in elements:
                self._annotate_element(elem, correction_map)
        
        # Return modified HTML
        return str(soup)
    
    def _annotate_element(self, element, correction_map: Dict):
        """
        Annotate a single HTML element with corrections.
        
        Args:
            element: BeautifulSoup element node
            correction_map: Map of original text to corrections
        """
        if not element or not element.get_text(strip=True):
            return
        
        element_text = element.get_text(strip=True, separator=' ')
        
        # Check if this element's text matches any original text with corrections
        for original_text, corr_data in correction_map.items():
            # Fuzzy match (handle minor whitespace differences)
            if self._text_matches(element_text, original_text):
                # Apply corrections
                new_html = self._apply_corrections_html(
                    original_text,
                    corr_data['corrections']
                )
                
                # Replace element's inner HTML with annotated version
                try:
                    element['data-corrected'] = 'true'
                    
                    logging.debug(f"New HTML before parsing: {new_html}")
                    
                    # Parse new HTML fragment and replace element contents
                    # Wrap in a container to preserve structure
                    wrapped = f"<span>{new_html}</span>"
                    fragment = BeautifulSoup(wrapped, 'html.parser').span
                    
                    element.clear()
                    # Extract all children from the wrapper
                    for child in list(fragment.children):
                        element.append(child)
                    
                    logging.debug(f"Applied corrections to {element.name} element")
                except Exception as e:
                    logging.debug(f"Could not annotate element: {e}")
                
                break
    
    def _text_matches(self, text1: str, text2: str) -> bool:
        """Check if two texts match (with normalization)"""
        # Normalize whitespace
        t1 = re.sub(r'\s+', ' ', text1.strip().lower())
        t2 = re.sub(r'\s+', ' ', text2.strip().lower())
        return t1 == t2
    
    def _apply_corrections_html(self, original: str, corrections: List[Dict]) -> str:
        """
        Apply correction annotations to text using word replacement.
        
        Args:
            original: Original text
            corrections: List of individual corrections
            
        Returns:
            HTML with <del> and <ins> tags
        """
        result = original
        
        # Apply corrections by replacing each original word with annotated version
        for corr in corrections:
            original_word = corr['original']
            corrected_word = corr['corrected']
            
            logging.debug(f"Applying correction: '{original_word}' -> '{corrected_word}' in text: '{result}'")
            
            # Build annotated replacement
            annotated = (
                f'<del style="{self.DEL_STYLE}">{original_word}</del>'
                f'<ins style="{self.INS_STYLE}">{corrected_word}</ins>'
            )
            
            # Replace first occurrence (word boundary aware)
            # Use regex to match whole word only
            pattern = r'\b' + re.escape(original_word) + r'\b'
            new_result = re.sub(pattern, annotated, result, count=1, flags=re.IGNORECASE)
            
            if new_result == result:
                logging.warning(f"Could not find word '{original_word}' in text")
            else:
                logging.debug(f"Successfully replaced '{original_word}'")
                result = new_result
        
        return result
    
    def _apply_corrections(self, original: str, corrected: str, corrections: List[Dict]) -> str:
        """
        Apply correction annotations to text.
        
        Args:
            original: Original text
            corrected: Fully corrected text
            corrections: List of individual corrections
            
        Returns:
            HTML with <del> and <ins> tags
        """
        # Sort corrections by position (reverse order to avoid offset issues)
        sorted_corrections = sorted(corrections, key=lambda c: c['position'], reverse=True)
        
        result = original
        
        for corr in sorted_corrections:
            pos = corr['position']
            length = corr['length']
            original_word = corr['original']
            corrected_word = corr['corrected']
            
            # Build annotated replacement
            annotated = (
                f'<del style="{self.DEL_STYLE}">{original_word}</del>'
                f'<ins style="{self.INS_STYLE}">{corrected_word}</ins>'
            )
            
            # Replace in text
            try:
                # Find the word at position
                before = result[:pos]
                after = result[pos + length:]
                result = before + annotated + after
            except Exception as e:
                logging.warning(f"Could not apply correction at position {pos}: {e}")
        
        return result
    
    def add_correction_legend(self, html: str) -> str:
        """
        Add a legend explaining correction colors at the top of the page.
        
        Args:
            html: HTML content
            
        Returns:
            HTML with legend prepended
        """
        legend_html = f"""
        <div style="position: sticky; top: 0; background: #fff; border: 2px solid #ddd; padding: 15px; margin: 20px; border-radius: 8px; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin-top: 0; color: #333;">📝 Légende des corrections</h3>
            <p style="margin: 10px 0;">
                <del style="{self.DEL_STYLE} padding: 2px 4px; border-radius: 3px;">Texte incorrect</del>
                <ins style="{self.INS_STYLE} padding: 2px 4px; border-radius: 3px; margin-left: 5px;">Texte corrigé</ins>
            </p>
            <p style="margin: 10px 0; font-size: 14px; color: #666;">
                Les corrections sont affichées directement dans le contenu original du site.
                Le texte <span style="color: #dc3545;">barré en rouge</span> représente l'erreur détectée,
                et le texte <span style="color: #28a745;">en vert</span> est la correction suggérée.
            </p>
        </div>
        """
        
        # Insert legend after <body> tag
        if '<body' in html:
            html = re.sub(
                r'(<body[^>]*>)',
                r'\1' + legend_html,
                html,
                count=1,
                flags=re.IGNORECASE
            )
        else:
            # If no body tag, prepend to content
            html = legend_html + html
        
        return html
    
    def save_snapshot(self, html: str, url: str, output_dir: str, version: str = "v1", fix_urls: bool = True) -> str:
        """
        Save HTML snapshot to file.
        
        Args:
            html: HTML content
            url: Page URL (used for filename and as base URL for fixing)
            output_dir: Output directory
            version: Version identifier (v1, v2_corrected, etc.)
            fix_urls: Convert relative URLs to absolute (default: True)
            
        Returns:
            Path to saved file
        """
        from urllib.parse import urlparse
        import os
        
        # Fix relative URLs if requested
        if fix_urls:
            # Extract base URL from full URL
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            logging.info(f"Converting relative URLs to absolute using base: {base_url}")
            html = self.fix_relative_urls(html, base_url)
        
        parsed = urlparse(url)
        safe_name = parsed.path.strip('/').replace('/', '_') or 'index'
        filename = f"{output_dir}/snapshot_{safe_name}_{version}.html"
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logging.info(f"Saved HTML snapshot: {filename}")
        return filename


def reconstruct_page_with_corrections(page_data: Dict, include_legend: bool = True, fix_urls: bool = True) -> str:
    """
    Convenience function to reconstruct a page with corrections.
    
    Args:
        page_data: Page data dict with 'html_snapshot', 'text', and 'url' fields
        include_legend: Add correction legend to the page
        fix_urls: Convert relative URLs to absolute for local viewing
        
    Returns:
        Reconstructed HTML with corrections
    """
    reconstructor = HTMLReconstructor()
    
    # Get original HTML
    html = page_data.get('html_snapshot', '')
    if not html:
        logging.warning(f"No HTML snapshot for {page_data.get('url', 'unknown')}")
        return ""
    
    # Fix URLs if requested
    if fix_urls:
        url = page_data.get('url', '')
        if url:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            html = reconstructor.fix_relative_urls(html, base_url)
    
    # Get corrections
    text_data = page_data.get('text', {})
    corrections = text_data.get('corrections', {})
    
    if not corrections or not corrections.get('corrected_paragraphs'):
        logging.info(f"No corrections for {page_data.get('url', 'unknown')}, returning original")
        return html
    
    # Reconstruct with corrections
    reconstructed = reconstructor.reconstruct_with_corrections(html, corrections)
    
    # Add legend if requested
    if include_legend:
        reconstructed = reconstructor.add_correction_legend(reconstructed)
    
    return reconstructed
