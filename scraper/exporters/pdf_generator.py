"""PDF generator with statistics pages"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import os

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logging.warning("WeasyPrint not available. Install with: pip install weasyprint")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. Install with: pip install reportlab")


class PDFGenerator:
    """Generate professional PDF reports with corrections and statistics"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize PDF generator.
        
        Args:
            output_dir: Output directory for PDFs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_from_html(self, html_content: str, output_path: str, 
                          stats_pages: Optional[str] = None) -> str:
        """
        Generate PDF from HTML using WeasyPrint.
        
        Args:
            html_content: HTML content
            output_path: Output PDF path
            stats_pages: Optional HTML for statistics pages
            
        Returns:
            Path to generated PDF
        """
        if not WEASYPRINT_AVAILABLE:
            logging.error("WeasyPrint not available")
            raise ImportError("WeasyPrint required for PDF generation")
        
        try:
            # Combine main content with stats
            full_html = html_content
            if stats_pages:
                full_html += stats_pages
            
            # Generate PDF
            HTML(string=full_html).write_pdf(output_path)
            
            logging.info(f"PDF generated: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"PDF generation failed: {e}")
            raise
    
    def generate_statistics_html(self, summary: Dict, pages_data: List[Dict]) -> str:
        """
        Generate HTML for statistics pages.
        
        Args:
            summary: Overall summary statistics
            pages_data: List of page data with corrections
            
        Returns:
            HTML string for statistics pages
        """
        html_parts = []
        
        # Page break before stats
        html_parts.append('<div style="page-break-before: always;"></div>')
        
        # Statistics header
        html_parts.append('''
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 3rem; text-align: center;">
    <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">📊 STATISTIQUES D'ANALYSE</h1>
    <p style="font-size: 1.2rem; opacity: 0.9;">Rapport Complet de Correction</p>
</div>
''')
        
        # Summary section
        html_parts.append('<div style="padding: 2rem; max-width: 1200px; margin: 0 auto;">')
        
        # Executive summary
        html_parts.append('''
<h2 style="color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem; margin: 2rem 0 1rem 0;">
    📈 Résumé Exécutif
</h2>
''')
        
        total_pages = summary.get('total_pages', 0)
        total_corrections = summary.get('total_corrections', 0)
        avg_quality = summary.get('average_quality_score', 0)
        
        html_parts.append(f'''
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem;">
    <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold; color: #1976d2;">{total_pages}</div>
        <div style="color: #555; margin-top: 0.5rem;">Pages Analysées</div>
    </div>
    <div style="background: #fff3e0; padding: 1.5rem; border-radius: 8px; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold; color: #f57c00;">{total_corrections}</div>
        <div style="color: #555; margin-top: 0.5rem;">Corrections Totales</div>
    </div>
    <div style="background: #e8f5e9; padding: 1.5rem; border-radius: 8px; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold; color: #388e3c;">{avg_quality:.1f}/100</div>
        <div style="color: #555; margin-top: 0.5rem;">Score Qualité Moyen</div>
    </div>
</div>
''')
        
        # Corrections by type
        corrections_by_type = summary.get('corrections_by_type', {})
        if corrections_by_type:
            html_parts.append('''
<h2 style="color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem; margin: 2rem 0 1rem 0;">
    🔍 Répartition des Corrections
</h2>
<table style="width: 100%; border-collapse: collapse; margin-bottom: 2rem;">
    <thead>
        <tr style="background: #f5f5f5;">
            <th style="padding: 1rem; text-align: left; border-bottom: 2px solid #ddd;">Type d'Erreur</th>
            <th style="padding: 1rem; text-align: center; border-bottom: 2px solid #ddd;">Nombre</th>
            <th style="padding: 1rem; text-align: center; border-bottom: 2px solid #ddd;">Pourcentage</th>
        </tr>
    </thead>
    <tbody>
''')
            
            total = sum(corrections_by_type.values())
            for error_type, count in sorted(corrections_by_type.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                html_parts.append(f'''
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid #eee;">{error_type.title()}</td>
            <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid #eee; font-weight: bold;">{count}</td>
            <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid #eee;">{percentage:.1f}%</td>
        </tr>
''')
            
            html_parts.append('    </tbody>\n</table>')
        
        # Page-by-page details
        html_parts.append('''
<h2 style="color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem; margin: 2rem 0 1rem 0;">
    📄 Détails par Page
</h2>
''')
        
        for i, page in enumerate(pages_data[:10], 1):  # Limit to 10 pages
            corrections = page.get('corrections', {})
            url = page.get('url', 'N/A')
            
            html_parts.append(f'''
<div style="background: #fafafa; padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; border-left: 4px solid #667eea;">
    <h3 style="color: #2c3e50; margin-bottom: 0.5rem;">Page {i}</h3>
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 1rem; word-break: break-all;">{url}</div>
    <div style="display: flex; gap: 2rem;">
        <div><strong>Corrections:</strong> {corrections.get('correction_count', 0)}</div>
        <div><strong>Qualité:</strong> {corrections.get('average_quality', 0):.1f}/100</div>
    </div>
</div>
''')
        
        if len(pages_data) > 10:
            html_parts.append(f'<p style="text-align: center; color: #666;"><em>...et {len(pages_data) - 10} autres pages</em></p>')
        
        html_parts.append('</div>')  # Close container
        
        return '\n'.join(html_parts)
    
    def generate_report(self, pages_data: List[Dict], html_pages: List[str], 
                       output_filename: str = None) -> str:
        """
        Generate complete PDF report with all pages and statistics.
        
        Args:
            pages_data: List of page data with corrections
            html_pages: List of HTML content for each page
            output_filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated PDF
        """
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"corrected_report_{timestamp}.pdf"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Calculate summary statistics
        summary = self._calculate_summary(pages_data)
        
        # Generate statistics HTML
        stats_html = self.generate_statistics_html(summary, pages_data)
        
        # Combine all HTML
        full_html = '\n'.join(html_pages) + stats_html
        
        # Generate PDF
        return self.generate_from_html(full_html, output_path)
    
    def _calculate_summary(self, pages_data: List[Dict]) -> Dict:
        """Calculate overall summary statistics"""
        total_corrections = 0
        total_quality = 0
        corrections_by_type = {}
        
        for page in pages_data:
            corrections = page.get('corrections', {})
            
            # Count corrections
            count = corrections.get('correction_count', 0)
            total_corrections += count
            
            # Sum quality scores
            quality = corrections.get('average_quality', 0)
            total_quality += quality
            
            # Aggregate by type
            for error_type, type_count in corrections.get('corrections_by_type', {}).items():
                corrections_by_type[error_type] = corrections_by_type.get(error_type, 0) + type_count
        
        avg_quality = total_quality / len(pages_data) if pages_data else 0
        
        return {
            'total_pages': len(pages_data),
            'total_corrections': total_corrections,
            'average_quality_score': avg_quality,
            'corrections_by_type': corrections_by_type,
            'pages_with_corrections': sum(1 for p in pages_data if p.get('corrections', {}).get('correction_count', 0) > 0)
        }


def generate_pdf_report(pages_data: List[Dict], html_pages: List[str], 
                       output_dir: str = "output", output_filename: str = None) -> str:
    """
    Convenience function to generate PDF report.
    
    Args:
        pages_data: List of page data with corrections
        html_pages: List of HTML content
        output_dir: Output directory
        output_filename: Output filename
        
    Returns:
        Path to generated PDF
    """
    generator = PDFGenerator(output_dir=output_dir)
    return generator.generate_report(pages_data, html_pages, output_filename)
