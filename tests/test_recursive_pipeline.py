"""
Test du pipeline récursif avec la page de test locale
"""

import sys
import os
import logging
from pathlib import Path

# Add scraper to path
scraper_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scraper_dir))

from scraper.core.recursive_downloader import RecursiveDownloader
from scraper.core.offline_corrector import OfflineCorrector
from scraper.exporters.weasyprint_generator import WeasyPrintGenerator
from scraper.utils import setup_logging

def test_recursive_pipeline():
    """Test complete pipeline with test page"""
    
    setup_logging("INFO")
    
    print("="*70)
    print("TEST PIPELINE RÉCURSIF - Page de test locale")
    print("="*70)
    
    # Setup directories
    output_dir = Path(__file__).parent.parent / "output" / "test_recursive"
    downloaded_dir = output_dir / "downloaded"
    corrected_dir = output_dir / "corrected"
    pdf_dir = output_dir / "pdf"
    
    # Clean previous test
    import shutil
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    print("\n[PHASE 1] PRÉPARATION")
    print("-" * 70)
    
    # Copy test page to simulate download
    test_page = Path(__file__).parent / "test_page_errors.html"
    pages_dir = downloaded_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy test page
    import shutil
    target_page = pages_dir / "index.html"
    shutil.copy(test_page, target_page)
    
    print(f"[OK] Page de test copiee: {target_page}")
    
    # Create fake pages list
    pages_list = [{
        'url': 'https://multi-tess-sarl.vercel.app/index.html',
        'local_path': str(target_page),
        'depth': 0
    }]
    
    print(f"[OK] Repertoires crees: {output_dir}")
    
    # ======================================================================
    # PHASE 2: CORRECTION
    # ======================================================================
    print("\n[PHASE 2] CORRECTION OFFLINE")
    print("-" * 70)
    
    corrector = OfflineCorrector(
        pages_dir=str(pages_dir),
        output_dir=str(corrected_dir),
        language="fr",
        aggressive=True
    )
    
    correction_summary = corrector.correct_all_pages(pages_list)
    corrector.cleanup()
    
    print(f"\n[OK] Pages corrigees: {correction_summary['corrected_successfully']}")
    print(f"[OK] Erreurs trouvees: {correction_summary['total_errors_found']}")
    print(f"[OK] Corrections appliquees: {correction_summary['total_corrections_applied']}")
    
    # ======================================================================
    # PHASE 3: PDF GENERATION
    # ======================================================================
    print("\n[PHASE 3] GÉNÉRATION PDF")
    print("-" * 70)
    
    pdf_generator = WeasyPrintGenerator(output_dir=str(pdf_dir))
    
    corrected_files = list(Path(corrected_dir).glob('*.html'))
    
    if not corrected_files:
        print("[ERROR] Aucun fichier HTML corrige trouve!")
        return False
    
    print(f"Fichiers HTML trouvés: {len(corrected_files)}")
    
    # Generate single PDF
    print("\nGénération du PDF...")
    try:
        pdf_path = pdf_generator.generate_single_pdf(
            corrected_files[0],
            output_name="test_corrections.pdf"
        )
        print(f"[OK] PDF genere: {pdf_path}")
        
        # Open PDF
        print("\nOuverture du PDF...")
        os.startfile(pdf_path)
        
    except Exception as e:
        print(f"[ERROR] Erreur PDF: {e}")
        logging.exception("PDF generation failed")
        return False
    
    # ======================================================================
    # SUMMARY
    # ======================================================================
    print("\n" + "="*70)
    print("TEST TERMINÉ AVEC SUCCÈS")
    print("="*70)
    print(f"\nFichiers générés:")
    print(f"  - Page originale: {target_page}")
    print(f"  - Page corrigée: {corrected_dir / 'index.html'}")
    print(f"  - PDF final: {pdf_path}")
    
    return True

if __name__ == "__main__":
    success = test_recursive_pipeline()
    sys.exit(0 if success else 1)
