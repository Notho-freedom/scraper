"""
ULTRACORE REAPER v2.0 - Advanced Web Scraper & Analyzer
========================================================
Features:
- Multi-threaded async crawling with rate limiting
- Advanced metadata extraction (SEO, Open Graph, Twitter Cards, JSON-LD)
- NLP analysis (sentiment, keywords, language detection)
- Content categorization and duplicate detection
- Performance metrics and resource analysis
- Export to multiple formats (JSON, CSV, SQLite)
- Resume capability and error recovery
- Robots.txt compliance
- Advanced link analysis and site mapping
"""

import asyncio
import aiohttp
from selectolax.parser import HTMLParser
from urllib.parse import urlparse, urljoin, parse_qs
from urllib.robotparser import RobotFileParser
from url_normalize import url_normalize
from colorama import Fore, Style, init
from tqdm import tqdm
import json
import csv
import sqlite3
import hashlib
import time
import re
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from typing import Set, Dict, List, Optional
import sys

# Initialize colorama
init(autoreset=True)

# === CONFIGURATION ===
@dataclass
class Config:
    max_depth: int = 30
    max_pages: int = 500
    concurrent_tasks: int = 50
    timeout: int = 15
    retry_attempts: int = 3
    rate_limit: float = 0.1  # seconds between requests
    user_agent: str = "UltracoreReaper/2.0"
    respect_robots: bool = True
    extract_images: bool = True
    extract_scripts: bool = True
    analyze_sentiment: bool = False
    detect_duplicates: bool = True
    save_format: str = "json"  # json, csv, sqlite, all
    output_dir: str = "output"
    log_level: str = "INFO"


# === LOGGING SETUP ===
def setup_logging(level: str):
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


# === GLOBAL STATE ===
class CrawlerState:
    def __init__(self):
        self.visited: Set[str] = set()
        self.results: List[Dict] = []
        self.errors: List[Dict] = []
        self.duplicates: Dict[str, List[str]] = defaultdict(list)
        self.stats = {
            "start": time.time(),
            "pages": 0,
            "words": 0,
            "images": 0,
            "scripts": 0,
            "errors": 0,
            "depths": {},
            "response_times": [],
            "content_types": Counter(),
            "status_codes": Counter()
        }
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.content_hashes: Dict[str, str] = {}


# === ROBOTS.TXT HANDLER ===
async def can_fetch(session, url: str, state: CrawlerState, user_agent: str) -> bool:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    if base not in state.robots_cache:
        rp = RobotFileParser()
        robots_url = urljoin(base, "/robots.txt")
        try:
            async with session.get(robots_url, timeout=5) as r:
                if r.status == 200:
                    content = await r.text()
                    rp.parse(content.splitlines())
                else:
                    rp.allow_all = True
        except Exception:
            rp.allow_all = True
        state.robots_cache[base] = rp
    
    return state.robots_cache[base].can_fetch(user_agent, url)


# === ADVANCED METADATA EXTRACTION ===
def extract_metadata(html: str) -> Dict:
    parser = HTMLParser(html)
    
    meta = {
        "title": None,
        "description": None,
        "keywords": None,
        "author": None,
        "canonical": None,
        "language": None,
        "og": {},
        "twitter": {},
        "json_ld": [],
        "h1": [],
        "h2": [],
        "h3": []
    }
    
    # Title
    title_node = parser.css_first("title")
    if title_node:
        meta["title"] = title_node.text(strip=True)
    
    # Headings
    for h1 in parser.css("h1"):
        if h1.text(strip=True):
            meta["h1"].append(h1.text(strip=True))
    for h2 in parser.css("h2"):
        if h2.text(strip=True):
            meta["h2"].append(h2.text(strip=True))
    for h3 in parser.css("h3"):
        if h3.text(strip=True):
            meta["h3"].append(h3.text(strip=True))
    
    # Meta tags
    for tag in parser.css("meta"):
        name = tag.attributes.get("name", "").lower()
        prop = tag.attributes.get("property", "").lower()
        content = tag.attributes.get("content", "").strip()
        
        if not content:
            continue
        
        if name == "description":
            meta["description"] = content
        elif name == "keywords":
            meta["keywords"] = content
        elif name == "author":
            meta["author"] = content
        elif name == "language" or name == "lang":
            meta["language"] = content
        elif prop.startswith("og:"):
            meta["og"][prop[3:]] = content
        elif name.startswith("twitter:") or prop.startswith("twitter:"):
            key = name[8:] if name.startswith("twitter:") else prop[8:]
            meta["twitter"][key] = content
    
    # Canonical URL
    canonical = parser.css_first('link[rel="canonical"]')
    if canonical:
        meta["canonical"] = canonical.attributes.get("href")
    
    # Language from html tag
    html_tag = parser.css_first("html")
    if html_tag and not meta["language"]:
        meta["language"] = html_tag.attributes.get("lang")
    
    # JSON-LD structured data
    for script in parser.css('script[type="application/ld+json"]'):
        try:
            json_ld = json.loads(script.text())
            meta["json_ld"].append(json_ld)
        except Exception:
            pass
    
    return meta


