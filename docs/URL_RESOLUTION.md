# URL Resolution for Local HTML Viewing

## Problem

When scraping websites, the saved HTML snapshots contain relative URLs (e.g., `/assets/css/style.css`, `/images/logo.png`) that work on the server but break when opened locally:

```html
<!-- On server: https://example.com/page.html -->
<link href="/assets/css/style.css" rel="stylesheet">
<img src="/logo.png">
<script src="/js/main.js"></script>
```

When you open this HTML file locally (e.g., `file:///C:/Users/user/output/snapshot.html`):
- Browser looks for `file:///C:/assets/css/style.css` ❌
- Browser looks for `file:///C:/logo.png` ❌
- **Result**: No CSS, no images, no JavaScript - broken page!

## Solution

The `HTMLReconstructor.fix_relative_urls()` method automatically converts all relative URLs to absolute URLs:

```python
from scraper.exporters.html_reconstructor import HTMLReconstructor

reconstructor = HTMLReconstructor()
fixed_html = reconstructor.fix_relative_urls(html, "https://example.com")
```

**After conversion:**
```html
<link href="https://example.com/assets/css/style.css" rel="stylesheet">
<img src="https://example.com/logo.png">
<script src="https://example.com/js/main.js"></script>
```

Now when opened locally, the browser fetches resources from the original server! ✅

## What Gets Fixed

### 1. Link Stylesheets (`<link href>`)
```html
<!-- Before -->
<link rel="stylesheet" href="/css/main.css">
<link rel="icon" href="/favicon.ico">

<!-- After -->
<link rel="stylesheet" href="https://example.com/css/main.css">
<link rel="icon" href="https://example.com/favicon.ico">
```

### 2. Images (`<img src>` and `srcset`)
```html
<!-- Before -->
<img src="/images/logo.png">
<img srcset="/img/small.jpg 480w, /img/large.jpg 800w">

<!-- After -->
<img src="https://example.com/images/logo.png">
<img srcset="https://example.com/img/small.jpg 480w, https://example.com/img/large.jpg 800w">
```

### 3. Scripts (`<script src>`)
```html
<!-- Before -->
<script src="/js/bundle.js"></script>

<!-- After -->
<script src="https://example.com/js/bundle.js"></script>
```

### 4. Links (`<a href>`)
```html
<!-- Before -->
<a href="/about">About</a>
<a href="/contact">Contact</a>

<!-- After -->
<a href="https://example.com/about">About</a>
<a href="https://example.com/contact">Contact</a>
```

### 5. Inline CSS (`style` attribute)
```html
<!-- Before -->
<div style="background: url('/bg.jpg')">

<!-- After -->
<div style="background: url('https://example.com/bg.jpg')">
```

### 6. Style Tags (`<style>`)
```html
<!-- Before -->
<style>
  body { background: url('/images/pattern.png'); }
</style>

<!-- After -->
<style>
  body { background: url('https://example.com/images/pattern.png'); }
</style>
```

## What Doesn't Get Modified (Smart Filtering)

The function intelligently preserves URLs that should NOT be changed:

### External URLs (Already Absolute)
```html
<a href="https://external-site.com">External</a>
<!-- Not modified - already absolute -->
```

### Anchor Links
```html
<a href="#section">Jump to section</a>
<!-- Not modified - internal page anchor -->
```

### JavaScript/Data URIs
```html
<a href="javascript:void(0)">Click</a>
<img src="data:image/png;base64,...">
<!-- Not modified - special protocols -->
```

### mailto/tel Links
```html
<a href="mailto:contact@example.com">Email</a>
<a href="tel:+1234567890">Call</a>
<!-- Not modified - special protocols -->
```

## Usage in Code

### Automatic (Default Behavior)

URL fixing is **enabled by default** when saving snapshots:

```python
from scraper.exporters.html_reconstructor import HTMLReconstructor

reconstructor = HTMLReconstructor()

# Automatically fixes URLs using the page URL as base
reconstructor.save_snapshot(
    html=page_html,
    url="https://multi-tess-sarl.vercel.app/about",
    output_dir="output",
    version="v1_original",
    fix_urls=True  # Default: True
)
```

### Disable URL Fixing (Keep Relative Paths)

If you want to preserve relative URLs for some reason:

```python
reconstructor.save_snapshot(
    html=page_html,
    url="https://example.com/page",
    output_dir="output",
    version="v1",
    fix_urls=False  # Disable URL fixing
)
```

### Manual URL Fixing

You can also fix URLs independently:

```python
from scraper.exporters.html_reconstructor import HTMLReconstructor

reconstructor = HTMLReconstructor()

# Read HTML from anywhere
with open("downloaded_page.html", 'r', encoding='utf-8') as f:
    html = f.read()

# Fix URLs
fixed_html = reconstructor.fix_relative_urls(
    html=html,
    base_url="https://example.com"
)

# Save result
with open("fixed_page.html", 'w', encoding='utf-8') as f:
    f.write(fixed_html)
```

### Integration with Full Pipeline

The `reconstruct_page_with_corrections()` function also supports URL fixing:

