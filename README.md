# ULTRACORE REAPER v2.0

Advanced asynchronous web scraper with metadata extraction, content analysis, and multiple export formats.

## Features

- 🚀 **High-performance async crawling** with configurable concurrency
- 🔍 **Advanced extraction**: metadata, SEO tags, Open Graph, JSON-LD
- 📊 **Content analysis**: text, keywords, resources, links
- 🔄 **Duplicate detection** via content hashing
- 🤖 **Robots.txt compliance** with intelligent caching
- 💾 **Multiple export formats**: JSON, CSV, SQLite
- 📈 **Detailed statistics** and performance metrics
- 🛡️ **Error recovery** with retry logic and rate limiting

## Installation

```bash
# Clone or download the project
cd scraper

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Interactive mode
```bash
python run.py
```

### Command-line mode
```bash
# Basic usage
python run.py https://example.com

# With custom parameters
python run.py https://example.com --max-pages 1000 --max-depth 5 --format all

# All options
python run.py URL [--max-depth DEPTH] [--max-pages PAGES] [--concurrent N] 
              [--timeout SEC] [--format json|csv|sqlite|all] 
              [--output-dir DIR] [--no-robots] [--log-level LEVEL]
```

## Project Structure

```
scraper/
├── scraper/              # Main package
│   ├── core/            # Core functionality
│   │   ├── config.py    # Configuration
│   │   ├── state.py     # State management
│   │   └── crawler.py   # Main crawler
│   ├── extractors/      # Content extractors
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

## Options

- `--max-depth N`: Maximum crawl depth (default: 30)
- `--max-pages N`: Maximum pages to crawl (default: 500)
- `--concurrent N`: Number of concurrent requests (default: 50)
- `--timeout SEC`: Request timeout in seconds (default: 15)
- `--format FORMAT`: Export format: json, csv, sqlite, or all (default: json)
- `--output-dir DIR`: Output directory (default: output)
- `--no-robots`: Ignore robots.txt rules
- `--log-level LEVEL`: Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Examples

```bash
# Quick scan with default settings
python run.py https://example.com

# Deep crawl with all export formats
python run.py https://example.com --max-depth 10 --max-pages 2000 --format all

# Fast, shallow scan
python run.py https://example.com --max-depth 2 --concurrent 100

# Export to CSV only
python run.py https://example.com --format csv --output-dir reports
```

## Output

The scraper generates comprehensive reports including:
- Total pages analyzed
- Word count and statistics
- Resource counts (images, scripts, etc.)
- Response time metrics
- HTTP status code distribution
- Content type analysis
- Duplicate detection results

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scraper

# Run specific test file
pytest tests/test_extractors.py
```

## License

MIT License - Feel free to use and modify as needed.

## Version History

- **v2.0.0**: Modular architecture with advanced features
- **v1.0.0**: Initial monolithic version
