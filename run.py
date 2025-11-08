"""
ULTRACORE REAPER v2.0 - Main Entry Point
"""

import asyncio
import aiohttp
import argparse
import sys
import os
import time
from colorama import Fore, Style, init
from tqdm import tqdm

from scraper.core import Config, CrawlerState, Crawler
from scraper.exporters import export_json, export_csv, export_sqlite
from scraper.utils import setup_logging, cleanup_fetcher, get_fetcher

# Initialize colorama
init(autoreset=True)


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
    if state.stats["depths"]:
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


async def main():
    """Main entry point"""
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
    
    # NLP options
    parser.add_argument("--nlp", action="store_true", help="Enable advanced NLP processing (NLTK/spaCy)")
    parser.add_argument("--nlp-language", default="french", choices=["french", "english"], help="NLP language")
    parser.add_argument("--nlp-spacy", action="store_true", default=True, help="Use spaCy if available")
    
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
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Config
    config = Config(
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        concurrent_tasks=args.concurrent,
        timeout=args.timeout,
        respect_robots=not args.no_robots,
        save_format=args.format,
        output_dir=args.output_dir,
        log_level=args.log_level,
        enable_nlp=args.nlp,
        nlp_language=args.nlp_language,
        nlp_use_spacy=args.nlp_spacy
    )
    
    print(f"\n{Fore.CYAN}🚀 Démarrage du scan de: {base_url}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}⚙️  Config: {config.max_pages} pages max, profondeur {config.max_depth}, {config.concurrent_tasks} tâches concurrentes{Style.RESET_ALL}")
    if config.enable_nlp:
        print(f"{Fore.GREEN}🧠 NLP activé: {config.nlp_language}, spaCy={'enabled' if config.nlp_use_spacy else 'disabled'}{Style.RESET_ALL}")
    print()
    
    # Initialize crawler
    state = CrawlerState()
    crawler = Crawler(config, state)  # config first, then state
    
    # Start crawling
    sem = asyncio.Semaphore(config.concurrent_tasks)
    headers = {'User-Agent': config.user_agent}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        with tqdm(total=config.max_pages, desc="Scan en cours", ncols=120, 
                 bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            try:
                await crawler.crawl(base_url, session, 0, sem, pbar)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Scan interrompu par l'utilisateur{Style.RESET_ALL}")
            finally:
                # Display Playwright metrics if used
                try:
                    fetcher = await get_fetcher()
                    metrics = fetcher.get_metrics()
                    if metrics['total_fetches'] > 0:
                        print(f"\n{Fore.CYAN}🎭 Playwright Metrics:{Style.RESET_ALL}")
                        print(f"  Total fetches    : {Fore.GREEN}{metrics['total_fetches']}{Style.RESET_ALL}")
                        print(f"  Cache hits       : {Fore.GREEN}{metrics['cache_hits']}{Style.RESET_ALL} ({metrics['cache_hit_rate']})")
                        print(f"  Avg fetch time   : {Fore.GREEN}{metrics['avg_time']:.2f}s{Style.RESET_ALL}")
                        print(f"  Pool size        : {Fore.GREEN}{metrics['pool_size']}{Style.RESET_ALL}")
                        print(f"  Errors           : {Fore.RED}{metrics['errors']}{Style.RESET_ALL}")
                except Exception:
                    pass  # Playwright not used
                
                # Cleanup Playwright resources
                await cleanup_fetcher()
    
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
