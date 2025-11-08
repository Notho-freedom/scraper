"""Test HTML reconstruction with corrections"""

import sys
import os
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.exporters.html_reconstructor import HTMLReconstructor

# Sample HTML
html = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Bienvenue</h1>
    <p>Voici un texte avec des erreur de grammaire.</p>
    <p>Un autre paragraphe sans fautes.</p>
</body>
</html>
"""

# Sample corrections data (matching the structure from text_corrector)
corrections_data = {
    'corrected_paragraphs': [
        {
            'original_text': 'Voici un texte avec des erreur de grammaire.',
            'corrected_text': 'Voici un texte avec des erreurs de grammaire.',
            'corrections': [
                {
                    'original': 'erreur',
                    'corrected': 'erreurs',
                    'position': 28,
                    'length': 6,
                    'type': 'grammar',
                    'rule_id': 'test'
                }
            ],
            'quality_score': 95.0
        }
    ]
}

print("🔍 Testing HTML Reconstruction...\n")
print("Original HTML:")
print(html)
print("\n" + "="*70 + "\n")

reconstructor = HTMLReconstructor()
reconstructed = reconstructor.reconstruct_with_corrections(html, corrections_data)

print("Reconstructed HTML with corrections:")
print(reconstructed)
print("\n" + "="*70 + "\n")

# Check if corrections were applied
if '<del' in reconstructed and '<ins' in reconstructed:
    print("✅ SUCCESS: Corrections were injected!")
    print(f"   Found <del> tag: {'erreur' in reconstructed}")
    print(f"   Found <ins> tag: {'erreurs' in reconstructed}")
else:
    print("❌ FAILED: Corrections were NOT injected")

# Add legend
with_legend = reconstructor.add_correction_legend(reconstructed)
if 'Légende des corrections' in with_legend:
    print("✅ Legend added successfully")
else:
    print("❌ Legend not added")
