"""Test script for grammar checking and correction"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.utils.grammar_checker import GrammarChecker, LANGUAGETOOL_AVAILABLE
from scraper.utils.text_corrector import TextCorrector

def test_grammar_checker():
    """Test grammar checker"""
    print("="*60)
    print("TEST: Grammar Checker")
    print("="*60)
    print(f"LanguageTool available: {LANGUAGETOOL_AVAILABLE}\n")
    
    if not LANGUAGETOOL_AVAILABLE:
        print("⚠️  LanguageTool not available. Install with:")
        print("   pip install language-tool-python")
        return
    
    # Test text with errors
    text = "Voici un texte avec des erreur de grammaire et d'orthographe."
    
    print(f"Original text: {text}\n")
    
    # Check for errors
    checker = GrammarChecker(language='fr')
    result = checker.check_text(text)
    
    print(f"Errors found: {result.error_count}")
    print(f"By type: {result.errors_by_type}")
    print(f"By severity: {result.errors_by_severity}\n")
    
    if result.errors:
        print("Details:")
        for i, error in enumerate(result.errors[:3], 1):
            print(f"\n{i}. {error.error_type}: {error.message}")
            print(f"   Original: '{error.original_text}'")
            print(f"   Suggestions: {error.suggestions[:3]}")
    
    print("\n" + "="*60 + "\n")

def test_text_corrector():
    """Test text corrector"""
    print("="*60)
    print("TEST: Text Corrector")
    print("="*60 + "\n")
    
    if not LANGUAGETOOL_AVAILABLE:
        print("⚠️  Correction requires LanguageTool")
        return
    
    text = "Voici un texte avec des erreur de grammaire."
    
    print(f"Original: {text}\n")
    
    # Correct text
    corrector = TextCorrector(language='fr')
    result = corrector.correct_text(text)
    
    print(f"Corrections made: {result.correction_count}")
    print(f"Quality score: {result.quality_score:.1f}/100\n")
    
    if result.corrections:
        print("Corrections:")
        for i, corr in enumerate(result.corrections, 1):
            print(f"{i}. '{corr.original}' → '{corr.corrected}' (confidence: {corr.confidence:.0%})")
    
    print(f"\nCorrected: {result.corrected_text}")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_grammar_checker()
    test_text_corrector()
    print("✅ Tests completed!")