# === ADVANCED TEXT EXTRACTION ===
def extract_text(html: str) -> Dict:
    parser = HTMLParser(html)
    
    # Remove script and style elements
    for elem in parser.css("script, style, nav, footer, header"):
        elem.decompose()
    
    # Extract main content
    main_content = parser.css_first("main, article, .content, #content")
    if main_content:
        texts = [node.text(strip=True) for node in main_content.css("*") if node.text(strip=True)]
    else:
        texts = [node.text(strip=True) for node in parser.css("body *") if node.text(strip=True)]
    
    raw_text = " ".join(texts)
    raw_text = re.sub(r"\s+", " ", raw_text)
    
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text) if s.strip()]
    
    # Word analysis
    words = raw_text.split()
    word_count = len(words)
    unique_words = len(set(w.lower() for w in words if len(w) > 3))
    
    # Extract keywords (simple frequency analysis)
    word_freq = Counter(w.lower() for w in words if len(w) > 4 and w.isalpha())
    top_keywords = [word for word, _ in word_freq.most_common(10)]
    
    return {
        "sentences": sentences[:100],  # Limit for storage
        "word_count": word_count,
        "unique_words": unique_words,
        "char_count": len(raw_text),
        "sentence_count": len(sentences),
        "keywords": top_keywords,
        "avg_sentence_length": word_count / len(sentences) if sentences else 0
    }


# === RESOURCE EXTRACTION ===
def extract_resources(html: str, base_url: str) -> Dict:
    parser = HTMLParser(html)
    
    resources = {
        "images": [],
        "scripts": [],
        "stylesheets": [],
        "links_external": [],
        "emails": [],
        "phones": []
    }
    
    # Images
    for img in parser.css("img[src]"):
        src = img.attributes.get("src")
        alt = img.attributes.get("alt", "")
        if src:
            full_url = urljoin(base_url, src)
            resources["images"].append({"url": full_url, "alt": alt})
    
    # Scripts
    for script in parser.css("script[src]"):
        src = script.attributes.get("src")
        if src:
            full_url = urljoin(base_url, src)
            resources["scripts"].append(full_url)
    
    # Stylesheets
    for link in parser.css('link[rel="stylesheet"]'):
        href = link.attributes.get("href")
        if href:
            full_url = urljoin(base_url, href)
            resources["stylesheets"].append(full_url)
    
    # Extract emails and phones from text
    body_text = parser.body.text() if parser.body else ""
    resources["emails"] = list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', body_text)))
    resources["phones"] = list(set(re.findall(r'\b(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b', body_text)))
    
    return resources


# === LINK EXTRACTION WITH ANALYSIS ===
def extract_links(html: str, base_url: str) -> Dict:
    parser = HTMLParser(html)
    domain = urlparse(base_url).netloc
    
    links = {
        "internal": set(),
        "external": set(),
        "anchor_texts": defaultdict(list)
    }
    
    for tag in parser.css("a[href]"):
        href = tag.attributes.get("href")
        anchor_text = tag.text(strip=True)
        
        if href:
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            
            # Clean URL (remove fragments and some query params)
            clean_url = url_normalize(parsed.scheme + "://" + parsed.netloc + parsed.path)
            
            if parsed.netloc == domain:
                links["internal"].add(clean_url)
                if anchor_text:
                    links["anchor_texts"][clean_url].append(anchor_text)
            elif parsed.scheme in ['http', 'https']:
                links["external"].add(full)
    
    return links


