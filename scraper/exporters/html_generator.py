"""HTML generator with corrections highlighting"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
import html


class CorrectedHTMLGenerator:
    """Generate HTML pages with corrections highlighted"""
    
    # Color scheme for different error types
    ERROR_COLORS = {
        'spelling': '#ff6b6b',      # Red
        'grammar': '#ffa726',        # Orange
        'punctuation': '#66bb6a',    # Green
        'typography': '#42a5f5',     # Blue
        'style': '#ab47bc',          # Purple
        'other': '#78909c'           # Grey
    }
    
    def __init__(self, site_title: str = "Site Corrigé"):
        """
        Initialize HTML generator.
        
        Args:
            site_title: Title for the generated site
        """
        self.site_title = site_title
    
    def generate_page(self, page_data: Dict, include_annotations: bool = True) -> str:
        """
        Generate HTML for a single page with corrections.
        
        Args:
            page_data: Page data with corrections
            include_annotations: Include error annotations
            
        Returns:
            HTML string
        """
        url = page_data.get('url', 'Unknown')
        metadata = page_data.get('metadata', {})
        text_data = page_data.get('text', {})
        corrections_data = page_data.get('corrections', {})
        
        # Build HTML
        html_parts = []
        
        # Head
        html_parts.append(self._generate_head(metadata.get('title', 'Page')))
        
        # Body start
        html_parts.append('<body>')
        
        # Header with navigation
        html_parts.append(self._generate_header(url, metadata))
        
        # Correction summary banner
        if corrections_data.get('correction_count', 0) > 0:
            html_parts.append(self._generate_correction_banner(corrections_data))
        
        # Main content
        html_parts.append('<main class="container">')
        
        # Original title
        if metadata.get('title'):
            html_parts.append(f'<h1>{html.escape(metadata["title"])}</h1>')
        
        # Corrected text with highlights
        if corrections_data.get('corrected_paragraphs'):
            html_parts.append('<div class="content-corrected">')
            for para_result in corrections_data['corrected_paragraphs']:
                html_parts.append(self._generate_corrected_paragraph(para_result, include_annotations))
            html_parts.append('</div>')
        elif text_data.get('paragraphs'):
            # Fallback: show original paragraphs
            html_parts.append('<div class="content-original">')
            for para in text_data['paragraphs']:
                html_parts.append(f'<p>{html.escape(para)}</p>')
            html_parts.append('</div>')
        
        # Error list (if annotations enabled)
        if include_annotations and corrections_data.get('all_errors'):
            html_parts.append(self._generate_error_list(corrections_data['all_errors']))
        
        html_parts.append('</main>')
        
        # Footer
        html_parts.append(self._generate_footer(page_data))
        
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
    
    def _generate_head(self, title: str) -> str:
        """Generate HTML head with styles"""
        return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} - Corrigé</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .header .url {{
            opacity: 0.9;
            font-size: 0.9rem;
            word-break: break-all;
        }}
        
        .correction-banner {{
            background: #4caf50;
            color: white;
            padding: 1rem;
            text-align: center;
            font-weight: 500;
        }}
        
        .correction-banner.has-errors {{
            background: #ff9800;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        main.container {{
            background: white;
            border-radius: 8px;
            padding: 3rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 2rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.5rem;
        }}
        
        .content-corrected p {{
            margin-bottom: 1.5rem;
            font-size: 1.1rem;
            line-height: 1.8;
        }}
        
        .correction {{
            background: #fff3cd;
            border-bottom: 2px solid;
            padding: 2px 4px;
            cursor: help;
            position: relative;
            transition: all 0.3s ease;
        }}
        
        .correction:hover {{
            background: #ffeaa7;
            transform: translateY(-1px);
        }}
        
        .correction.spelling {{ border-color: {self.ERROR_COLORS['spelling']}; }}
        .correction.grammar {{ border-color: {self.ERROR_COLORS['grammar']}; }}
        .correction.punctuation {{ border-color: {self.ERROR_COLORS['punctuation']}; }}
        .correction.typography {{ border-color: {self.ERROR_COLORS['typography']}; }}
        .correction.style {{ border-color: {self.ERROR_COLORS['style']}; }}
        .correction.other {{ border-color: {self.ERROR_COLORS['other']}; }}
        
        .correction .tooltip {{
            visibility: hidden;
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background: #2c3e50;
            color: white;
            padding: 0.75rem;
            border-radius: 6px;
            font-size: 0.85rem;
            width: 250px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            line-height: 1.4;
        }}
        
        .correction:hover .tooltip {{
            visibility: visible;
        }}
        
        .tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border: 5px solid transparent;
            border-top-color: #2c3e50;
        }}
        
        .error-list {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 2px solid #eee;
        }}
        
        .error-list h2 {{
            color: #e74c3c;
            margin-bottom: 1.5rem;
        }}
        
        .error-item {{
            background: #fef5e7;
            border-left: 4px solid;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }}
        
        .error-item.spelling {{ border-left-color: {self.ERROR_COLORS['spelling']}; }}
        .error-item.grammar {{ border-left-color: {self.ERROR_COLORS['grammar']}; }}
        .error-item.punctuation {{ border-left-color: {self.ERROR_COLORS['punctuation']}; }}
        .error-item.typography {{ border-left-color: {self.ERROR_COLORS['typography']}; }}
        .error-item.style {{ border-left-color: {self.ERROR_COLORS['style']}; }}
        
        .error-type {{
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            color: #e74c3c;
            margin-bottom: 0.25rem;
        }}
        
        .error-message {{
            margin-bottom: 0.5rem;
        }}
        
        .error-suggestion {{
            color: #27ae60;
            font-weight: 500;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 2rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
            font-size: 0.9rem;
        }}
        
        @media print {{
            .correction-banner, .error-list, .legend {{
                display: none;
            }}
        }}
    </style>
</head>'''
    
    def _generate_header(self, url: str, metadata: Dict) -> str:
        """Generate header section"""
        parsed = urlparse(url)
        return f'''<header class="header">
    <div class="container">
        <h1>🔍 {html.escape(self.site_title)}</h1>
        <div class="url">📄 {html.escape(url)}</div>
    </div>
</header>'''
    
    def _generate_correction_banner(self, corrections_data: Dict) -> str:
        """Generate correction summary banner"""
        count = corrections_data.get('correction_count', 0)
        quality = corrections_data.get('average_quality', 0)
        
        if count == 0:
            return '''<div class="correction-banner">
    ✅ Aucune correction nécessaire - Texte de qualité excellente!
</div>'''
        
        return f'''<div class="correction-banner has-errors">
    ⚠️ {count} correction{'s' if count > 1 else ''} appliquée{'s' if count > 1 else ''} | Score qualité: {quality:.1f}/100
</div>'''
    
    def _generate_corrected_paragraph(self, para_result: Dict, include_annotations: bool) -> str:
        """Generate paragraph with corrections highlighted"""
        corrections = para_result.get('corrections', [])
        
        if not corrections:
            # No corrections - show original
            return f'<p>{html.escape(para_result.get("corrected_text", ""))}</p>'
        
        # Build paragraph with highlighted corrections
        text = para_result.get('original_text', '')
        result_parts = []
        last_pos = 0
        
        # Sort corrections by position
        sorted_corrections = sorted(corrections, key=lambda c: c.get('position', 0))
        
        for corr in sorted_corrections:
            pos = corr.get('position', 0)
            length = corr.get('length', 0)
            original = corr.get('original', '')
            corrected = corr.get('corrected', '')
            error_type = corr.get('type', 'other')
            
            # Add text before correction
            if pos > last_pos:
                result_parts.append(html.escape(text[last_pos:pos]))
            
            # Add highlighted correction
            if include_annotations:
                tooltip = f"Original: {html.escape(original)}<br>Corrigé: {html.escape(corrected)}"
                result_parts.append(
                    f'<span class="correction {error_type}" data-original="{html.escape(original)}">'
                    f'{html.escape(corrected)}'
                    f'<span class="tooltip">{tooltip}</span>'
                    f'</span>'
                )
            else:
                result_parts.append(html.escape(corrected))
            
            last_pos = pos + length
        
        # Add remaining text
        if last_pos < len(text):
            result_parts.append(html.escape(text[last_pos:]))
        
        return f'<p>{"".join(result_parts)}</p>'
    
    def _generate_error_list(self, errors: List[Dict]) -> str:
        """Generate list of all errors"""
        if not errors:
            return ''
        
        html_parts = ['<div class="error-list">']
        html_parts.append('<h2>📋 Liste des Corrections</h2>')
        
        for i, error in enumerate(errors[:20], 1):  # Limit to 20 errors
            error_type = error.get('type', 'other')
            message = error.get('message', 'Error')
            original = error.get('original_text', '')
            suggestions = error.get('suggestions', [])
            
            html_parts.append(f'<div class="error-item {error_type}">')
            html_parts.append(f'<div class="error-type">{error_type}</div>')
            html_parts.append(f'<div class="error-message">{html.escape(message)}</div>')
            if original:
                html_parts.append(f'<div>Texte: "<strong>{html.escape(original)}</strong>"</div>')
            if suggestions:
                html_parts.append(f'<div class="error-suggestion">→ {html.escape(suggestions[0])}</div>')
            html_parts.append('</div>')
        
        if len(errors) > 20:
            html_parts.append(f'<p><em>...et {len(errors) - 20} autres erreurs</em></p>')
        
        # Add legend
        html_parts.append(self._generate_legend())
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_legend(self) -> str:
        """Generate color legend"""
        legend_items = [
            ('spelling', 'Orthographe'),
            ('grammar', 'Grammaire'),
            ('punctuation', 'Ponctuation'),
            ('typography', 'Typographie'),
            ('style', 'Style')
        ]
        
        items = []
        for error_type, label in legend_items:
            color = self.ERROR_COLORS[error_type]
            items.append(
                f'<div class="legend-item">'
                f'<div class="legend-color" style="background: {color};"></div>'
                f'<span>{label}</span>'
                f'</div>'
            )
        
        return f'<div class="legend">{"".join(items)}</div>'
    
    def _generate_footer(self, page_data: Dict) -> str:
        """Generate footer"""
        timestamp = page_data.get('timestamp', datetime.now().isoformat())
        
        return f'''<footer class="footer">
    <p>📝 Rapport généré par <strong>ULTRACORE REAPER v2.0</strong></p>
    <p>🕐 {timestamp}</p>
    <p>✨ Avec correction automatique et analyse NLP avancée</p>
</footer>'''


def generate_corrected_html(page_data: Dict, include_annotations: bool = True) -> str:
    """
    Convenience function to generate corrected HTML.
    
    Args:
        page_data: Page data with corrections
        include_annotations: Include error annotations
        
    Returns:
        HTML string
    """
    generator = CorrectedHTMLGenerator()
    return generator.generate_page(page_data, include_annotations)
