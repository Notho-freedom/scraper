# ULTRACORE REAPER v2.0

Advanced asynchronous web scraper with Playwright integration, browser pooling, intelligent caching, and comprehensive content analysis.

## 🌟 Features

### Core Capabilities
- 🚀 **High-performance async crawling** with configurable concurrency
- 🎭 **JavaScript rendering** with Playwright (React, Vue, Angular support)
- ⚡ **Browser context pooling** (5 parallel contexts for 3x speedup)
- 💾 **Intelligent HTML caching** with gzip compression and TTL
- 🔍 **Advanced extraction**: metadata, SEO tags, Open Graph, JSON-LD
- 📊 **Content analysis**: text, keywords, resources, links
- 🔄 **Duplicate detection** via content hashing
- 🤖 **Robots.txt compliance** with intelligent caching
- 📈 **Real-time performance metrics** and monitoring
- 🛡️ **Error recovery** with retry logic and rate limiting

### Export & Analysis
- 💾 **Multiple export formats**: JSON, CSV, SQLite
- 📝 **Text quality optimization**: duplicate removal, word splitting
- 📈 **Detailed statistics** and performance reports
- 🎯 **Smart resource blocking** for bandwidth optimization

## 🚀 Performance

### Measured Results (10 pages)
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total time | 23.33s | 8.03s | **-65.6%** |
| Pages/sec | 0.43 | 1.25 | **+190.5%** |
| Time/page | 2.33s | 0.80s | **-65.6%** |

**Key Features:**
- Browser context pooling (5 contexts)
- HTML caching with compression
- Adaptive timeouts (15s vs 30s)
- Resource blocking (-70% bandwidth)

## 📦 Installation

```bash
# Clone or download the project
cd scraper

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
## 🎯 Usage

### Interactive mode
```bash
python run.py
```

### Command-line mode
```bash
# Basic usage
python run.py https://example.com

# SPA/React/Vue sites (automatic JS detection)
python run.py https://react-app.vercel.app --format json

# High-volume scraping with custom pool
python run.py https://example.com --max-pages 1000 --max-depth 5 --format all

# All options
python run.py URL [--max-depth DEPTH] [--max-pages PAGES] [--concurrent N] 
              [--timeout SEC] [--format json|csv|sqlite|all] 
              [--output-dir DIR] [--no-robots] [--log-level LEVEL]
```

### Example: Scraping a React SPA
```bash
python run.py https://multi-tess-sarl.vercel.app --format json --max-pages 50
```

**Output:**
```
```
scraper/
├── scraper/              # Main package
│   ├── core/            # Core functionality
│   │   ├── config.py    # Configuration (with Playwright settings)
│   │   ├── state.py     # State management
│   │   └── crawler.py   # Main crawler (with JS fallback)
│   ├── extractors/      # Content extractors
│   │   ├── metadata.py  # Metadata extraction
│   │   ├── text.py      # Text extraction (optimized)
│   │   ├── links.py     # Link extraction
│   │   └── resources.py # Resource extraction
│   ├── exporters/       # Data exporters
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   └── sqlite_exporter.py
│   └── utils/           # Utilities
│       ├── hash.py              # Content hashing
│       ├── robots.py            # Robots.txt handler
│       ├── logger.py            # Logging setup
│       ├── js_detector.py       # JavaScript detection
│       ├── playwright_fetcher.py # Playwright pooling & cache
│       └── text_cleaner.py      # Text quality optimization
├── tests/               # Unit tests (43 tests)
├── output/              # Output directory
├── run.py              # Main entry point
├── requirements.txt    # Dependencies
├── OPTIMISATION_PLAYWRIGHT.md  # Performance optimization guide
└── README.md          # This file
``` ├── extractors/      # Content extractors
│   │   ├── metadata.py  # Metadata extraction
│   │   ├── text.py      # Text extraction
│   │   ├── links.py     # Link extraction
│   │   └── resources.py # Resource extraction
│   ├── exporters/       # Data exporters
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   └── sqlite_exporter.py
│   └── utils/           # Utilities
│       ├── hash.py      # Content hashing
│       ├── robots.py    # Robots.txt handler
│       └── logger.py    # Logging setup
├── tests/               # Unit tests
├── output/              # Output directory
├── run.py              # Main entry point
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## ⚙️ Configuration Options