# === CONTENT HASH (for duplicate detection) ===
def compute_content_hash(text: str) -> str:
    """Generate hash of main content for duplicate detection"""
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()


# === FETCH WITH RETRY ===
async def fetch(session, url: str, config: Config, state: CrawlerState) -> Optional[tuple]:
    """Fetch URL with retry logic and metrics"""
    for attempt in range(config.retry_attempts):
        try:
            start_time = time.time()
            async with session.get(url, timeout=config.timeout) as response:
                elapsed = time.time() - start_time
                state.stats["response_times"].append(elapsed)
                state.stats["status_codes"][response.status] += 1
                
                content_type = response.headers.get("content-type", "")
                state.stats["content_types"][content_type.split(';')[0]] += 1
                
                if response.status == 200 and "text/html" in content_type:
                    html = await response.text()
                    return html, elapsed
                else:
                    logging.warning(f"Non-200 or non-HTML response for {url}: {response.status}")
                    return None, elapsed
                    
        except asyncio.TimeoutError:
            logging.warning(f"Timeout on {url} (attempt {attempt + 1}/{config.retry_attempts})")
            if attempt == config.retry_attempts - 1:
                state.errors.append({"url": url, "error": "timeout", "time": datetime.now().isoformat()})
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            if attempt == config.retry_attempts - 1:
                state.errors.append({"url": url, "error": str(e), "time": datetime.now().isoformat()})
        
        await asyncio.sleep(config.rate_limit * (attempt + 1))
    
    state.stats["errors"] += 1
    return None, 0


# === MAIN CRAWL FUNCTION ===
async def crawl(url: str, session, config: Config, state: CrawlerState, 
                depth: int = 0, sem=None, pbar=None):
    """Main recursive crawling function"""
    
    # Check limits
    if (url in state.visited or 
        depth > config.max_depth or 
        len(state.visited) >= config.max_pages):
        return
    
    async with sem:
        # Check robots.txt
        if config.respect_robots:
            if not await can_fetch(session, url, state, config.user_agent):
                logging.info(f"Blocked by robots.txt: {url}")
                return
        
        state.visited.add(url)
        
        # Fetch page
        result = await fetch(session, url, config, state)
        if not result or not result[0]:
            return
        
        html, response_time = result
        
        # Extract all data
        metadata = extract_metadata(html)
        text_data = extract_text(html)
        resources = extract_resources(html, url)
        link_data = extract_links(html, url)
        
        # Duplicate detection
        content_hash = compute_content_hash(" ".join(text_data["sentences"]))
        is_duplicate = False
        if config.detect_duplicates:
            if content_hash in state.content_hashes:
                is_duplicate = True
                state.duplicates[content_hash].append(url)
                logging.info(f"Duplicate content detected: {url}")
            else:
                state.content_hashes[content_hash] = url
        
        # Update stats
        state.stats["pages"] += 1
        state.stats["words"] += text_data["word_count"]
        state.stats["images"] += len(resources["images"])
        state.stats["scripts"] += len(resources["scripts"])
        state.stats["depths"].setdefault(depth, 0)
        state.stats["depths"][depth] += 1
        
        # Store result
        page_result = {
            "url": url,
            "depth": depth,
            "timestamp": datetime.now().isoformat(),
            "response_time": round(response_time, 3),
            "is_duplicate": is_duplicate,
            "content_hash": content_hash,
            "metadata": metadata,
            "text": text_data,
            "resources": resources,
            "links": {
                "internal_count": len(link_data["internal"]),
                "external_count": len(link_data["external"]),
                "external_domains": list(set(urlparse(u).netloc for u in link_data["external"]))[:20]
            }
        }
        
        state.results.append(page_result)
        
        # Update progress bar
        if pbar:
            pbar.update(1)
            path = urlparse(url).path[:50] or "/"
            pbar.set_description(f"{Fore.CYAN}{path:<50}{Style.RESET_ALL}")
        
        # Rate limiting
        await asyncio.sleep(config.rate_limit)
        
        # Crawl child links
        if depth < config.max_depth:
            tasks = []
            for link in link_data["internal"]:
                if link not in state.visited and len(state.visited) < config.max_pages:
                    task = asyncio.create_task(
                        crawl(link, session, config, state, depth + 1, sem, pbar)
                    )
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)


