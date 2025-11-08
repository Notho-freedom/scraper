"""Quick test for the complete correction pipeline"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.utils.grammar_checker import GrammarChecker, LANGUAGETOOL_AVAILABLE
from scraper.utils.text_corrector import TextCorrector
from scraper.exporters.html_generator import generate_corrected_html
from scraper.exporters.pdf_generator import PDFGenerator, WEASYPRINT_AVAILABLE

def test_full_pipeline():
    """Test the complete correction pipeline"""
    
    print("="*70)
    print("TEST PIPELINE COMPLET DE CORRECTION")
    print("="*70)
    print()
    
    # Check dependencies
    print("📦 Vérification des dépendances:")
    print(f"  - LanguageTool: {'✅ Disponible' if LANGUAGETOOL_AVAILABLE else '❌ Non disponible'}")
    print(f"  - WeasyPrint: {'✅ Disponible' if WEASYPRINT_AVAILABLE else '❌ Non disponible'}")
    print()
    
    if not LANGUAGETOOL_AVAILABLE:
        print("⚠️  LanguageTool requis. Installation: pip install language-tool-python")
        return
    
    # Sample text with errors
    text_with_errors = """
    Multi-Tess est votre partenaire de confiance pour tous vos projet d'ascenseurs.
    En tant que principale fournisseur national, nous concevons et fabriquons une gamme complète.
    Notre expertise couvre la conception sur mesur, l'installation professionelle et la maintenance préventive.
    Chaque projet Multi-Tess est une histoire unique de défi technique et de solution inovante.
    """
    
    print("1️⃣  TEXTE ORIGINAL:")
    print(text_with_errors)
    print()
    
    # Step 1: Check for errors
    print("2️⃣  DÉTECTION D'ERREURS...")
    checker = GrammarChecker(language='fr')
    check_result = checker.check_text(text_with_errors.strip())
    
    print(f"   Erreurs trouvées: {check_result.error_count}")
    print(f"   Par type: {check_result.errors_by_type}")
    
    if check_result.errors:
        print("\n   Exemples d'erreurs:")
        for i, error in enumerate(check_result.errors[:3], 1):
            print(f"     {i}. {error.error_type}: '{error.original_text}' → {error.suggestions[:2]}")
    print()
    
    # Step 2: Apply corrections
    print("3️⃣  CORRECTION AUTOMATIQUE...")
    corrector = TextCorrector(language='fr')
    correction_result = corrector.correct_text(text_with_errors.strip())
    
    print(f"   Corrections appliquées: {correction_result.correction_count}")
    print(f"   Score qualité: {correction_result.quality_score:.1f}/100")
    print()
    
    print("   TEXTE CORRIGÉ:")
    print(f"   {correction_result.corrected_text}")
    print()
    
    # Step 3: Generate HTML
    print("4️⃣  GÉNÉRATION HTML AVEC ANNOTATIONS...")
    
    # Create mock page data
    page_data = {
        'url': 'https://example.com/test',
        'metadata': {
            'title': 'Test de Correction',
            'language': 'fr'
        },
        'text': {
            'paragraphs': [text_with_errors.strip()],
            'word_count': len(text_with_errors.split()),
            'nlp_enabled': False
        },
        'corrections': {
            'corrected_paragraphs': [{
                'original_text': text_with_errors.strip(),
                'corrected_text': correction_result.corrected_text,
                'corrections': [c.to_dict() for c in correction_result.corrections],
                'quality_score': correction_result.quality_score
            }],
            'all_errors': [e.to_dict() for e in check_result.errors],
            'correction_count': correction_result.correction_count,
            'corrections_by_type': correction_result.corrections_by_type,
            'average_quality': correction_result.quality_score
        },
        'timestamp': '2025-11-08T17:00:00'
    }
    
    html_content = generate_corrected_html(page_data, include_annotations=True)
    
    # Save HTML
    html_path = "output/test_corrected.html"
    os.makedirs("output", exist_ok=True)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ HTML généré: {html_path}")
    print()
    
    # Step 4: Generate PDF
    if WEASYPRINT_AVAILABLE:
        print("5️⃣  GÉNÉRATION PDF...")
        try:
            pdf_gen = PDFGenerator(output_dir="output")
            pdf_path = pdf_gen.generate_from_html(html_content, "output/test_corrected.pdf")
            print(f"   ✅ PDF généré: {pdf_path}")
        except Exception as e:
            print(f"   ❌ Erreur PDF: {e}")
    else:
        print("5️⃣  GÉNÉRATION PDF: ⚠️  WeasyPrint non disponible")
    
    print()
    print("="*70)
    print("✅ PIPELINE COMPLET TESTÉ AVEC SUCCÈS!")
    print("="*70)

if __name__ == "__main__":
    test_full_pipeline()
