"""
WeasyPrint PDF Generator - Converts corrected HTML to PDF
"""

import logging
from pathlib import Path
from typing import List, Optional
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


class WeasyPrintGenerator:
    """Generates PDF from corrected HTML pages using WeasyPrint"""
    
    def __init__(self, output_dir: str = "output/pdf"):
        """
        Initialize PDF generator
        
        Args:
            output_dir: Directory to save PDF files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Font configuration for better rendering
        self.font_config = FontConfiguration()
        
        logging.info(f"WeasyPrintGenerator initialized, output: {self.output_dir}")
    
    def generate_single_pdf(self, html_path: Path, output_name: Optional[str] = None) -> str:
        """
        Generate PDF from a single HTML file
        
        Args:
            html_path: Path to HTML file
            output_name: Optional custom PDF filename
            
        Returns:
            Path to generated PDF
        """
        try:
            logging.info(f"Generating PDF from: {html_path.name}")
            
            # Determine output filename
            if output_name:
                pdf_filename = output_name if output_name.endswith('.pdf') else f"{output_name}.pdf"
            else:
                pdf_filename = html_path.stem + '.pdf'
            
            pdf_path = self.output_dir / pdf_filename
            
            # Custom CSS for better PDF rendering
            custom_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2cm;
                }
                
                body {
                    font-family: 'DejaVu Sans', Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    color: #2c3e50;
                    margin-top: 1em;
                    margin-bottom: 0.5em;
                    page-break-after: avoid;
                }
                
                h1 { font-size: 20pt; }
                h2 { font-size: 18pt; }
                h3 { font-size: 16pt; }
                
                p {
                    margin: 0.5em 0;
                    text-align: justify;
                    orphans: 3;
                    widows: 3;
                }
                
                del {
                    text-decoration: line-through;
                    color: #dc3545;
                    background-color: #f8d7da;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                
                ins {
                    text-decoration: none;
                    color: #28a745;
                    background-color: #d4edda;
                    font-weight: 500;
                    padding: 2px 4px;
                    border-radius: 3px;
                    margin-left: 3px;
                }
                
                img {
                    max-width: 100%;
                    height: auto;
                    page-break-inside: avoid;
                }
                
                table {
                    border-collapse: collapse;
                    width: 100%;
                    page-break-inside: avoid;
                }
                
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                
                th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                }
                
                .correction-legend {
                    background: #f8f9fa;
                    border: 2px solid #dee2e6;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 8px;
                    page-break-inside: avoid;
                }
                
                @media print {
                    a {
                        text-decoration: none;
                        color: #333;
                    }
                    
                    a[href]:after {
                        content: " (" attr(href) ")";
                        font-size: 9pt;
                        color: #666;
                    }
                }
            ''', font_config=self.font_config)
            
            # Generate PDF
            HTML(filename=str(html_path)).write_pdf(
                target=str(pdf_path),
                stylesheets=[custom_css],
                font_config=self.font_config
            )
            
            logging.info(f"PDF generated: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logging.error(f"Failed to generate PDF from {html_path}: {e}")
            raise
    
    def generate_multi_page_pdf(self, html_files: List[Path], output_name: str = "combined_report.pdf") -> str:
        """
        Generate a single PDF from multiple HTML files
        
        Args:
            html_files: List of HTML file paths
            output_name: Output PDF filename
            
        Returns:
            Path to generated PDF
        """
        try:
            logging.info(f"Generating combined PDF from {len(html_files)} pages")
            
            pdf_path = self.output_dir / output_name
            
            # Combine HTML files into one document
            combined_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Combined Report</title>
            </head>
            <body>
            """
            
            for i, html_file in enumerate(html_files):
                logging.info(f"  Adding page {i+1}/{len(html_files)}: {html_file.name}")
                
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Extract body content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                body = soup.find('body')
                
                if body:
                    # Add page separator (except for first page)
                    if i > 0:
                        combined_html += '<div style="page-break-before: always;"></div>'
                    
                    # Add page header
                    combined_html += f'<h1 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">Page {i+1}: {html_file.stem}</h1>'
                    
                    # Add body content
                    combined_html += str(body)
            
            combined_html += """
            </body>
            </html>
            """
            
            # Custom CSS for multi-page PDF
            custom_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2cm;
                    
                    @top-center {
                        content: "Site Correction Report";
                        font-size: 10pt;
                        color: #666;
                    }
                    
                    @bottom-right {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #666;
                    }
                }
                
                body {
                    font-family: 'DejaVu Sans', Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                }
                
                h1 {
                    color: #2c3e50;
                    font-size: 20pt;
                    margin-top: 0;
                    page-break-after: avoid;
                }
                
                del {
                    text-decoration: line-through;
                    color: #dc3545;
                    background-color: #f8d7da;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                
                ins {
                    text-decoration: none;
                    color: #28a745;
                    background-color: #d4edda;
                    font-weight: 500;
                    padding: 2px 4px;
                    border-radius: 3px;
                    margin-left: 3px;
                }
                
                img {
                    max-width: 100%;
                    height: auto;
                }
            ''', font_config=self.font_config)
            
            # Generate PDF from combined HTML
            HTML(string=combined_html, base_url=str(html_files[0].parent)).write_pdf(
                target=str(pdf_path),
                stylesheets=[custom_css],
                font_config=self.font_config
            )
            
            logging.info(f"Combined PDF generated: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logging.error(f"Failed to generate combined PDF: {e}")
            raise
    
    def generate_pdfs_batch(self, html_files: List[Path]) -> List[str]:
        """
        Generate individual PDFs for each HTML file
        
        Args:
            html_files: List of HTML file paths
            
        Returns:
            List of generated PDF paths
        """
        pdf_paths = []
        
        logging.info(f"Generating {len(html_files)} individual PDFs")
        
        for html_file in html_files:
            try:
                pdf_path = self.generate_single_pdf(html_file)
                pdf_paths.append(pdf_path)
            except Exception as e:
                logging.error(f"Skipping {html_file.name} due to error: {e}")
        
        logging.info(f"Generated {len(pdf_paths)}/{len(html_files)} PDFs successfully")
        return pdf_paths
