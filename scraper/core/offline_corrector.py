"""
Offline Corrector - Corrects downloaded HTML pages with grammar fixes
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from scraper.utils.grammar_checker import GrammarChecker
from scraper.utils.text_corrector import TextCorrector
from scraper.exporters.html_reconstructor import HTMLReconstructor


class OfflineCorrector:
    """Corrects grammar/spelling in downloaded HTML pages"""
    
    def __init__(self, pages_dir: str, output_dir: str = "output/corrected_pages",
                 language: str = "fr", aggressive: bool = True):
        """
        Initialize offline corrector
        
        Args:
            pages_dir: Directory containing downloaded HTML pages
            output_dir: Directory to save corrected pages
            language: Language for correction (fr, en)
            aggressive: Use aggressive correction mode
        """
        self.pages_dir = Path(pages_dir)
        self.output_dir = Path(output_dir)
        self.language = language
        self.aggressive = aggressive
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize correction tools (singleton pattern)
        self.grammar_checker = GrammarChecker.get_instance(language=language)
        self.text_corrector = TextCorrector.get_instance(language=language)
        self.reconstructor = HTMLReconstructor()
        
        # Tracking
        self.corrected_pages: List[Dict] = []
        self.total_errors = 0
        self.total_corrections = 0
        
        logging.info(f"OfflineCorrector initialized")
        logging.info(f"Pages: {self.pages_dir}, Output: {self.output_dir}")
        logging.info(f"Language: {language}, Aggressive: {aggressive}")
    
    def extract_text_from_html(self, html_path: Path) -> str:
        """Extract text content from HTML file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style tags
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            return text
            
        except Exception as e:
            logging.error(f"Failed to extract text from {html_path}: {e}")
            return ""
    
    def correct_page(self, html_path: Path) -> Optional[str]:
        """
        Correct a single HTML page
        
        Args:
            html_path: Path to HTML file
            
        Returns:
            Path to corrected HTML file, or None if failed
        """
        try:
            logging.info(f"Correcting page: {html_path.name}")
            
            # Read HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            # Extract text for analysis
            text = self.extract_text_from_html(html_path)
            
            if not text:
                logging.warning(f"No text extracted from {html_path.name}")
                return None
            
            # Check grammar
            check_result = self.grammar_checker.check_text(text)
            errors = check_result.errors if hasattr(check_result, 'errors') else []
            self.total_errors += len(errors)
            
            logging.info(f"  Found {len(errors)} errors")
            
            if not errors:
                # No errors, copy original to output
                output_path = self.output_dir / html_path.name
                output_path.write_text(html, encoding='utf-8')
                return str(output_path)
            
            # Apply corrections
            correction_result = self.text_corrector.correct_text(
                text, 
                aggressive=self.aggressive
            )
            
            # Extract corrected text and corrections list from result
            corrected_text = correction_result.corrected_text if hasattr(correction_result, 'corrected_text') else text
            corrections = correction_result.corrections if hasattr(correction_result, 'corrections') else []
            
            self.total_corrections += len(corrections)
            
            logging.info(f"  Applied {len(corrections)} corrections")
            
            # Prepare corrections data for HTML reconstruction
            # Convert Correction objects to dict format expected by HTMLReconstructor
            corrections_list = []
            for corr in corrections:
                corrections_list.append({
                    'original_text': corr.original,
                    'corrected_text': corr.corrected,
                    'position': corr.position,
                    'length': corr.length,
                    'confidence': corr.confidence
                })
            
            corrections_data = {
                'corrected_paragraphs': [{
                    'original_text': text,
                    'corrected_text': corrected_text,
                    'corrections': corrections_list
                }]
            }
            
            # Inject corrections into HTML
            reconstructed_html = self.reconstructor.reconstruct_with_corrections(
                html, 
                corrections_data
            )
            
            # Add correction legend
            reconstructed_html = self.reconstructor.add_correction_legend(reconstructed_html)
            
            # Save corrected HTML
            output_path = self.output_dir / html_path.name
            output_path.write_text(reconstructed_html, encoding='utf-8')
            
            # Track correction
            self.corrected_pages.append({
                'original_path': str(html_path),
                'corrected_path': str(output_path),
                'errors_found': len(errors),
                'corrections_applied': len(corrections)
            })
            
            logging.info(f"  Saved corrected page to: {output_path.name}")
            
            return str(output_path)
            
        except Exception as e:
            logging.error(f"Failed to correct {html_path}: {e}")
            return None
    
    def correct_all_pages(self, pages_list: Optional[List[Dict]] = None) -> Dict:
        """
        Correct all pages in the directory
        
        Args:
            pages_list: Optional list of page dicts with 'local_path' keys
                       If None, scans pages_dir for all .html files
        
        Returns:
            Summary statistics
        """
        logging.info("Starting batch correction of all pages")
        
        # Get list of HTML files to correct
        if pages_list:
            html_files = [Path(page['local_path']) for page in pages_list]
        else:
            html_files = list(self.pages_dir.glob('*.html'))
        
        logging.info(f"Found {len(html_files)} HTML files to correct")
        
        # Correct each page
        success_count = 0
        for html_file in html_files:
            if self.correct_page(html_file):
                success_count += 1
        
        # Summary
        summary = {
            'total_pages': len(html_files),
            'corrected_successfully': success_count,
            'total_errors_found': self.total_errors,
            'total_corrections_applied': self.total_corrections,
            'output_directory': str(self.output_dir),
            'corrected_pages': self.corrected_pages
        }
        
        logging.info("="*70)
        logging.info("CORRECTION SUMMARY")
        logging.info("="*70)
        logging.info(f"Total pages processed: {summary['total_pages']}")
        logging.info(f"Successfully corrected: {summary['corrected_successfully']}")
        logging.info(f"Total errors found: {summary['total_errors_found']}")
        logging.info(f"Total corrections applied: {summary['total_corrections_applied']}")
        logging.info(f"Output directory: {summary['output_directory']}")
        logging.info("="*70)
        
        return summary
    
    def cleanup(self):
        """Cleanup resources"""
        # Singleton cleanup
        GrammarChecker.clear_instances()
        TextCorrector.clear_instances()
        logging.info("OfflineCorrector cleaned up")
