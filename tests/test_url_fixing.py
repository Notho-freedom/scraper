"""Test URL fixing functionality"""

import sys
import os
from pathlib import Path

# Add scraper directory to path
scraper_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scraper_dir))

from scraper.exporters.html_reconstructor import HTMLReconstructor

def test_url_fixing():
    """Test that relative URLs are converted to absolute"""
    
    # Sample HTML with relative URLs
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="/assets/css/main.css">
        <link rel="icon" href="/favicon.ico">
        <style>
            body { background: url('/images/bg.jpg'); }
        </style>
    </head>
    <body>
        <img src="/logo.png" alt="Logo">
        <img srcset="/images/small.jpg 480w, /images/large.jpg 800w" alt="Responsive">
        <script src="/js/main.js"></script>
        <a href="/about">About</a>
        <a href="https://external.com/page">External</a>
        <a href="#section">Anchor</a>
    </body>
    </html>
    """
    
    base_url = "https://multi-tess-sarl.vercel.app"
    
    print("[1] Testing URL fixing...")
    reconstructor = HTMLReconstructor()
    fixed_html = reconstructor.fix_relative_urls(html, base_url)
    
    # Check conversions
    print("\n[2] Checking conversions:")
    
    checks = [
        ("/assets/css/main.css", "https://multi-tess-sarl.vercel.app/assets/css/main.css"),
        ("/favicon.ico", "https://multi-tess-sarl.vercel.app/favicon.ico"),
        ("/images/bg.jpg", "https://multi-tess-sarl.vercel.app/images/bg.jpg"),
        ("/logo.png", "https://multi-tess-sarl.vercel.app/logo.png"),
        ("/js/main.js", "https://multi-tess-sarl.vercel.app/js/main.js"),
        ("/about", "https://multi-tess-sarl.vercel.app/about"),
    ]
    
    all_passed = True
    for relative, expected in checks:
        if expected in fixed_html:
            print(f"  [OK] {relative} -> {expected}")
        else:
            print(f"  [!] FAILED: {relative} not converted to {expected}")
            all_passed = False
    
    # Check that external URLs and anchors are NOT changed
    print("\n[3] Checking preserved URLs:")
    preserve_checks = [
        ("https://external.com/page", "External URL"),
        ("#section", "Anchor link"),
    ]
    
    for url, desc in preserve_checks:
        if url in fixed_html:
            print(f"  [OK] {desc} preserved: {url}")
        else:
            print(f"  [!] FAILED: {desc} was incorrectly modified")
            all_passed = False
    
    # Save output for inspection
    output_path = "output/test_url_fixing_result.html"
    os.makedirs("output", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fixed_html)
    print(f"\n[4] Saved result to: {output_path}")
    
    # Print result
    if all_passed:
        print("\n[OK] All URL fixing tests passed!")
    else:
        print("\n[!] Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = test_url_fixing()
    sys.exit(0 if success else 1)
