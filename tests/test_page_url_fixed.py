"""Test URL fixing with real test page"""

import sys
import os
from pathlib import Path

# Add scraper directory to path
scraper_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scraper_dir))

from scraper.exporters.html_reconstructor import HTMLReconstructor

def test_with_real_page():
    """Test URL fixing with test_page_errors.html"""
    
    print("[1] Loading test_page_errors.html...")
    test_file = Path(__file__).parent / "test_page_errors.html"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Simulate the URL this page would have on Multi-Tess site
    base_url = "https://multi-tess-sarl.vercel.app"
    
    print(f"[2] Applying URL fixes with base: {base_url}")
    reconstructor = HTMLReconstructor()
    fixed_html = reconstructor.fix_relative_urls(html, base_url)
    
    # Count relative vs absolute URLs
    print("\n[3] Analyzing results:")
    
    import re
    
    # Find all href and src attributes
    href_relative = len(re.findall(r'href=["\']/', fixed_html))
    src_relative = len(re.findall(r'src=["\']/', fixed_html))
    
    href_absolute = len(re.findall(r'href=["\']https?://', fixed_html))
    src_absolute = len(re.findall(r'src=["\']https?://', fixed_html))
    
    print(f"  Relative href: {href_relative} (should be 0)")
    print(f"  Absolute href: {href_absolute}")
    print(f"  Relative src: {src_relative} (should be 0)")
    print(f"  Absolute src: {src_absolute}")
    
    # Save result
    output_path = "output/test_page_url_fixed.html"
    os.makedirs("output", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fixed_html)
    
    print(f"\n[4] Saved result to: {output_path}")
    print("     You can now open this file locally and all resources should load!")
    
    # Check for success
    success = (href_relative == 0 and src_relative == 0)
    
    if success:
        print("\n[OK] URL fixing successful - all relative paths converted!")
    else:
        print("\n[!] Warning: Some relative paths remain")
    
    return success

if __name__ == "__main__":
    success = test_with_real_page()
    sys.exit(0 if success else 1)