```python
from scraper.exporters.html_reconstructor import reconstruct_page_with_corrections

# Page data from crawler
page_data = {
    'url': 'https://example.com/page',
    'html_snapshot': '<html>...</html>',
    'text': {'corrections': {...}}
}

# Reconstruct with corrections AND fix URLs
reconstructed_html = reconstruct_page_with_corrections(
    page_data=page_data,
    include_legend=True,
    fix_urls=True  # Default: True
)
```

## Command Line Usage

When running the scraper with HTML generation enabled:

```bash
# Generate corrected HTML with URL fixing (default)
python run.py https://example.com --correct --generate-html

# All snapshots will have absolute URLs automatically
# Output: output/snapshot_*.html files that work locally!
```

## Technical Implementation

### Method: `fix_relative_urls(html: str, base_url: str) -> str`

1. **Parse HTML** with BeautifulSoup
2. **Find all tags** with URL attributes (`href`, `src`, `srcset`)
3. **Use `urllib.parse.urljoin()`** to convert relative → absolute
4. **Handle special cases**:
   - Skip already-absolute URLs (`http://`, `https://`)
   - Skip special protocols (`data:`, `javascript:`, `mailto:`, `tel:`)
   - Skip anchors (`#section`)
   - Parse and fix CSS `url()` in `<style>` tags and `style` attributes
   - Handle responsive images (`srcset` with multiple sources)
5. **Return** modified HTML string

### Example Transformation

**Input HTML:**
```html
<html>
<head>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <img src="/logo.png">
  <a href="/about">About</a>
</body>
</html>
```

**Code:**
```python
reconstructor = HTMLReconstructor()
fixed = reconstructor.fix_relative_urls(html, "https://example.com")
```

**Output HTML:**
```html
<html>
<head>
  <link rel="stylesheet" href="https://example.com/style.css">
</head>
<body>
  <img src="https://example.com/logo.png">
  <a href="https://example.com/about">About</a>
</body>
</html>
```

## Benefits

✅ **Local viewing**: Open HTML snapshots locally without broken resources  
✅ **Distribution**: Share HTML files with customers who can open them offline  
✅ **Testing**: Review scraped pages with full styling and layout  
✅ **Archival**: Create self-contained HTML archives with working external resources  
✅ **PDF generation**: Convert to PDF with proper styling (requires external resources to load)  

## Limitations

⚠️ **Requires internet connection** to view the saved HTML (resources fetch from original server)  
⚠️ **Original site must be online** for resources to load  
⚠️ **No offline archive** - for true offline viewing, consider using `pywebcopy` to download all assets  

## Alternative: Full Site Cloning

For **true offline viewing** without internet connection:

### Option 1: pywebcopy (Future Enhancement)

```bash
pip install pywebcopy
```

```python
from pywebcopy import save_webpage

# Downloads entire site with all assets
save_webpage(
    url='https://example.com',
    project_folder='output/offline_site',
    project_name='example',
    bypass_robots=True,
    open_in_browser=False
)
```

**Pros:**
- True offline viewing
- All CSS, JS, images downloaded locally
- No internet needed after download

**Cons:**
- Much larger storage (downloads all assets)
- Slower (must download every resource)
- More complex

### Comparison

| Feature | URL Resolution (Current) | pywebcopy (Full Clone) |
|---------|-------------------------|------------------------|
| Storage | Small (HTML only) | Large (HTML + all assets) |
| Speed | Fast | Slow |
| Offline viewing | No (needs internet) | Yes (fully offline) |
| Implementation | Simple | Complex |
| Current status | ✅ Implemented | ⏳ Future enhancement |

## Testing

Run the URL fixing tests:

```bash
# Test URL fixing functionality
python tests/test_url_fixing.py

# Test with real page
python tests/test_page_url_fixed.py

# Full pipeline test with URL fixing
python tests/test_full_pipeline.py
```

All tests verify:
- Relative URLs converted to absolute
- External URLs preserved
- Anchor links preserved  
- Special protocols preserved
- CSS `url()` converted in `<style>` tags and `style` attributes

## Troubleshooting

### Issue: CSS still not loading
**Solution**: Check browser console for CORS errors. Some sites block external CSS loading.

### Issue: Images showing as broken
**Solution**: Verify the original site is online. Use browser DevTools Network tab to check 404s.

### Issue: Relative URLs not converted
**Solution**: Ensure `fix_urls=True` in `save_snapshot()` call (it's the default).

### Issue: Some resources still relative
**Solution**: Report the issue with HTML snippet - there may be an edge case not covered.

## Changelog

- **v1.0** (2025-01-16): Initial URL resolution implementation
  - Supports `href`, `src`, `srcset` attributes
  - Supports inline CSS `url()` and `<style>` tags
  - Smart filtering for anchors, external URLs, special protocols
  - Integrated with `save_snapshot()` and `reconstruct_page_with_corrections()`
  - Enabled by default with `fix_urls=True` parameter

## Future Enhancements

- [ ] Full asset download with `pywebcopy`
- [ ] Optional flag: `--download-assets` for offline viewing
- [ ] CSS/JS minification for smaller snapshots
- [ ] Base64 encoding of small images inline
- [ ] PDF generation with embedded assets
