"""
Test complet du pipeline de correction sur une page HTML avec erreurs.
"""
import logging
import sys
import os
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)

from scraper.utils.nlp_processor import NLPProcessor
from scraper.utils.grammar_checker import GrammarChecker
from scraper.utils.text_corrector import TextCorrector
from scraper.exporters.html_reconstructor import HTMLReconstructor

def test_full_correction_pipeline():
    """Test le pipeline complet de correction sur une page HTML avec erreurs."""
    
    print("=" * 80)
    print("TEST PIPELINE COMPLET DE CORRECTION")
    print("=" * 80)
    
    # 1. Charger le HTML de test
    test_file = Path(__file__).parent / "test_page_errors.html"
    print(f"\n[1] Chargement du fichier: {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 2. Extraire le texte
    print("\n[2] Extraction du texte...")
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    print(f"   Texte extrait: {len(text)} caractères")
    print(f"   Premiers 200 caractères: {text[:200]}...")
    
    # 3. Analyser avec NLP et détecter les erreurs
    print("\n[3] Analyse grammaticale et détection des erreurs...")
    
    # Initialize processors
    checker = GrammarChecker(language='fr')
    corrector = TextCorrector(language='fr')
    
    # Check for errors
    check_result = checker.check_text(text)
    
    print(f"\n[4] Résultats de l'analyse:")
    print(f"   Mots: {len(text.split())}")
    print(f"   Caractères: {len(text)}")
    
    # 4. Afficher les erreurs détectées
    all_errors = check_result.errors
    
    print(f"\n   Erreurs détectées: {check_result.error_count}")
    print("\nDétail des erreurs:")
    print("-" * 80)
    
    for i, error in enumerate(all_errors[:15], 1):  # Afficher les 15 premières
        print(f"\n{i}. Type: {error.error_type} | Sévérité: {error.severity}")
        print(f"   Texte original: '{error.original_text}'")
        if error.suggestions:
            print(f"   Suggestions: {', '.join(error.suggestions[:3])}")
        print(f"   Message: {error.message}")
        print(f"   Contexte: ...{error.context[:80]}...")
    
    if len(all_errors) > 15:
        print(f"\n   ... et {len(all_errors) - 15} autres erreurs")
    
    # 5. Appliquer les corrections
    print(f"\n[5] Application des corrections (mode agressif)...")
    correction_result = corrector.correct_text(text, aggressive=True)
    
    print(f"   Corrections appliquées: {correction_result.correction_count}")
    print(f"   Score qualité: {correction_result.quality_score:.1f}/100")
    
    if correction_result.corrections:
        print(f"\n   Exemples de corrections:")
        for i, corr in enumerate(correction_result.corrections[:5], 1):
            print(f"   {i}. '{corr.original}' -> '{corr.corrected}' (pos: {corr.position}, conf: {corr.confidence:.2f})")
    
    # 6. Créer une structure de corrections pour la reconstruction HTML
    print("\n[6] Préparation des données pour la reconstruction HTML...")
    
    if correction_result.correction_count > 0:
        print(f"   {correction_result.correction_count} corrections seront injectées dans le HTML")
        
        # Construire les données au format attendu par HTMLReconstructor
        corrections_data = {
            'corrected_paragraphs': [
                {
                    'original_text': text,
                    'corrected_text': correction_result.corrected_text,
                    'corrections': [c.to_dict() for c in correction_result.corrections]
                }
            ],
            'all_errors': [e.to_dict() for e in all_errors],
            'correction_count': correction_result.correction_count
        }
    else:
        print("   Aucune correction à injecter (seuil de confiance non atteint)")
        corrections_data = {
            'corrected_paragraphs': [],
            'all_errors': [e.to_dict() for e in all_errors],
            'correction_count': 0
        }
    
    # Construire les données de page
    page_data = {
        'url': 'test_page_errors.html',
        'html_snapshot': html,
        'text': {
            'corrections': corrections_data
        }
    }
    
    reconstructor = HTMLReconstructor()
    
    # Sauvegarder le snapshot original avec URL fixing
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # URL fictive pour le test (simule Multi-Tess site)
    test_url = "https://multi-tess-sarl.vercel.app/index.html"
    
    print(f"   [*] Conversion des URLs relatives vers absolues (base: {test_url})")
    original_file = reconstructor.save_snapshot(
        html, 
        test_url,
        str(output_dir),
        version='v1_original',
        fix_urls=True
    )
    print(f"   [OK] Snapshot original sauvegarde: {original_file}")
    
    # Reconstruire avec corrections
    if corrections_data['corrected_paragraphs'] and any(p.get('corrections') for p in corrections_data['corrected_paragraphs']):
        print("   [*] Injection des corrections dans le HTML...")
        reconstructed_html = reconstructor.reconstruct_with_corrections(html, corrections_data)
        
        # Ajouter la légende
        reconstructed_html = reconstructor.add_correction_legend(reconstructed_html)
        
        # Sauvegarder avec URL fixing
        corrected_file = reconstructor.save_snapshot(
            reconstructed_html,
            test_url,
            str(output_dir),
            version='v2_corrected',
            fix_urls=True
        )
        print(f"   [OK] Snapshot corrigé sauvegardé: {corrected_file}")
        print(f"   [i] Les fichiers peuvent maintenant être ouverts localement avec toutes les ressources!")
        
        # Vérifier les tags <del> et <ins>
        soup_corrected = BeautifulSoup(reconstructed_html, 'html.parser')
        del_tags = soup_corrected.find_all('del')
        ins_tags = soup_corrected.find_all('ins')
        
        print(f"\n[7] Résultat de l'injection:")
        print(f"   Tags <del> trouvés: {len(del_tags)}")
        print(f"   Tags <ins> trouvés: {len(ins_tags)}")
        
        if del_tags:
            print("\n   Exemples de corrections injectées:")
            for i, (del_tag, ins_tag) in enumerate(zip(del_tags[:3], ins_tags[:3]), 1):
                print(f"   {i}. <del>{del_tag.get_text()}</del> -> <ins>{ins_tag.get_text()}</ins>")
    else:
        print("   [!] Aucune correction structurée disponible pour l'injection")
        print("   [i] Les erreurs ont été détectées mais pas de corrections appliquées")
        
        # Sauvegarder quand même avec la légende
        html_with_legend = reconstructor.add_correction_legend(html)
        corrected_file = reconstructor.save_snapshot(
            html_with_legend,
            'test_page_errors.html',
            str(output_dir),
            version='v2_with_legend'
        )
        print(f"   [OK] Snapshot avec légende sauvegardé: {corrected_file}")
    
    print("\n" + "=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)
    print(f"\nFichiers générés dans: {output_dir}")
    print("Ouvrez les fichiers HTML dans un navigateur pour voir le résultat.")
    
    return {
        'errors_found': len(all_errors),
        'corrections_applied': correction_result.correction_count,
        'has_structured_corrections': any(p.get('corrections') for p in corrections_data['corrected_paragraphs'])
    }

if __name__ == "__main__":
    try:
        result = test_full_correction_pipeline()
        print(f"\nRésumé: {result}")
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()