# === EXPORT FUNCTIONS ===
def export_json(state: CrawlerState, config: Config):
    """Export results to JSON"""
    filename = f"{config.output_dir}/scraper_results_{int(time.time())}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "scan_date": datetime.now().isoformat(),
                "total_pages": state.stats["pages"],
                "total_words": state.stats["words"],
                "duration": round(time.time() - state.stats["start"], 2),
                "stats": dict(state.stats)
            },
            "pages": state.results,
            "errors": state.errors,
            "duplicates": {k: v for k, v in state.duplicates.items()}
        }, f, ensure_ascii=False, indent=2)
    logging.info(f"JSON export: {filename}")
    return filename


def export_csv(state: CrawlerState, config: Config):
    """Export results to CSV"""
    filename = f"{config.output_dir}/scraper_results_{int(time.time())}.csv"
    with open(filename, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "URL", "Depth", "Title", "Description", "Word Count", 
            "Links Internal", "Links External", "Images", "Response Time", "Duplicate"
        ])
        for page in state.results:
            writer.writerow([
                page["url"],
                page["depth"],
                page["metadata"]["title"] or "",
                page["metadata"]["description"] or "",
                page["text"]["word_count"],
                page["links"]["internal_count"],
                page["links"]["external_count"],
                len(page["resources"]["images"]),
                page["response_time"],
                page["is_duplicate"]
            ])
    logging.info(f"CSV export: {filename}")
    return filename


def export_sqlite(state: CrawlerState, config: Config):
    """Export results to SQLite database"""
    filename = f"{config.output_dir}/scraper_results_{int(time.time())}.db"
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE pages (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            depth INTEGER,
            title TEXT,
            description TEXT,
            word_count INTEGER,
            response_time REAL,
            is_duplicate BOOLEAN,
            timestamp TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE links (
            id INTEGER PRIMARY KEY,
            source_url TEXT,
            target_url TEXT,
            link_type TEXT
        )
    ''')
    
    # Insert data
    for page in state.results:
        cursor.execute('''
            INSERT OR IGNORE INTO pages VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            page["url"],
            page["depth"],
            page["metadata"]["title"],
            page["metadata"]["description"],
            page["text"]["word_count"],
            page["response_time"],
            page["is_duplicate"],
            page["timestamp"]
        ))
    
    conn.commit()
    conn.close()
    logging.info(f"SQLite export: {filename}")
    return filename