### Command-Line Arguments
- `--max-depth N`: Maximum crawl depth (default: 30)
- `--max-pages N`: Maximum pages to crawl (default: 500)
- `--concurrent N`: Number of concurrent requests (default: 50)
- `--timeout SEC`: Request timeout in seconds (default: 15)
- `--format FORMAT`: Export format: json, csv, sqlite, or all (default: json)
- `--output-dir DIR`: Output directory (default: output)
- `--no-robots`: Ignore robots.txt rules
- `--log-level LEVEL`: Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

### Playwright Settings (Automatic)
- `playwright_pool_size`: Browser context pool size (default: 5)
- `playwright_cache_enabled`: Enable HTML caching (default: True)
- `playwright_cache_ttl`: Cache TTL in seconds (default: 3600)
- `playwright_timeout`: Page timeout in ms (default: 15000)

## 💡 Examples

```bash
# Quick scan with default settings
python run.py https://example.com

# Deep crawl with all export formats
python run.py https://example.com --max-depth 10 --max-pages 2000 --format all

# Fast, shallow scan with high concurrency
python run.py https://example.com --max-depth 2 --concurrent 100

# Export to CSV only with custom output
python run.py https://example.com --format csv --output-dir reports

# Debug mode for troubleshooting
python run.py https://example.com --log-level DEBUG
```

## 📊 Output

The scraper generates comprehensive reports including:

### Statistics
- Total pages analyzed
- Word count and text quality metrics
- Resource counts (images, scripts, CSS)
- Response time metrics (avg, min, max)
- HTTP status code distribution
- Content type analysis
- Duplicate detection results
- Crawl depth distribution

### Playwright Metrics (for JS-heavy sites)
- Total fetches with JavaScript rendering
- Cache hit rate
- Average fetch time
- Active browser pool usage
- Error count

### Export Formats
- **JSON**: Complete structured data with metadata
- **CSV**: Tabular format for Excel/analysis
- **SQLite**: Relational database for querying

## 🧪 Testing

```bash
# Run all tests (43 tests)
pytest

# Run with coverage
pytest --cov=scraper

# Run specific test module
pytest tests/test_text_cleaner.py -v

# Run tests in parallel
pytest -n auto
```

**Test Coverage**: 43 unit tests covering extractors, utils, and core functionality.

## 📚 Documentation

- `README.md` - This file (quick start guide)
- `OPTIMISATION_PLAYWRIGHT.md` - Detailed performance optimization guide
- `RAPPORT_AMELIORATIONS_TEXTE.md` - Text quality optimization report
- `RESUME_INTERVENTION.md` - Change log and intervention summary

## 🔧 Advanced Usage

### Custom Configuration

```python
from scraper.core import Config, CrawlerState, Crawler

config = Config(
    max_pages=1000,
    playwright_pool_size=10,      # More parallelism
    playwright_cache_ttl=7200,    # 2-hour cache
    concurrent_tasks=100
)

state = CrawlerState()
crawler = Crawler(config, state)
# ... use crawler
```

### Programmatic Access

```python
import asyncio
from scraper.utils import fetch_with_js

async def main():
    html = await fetch_with_js('https://react-app.com', timeout=15000)
    print(html)

asyncio.run(main())
```

## 🛠️ Troubleshooting

### Common Issues

**Playwright not found:**
```bash
python -m playwright install chromium
```

**Import errors:**
```bash
pip install -r requirements.txt --upgrade
```

**Slow performance on Windows:**
- Use PowerShell (not CMD)
- Disable Windows Defender real-time scanning for project folder

**Memory issues on large crawls:**
```python
# Reduce pool size
config = Config(playwright_pool_size=3, concurrent_tasks=20)
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - Feel free to use and modify as needed.

## 📝 Version History

- **v2.1.0** (2025-11-08): Playwright optimization with browser pooling, caching, and 3x performance improvement
- **v2.0.0**: Modular architecture with advanced features
- **v1.0.0**: Initial monolithic version