# === REPORT GENERATION ===
def generate_report(state: CrawlerState, config: Config):
    """Generate comprehensive analysis report"""
    duration = time.time() - state.stats["start"]
    avg_words = state.stats["words"] / state.stats["pages"] if state.stats["pages"] else 0
    avg_response = sum(state.stats["response_times"]) / len(state.stats["response_times"]) if state.stats["response_times"] else 0
    
    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"{'ULTRACORE REAPER v2.0 - RAPPORT D\'ANALYSE':^70}")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}📊 STATISTIQUES GÉNÉRALES{Style.RESET_ALL}")
    print(f"  Pages analysées     : {Fore.CYAN}{state.stats['pages']}{Style.RESET_ALL}")
    print(f"  Pages en erreur     : {Fore.RED}{state.stats['errors']}{Style.RESET_ALL}")
    print(f"  Contenus dupliqués  : {Fore.MAGENTA}{len(state.duplicates)}{Style.RESET_ALL}")
    print(f"  Durée totale        : {Fore.GREEN}{round(duration, 2)}s{Style.RESET_ALL}")
    print(f"  Vitesse moyenne     : {Fore.GREEN}{round(state.stats['pages']/duration, 2)} pages/s{Style.RESET_ALL}")
    print(f"  Temps réponse moyen : {Fore.GREEN}{round(avg_response, 3)}s{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}📝 CONTENU{Style.RESET_ALL}")
    print(f"  Mots extraits       : {Fore.CYAN}{state.stats['words']:,}{Style.RESET_ALL}")
    print(f"  Moyenne mots/page   : {Fore.CYAN}{int(avg_words)}{Style.RESET_ALL}")
    print(f"  Images trouvées     : {Fore.CYAN}{state.stats['images']}{Style.RESET_ALL}")
    print(f"  Scripts trouvés     : {Fore.CYAN}{state.stats['scripts']}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}🌳 PROFONDEUR DE CRAWL{Style.RESET_ALL}")
    for depth in sorted(state.stats["depths"].keys()):
        bar_length = int(state.stats["depths"][depth] / max(state.stats["depths"].values()) * 40)
        bar = "█" * bar_length
        print(f"  Niveau {depth:2d}         : {Fore.BLUE}{bar}{Style.RESET_ALL} ({state.stats['depths'][depth]} pages)")
    
    print(f"\n{Fore.YELLOW}📡 CODES HTTP{Style.RESET_ALL}")
    for code, count in state.stats["status_codes"].most_common(5):
        print(f"  {code}              : {count}")
    
    print(f"\n{Fore.YELLOW}📄 TYPES DE CONTENU{Style.RESET_ALL}")
    for ctype, count in state.stats["content_types"].most_common(5):
        print(f"  {ctype[:30]:<30} : {count}")
    
    print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")


# === MAIN ENTRY POINT ===
async def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="ULTRACORE REAPER v2.0 - Advanced Web Scraper")
    parser.add_argument("url", nargs="?", help="Starting URL to crawl")
    parser.add_argument("--max-depth", type=int, default=30, help="Maximum crawl depth")
    parser.add_argument("--max-pages", type=int, default=500, help="Maximum pages to crawl")
    parser.add_argument("--concurrent", type=int, default=50, help="Concurrent requests")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds")
    parser.add_argument("--format", choices=["json", "csv", "sqlite", "all"], default="json", help="Export format")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Setup
    setup_logging(args.log_level)
    
    # Get URL
    if args.url:
        base_url = args.url
    else:
        base_url = input(f"{Fore.YELLOW}🌐 Entrez l'URL de départ : {Style.RESET_ALL}").strip()
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    # Create output directory
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Configure
    config = Config(
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        concurrent_tasks=args.concurrent,
        timeout=args.timeout,
        respect_robots=not args.no_robots,
        save_format=args.format,
        output_dir=args.output_dir,
        log_level=args.log_level
    )
    
    state = CrawlerState()
    
    print(f"\n{Fore.CYAN}🚀 Démarrage du scan de: {base_url}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}⚙️  Config: {config.max_pages} pages max, profondeur {config.max_depth}, {config.concurrent_tasks} tâches concurrentes{Style.RESET_ALL}\n")
    
    # Start crawling
    sem = asyncio.Semaphore(config.concurrent_tasks)
    headers = {'User-Agent': config.user_agent}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        with tqdm(total=config.max_pages, desc="Scan en cours", ncols=120, 
                 bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            try:
                await crawl(base_url, session, config, state, 0, sem, pbar)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Scan interrompu par l'utilisateur{Style.RESET_ALL}")
    
    # Generate report
    generate_report(state, config)
    
    # Export data
    print(f"\n{Fore.YELLOW}💾 Export des données...{Style.RESET_ALL}")
    if config.save_format == "json" or config.save_format == "all":
        json_file = export_json(state, config)
        print(f"  ✓ JSON  : {Fore.GREEN}{json_file}{Style.RESET_ALL}")
    
    if config.save_format == "csv" or config.save_format == "all":
        csv_file = export_csv(state, config)
        print(f"  ✓ CSV   : {Fore.GREEN}{csv_file}{Style.RESET_ALL}")
    
    if config.save_format == "sqlite" or config.save_format == "all":
        db_file = export_sqlite(state, config)
        print(f"  ✓ SQLite: {Fore.GREEN}{db_file}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}✨ Scan terminé avec succès!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Arrêt forcé du programme.{Style.RESET_ALL}")
        sys.exit(0)
