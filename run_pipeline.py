"""
ULTRACORE REAPER v3.0 - Recursive Pipeline (Standalone)

Workflow:
1. Téléchargement récursif ciblé
2. Correction offline
3. Génération PDF
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from colorama import Fore, Style, init

# Add scraper to path
SCRAPER_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRAPER_DIR))

# Initialize colorama
init(autoreset=True)


def print_header():
    """Print banner"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{'ULTRACORE REAPER v3.0 - RECURSIVE CORRECTION PIPELINE':^70}")
    print(f"{'='*70}{Style.RESET_ALL}\n")


def print_phase(phase_number: int, phase_name: str):
    """Print phase header"""
    print(f"\n{Fore.YELLOW}{'='*70}")
    print(f"{'PHASE ' + str(phase_number) + ': ' + phase_name:^70}")
    print(f"{'='*70}{Style.RESET_ALL}\n")


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ULTRACORE REAPER v3.0 - Recursive Site Correction Pipeline"
    )
    
    # Input
    parser.add_argument("url", nargs="?", help="Starting URL to download and correct")
    
    # Download options
    parser.add_argument("--max-depth", type=int, default=10, 
                       help="Maximum recursion depth (default: 10)")
    parser.add_argument("--max-pages", type=int, default=100, 
                       help="Maximum pages to download (default: 100)")
    parser.add_argument("--timeout", type=int, default=15, 
                       help="Request timeout in seconds (default: 15)")
    
    # Correction options
    parser.add_argument("--language", default="fr", choices=["fr", "en"],
                       help="Language for correction (default: fr)")
    parser.add_argument("--aggressive", action="store_true", default=True,
                       help="Use aggressive correction mode (default: True)")
    parser.add_argument("--no-aggressive", action="store_false", dest="aggressive",
                       help="Disable aggressive correction mode")
    
    # PDF options
    parser.add_argument("--pdf", choices=["single", "individual", "both"], default="single",
                       help="PDF generation mode (default: single)")
    parser.add_argument("--skip-pdf", action="store_true",
                       help="Skip PDF generation")
    
    # Output
    parser.add_argument("--output-dir", default="output/recursive_pipeline",
                       help="Base output directory (default: output/recursive_pipeline)")
    
    # Logging
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level (default: INFO)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Import modules here to avoid circular imports
    from scraper.core.recursive_downloader import RecursiveDownloader
    from scraper.core.offline_corrector import OfflineCorrector
    from scraper.exporters.weasyprint_generator import WeasyPrintGenerator
    
    # Print header
    print_header()
    
    # Get URL
    if args.url:
        target_url = args.url
    else:
        target_url = input(f"{Fore.YELLOW}[?] Entrez l'URL de depart : {Style.RESET_ALL}").strip()
    
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    print(f"{Fore.GREEN}[*] URL cible: {target_url}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Max depth: {args.max_depth}, Max pages: {args.max_pages}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Langue: {args.language}, Mode agressif: {args.aggressive}{Style.RESET_ALL}")
    
    # Prepare directories
    base_output = Path(args.output_dir)
    downloaded_dir = base_output / "downloaded_site"
    corrected_dir = base_output / "corrected_pages"
    pdf_dir = base_output / "pdf"
    
    start_time = time.time()
    
    try:
        # ============================================================
        # PHASE 1: RECURSIVE DOWNLOAD
        # ============================================================
        print_phase(1, "TELECHARGEMENT RECURSIF")
        
        downloader = RecursiveDownloader(
            base_url=target_url,
            output_dir=str(downloaded_dir),
            max_depth=args.max_depth,
            max_pages=args.max_pages,
            timeout=args.timeout
        )
        
        print(f"{Fore.CYAN}[*] Demarrage du telechargement recursif...{Style.RESET_ALL}")
        success = downloader.download_page(target_url)
        
        if not success:
            print(f"{Fore.RED}[ERROR] Echec du telechargement initial{Style.RESET_ALL}")
            return 1
        
        download_summary = downloader.get_summary()
        downloader.cleanup()
        
        print(f"\n{Fore.GREEN}[OK] Telechargement termine{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages telechargees: {download_summary['pages_downloaded']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Fichiers totaux: {download_summary['total_files']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Repertoire: {download_summary['output_directory']}{Style.RESET_ALL}")
        
        if download_summary['pages_downloaded'] == 0:
            print(f"{Fore.RED}[ERROR] Aucune page telechargee{Style.RESET_ALL}")
            return 1
        
        # ============================================================
        # PHASE 2: OFFLINE CORRECTION
        # ============================================================
        print_phase(2, "CORRECTION OFFLINE")
        
        corrector = OfflineCorrector(
            pages_dir=str(downloaded_dir / "pages"),
            output_dir=str(corrected_dir),
            language=args.language,
            aggressive=args.aggressive
        )
        
        print(f"{Fore.CYAN}[*] Correction des pages telechargees...{Style.RESET_ALL}")
        correction_summary = corrector.correct_all_pages(
            pages_list=download_summary['pages_list']
        )
        corrector.cleanup()
        
        print(f"\n{Fore.GREEN}[OK] Correction terminee{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages corrigees: {correction_summary['corrected_successfully']}/{correction_summary['total_pages']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Erreurs trouvees: {correction_summary['total_errors_found']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Corrections appliquees: {correction_summary['total_corrections_applied']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Repertoire: {correction_summary['output_directory']}{Style.RESET_ALL}")
        
        # ============================================================
        # PHASE 3: PDF GENERATION
        # ============================================================
        if not args.skip_pdf:
            print_phase(3, "GENERATION PDF")
            
            pdf_generator = WeasyPrintGenerator(output_dir=str(pdf_dir))
            
            # Get corrected HTML files
            corrected_files = list(Path(corrected_dir).glob('*.html'))
            
            if not corrected_files:
                print(f"{Fore.RED}[ERROR] Aucun fichier HTML corrige trouve{Style.RESET_ALL}")
                return 1
            
            print(f"{Fore.CYAN}[*] Generation PDF a partir de {len(corrected_files)} pages...{Style.RESET_ALL}")
            
            pdf_paths = []
            
            # Generate single combined PDF
            if args.pdf in ["single", "both"]:
                print(f"{Fore.CYAN}   Generation du PDF combine...{Style.RESET_ALL}")
                combined_pdf = pdf_generator.generate_multi_page_pdf(
                    corrected_files,
                    output_name="rapport_corrections_complet.pdf"
                )
                pdf_paths.append(combined_pdf)
                print(f"{Fore.GREEN}   [OK] PDF combine: {combined_pdf}{Style.RESET_ALL}")
            
            # Generate individual PDFs
            if args.pdf in ["individual", "both"]:
                print(f"{Fore.CYAN}   Generation des PDFs individuels...{Style.RESET_ALL}")
                individual_pdfs = pdf_generator.generate_pdfs_batch(corrected_files)
                pdf_paths.extend(individual_pdfs)
                print(f"{Fore.GREEN}   [OK] {len(individual_pdfs)} PDFs individuels generes{Style.RESET_ALL}")
            
            print(f"\n{Fore.GREEN}[OK] Generation PDF terminee{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   PDFs crees: {len(pdf_paths)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Repertoire: {pdf_dir}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}[SKIP] Generation PDF ignoree (--skip-pdf){Style.RESET_ALL}")
        
        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        duration = time.time() - start_time
        
        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{'PIPELINE TERMINE AVEC SUCCES':^70}")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}[*] RESUME GLOBAL{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Duree totale: {duration:.2f}s{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages telechargees: {download_summary['pages_downloaded']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Fichiers telecharges: {download_summary['total_files']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages corrigees: {correction_summary['corrected_successfully']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Erreurs detectees: {correction_summary['total_errors_found']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Corrections appliquees: {correction_summary['total_corrections_applied']}{Style.RESET_ALL}")
        
        if not args.skip_pdf:
            print(f"{Fore.CYAN}   PDFs generes: {len(pdf_paths)}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}[*] FICHIERS DE SORTIE{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Site telecharge: {downloaded_dir}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages corrigees: {corrected_dir}{Style.RESET_ALL}")
        
        if not args.skip_pdf:
            print(f"{Fore.CYAN}   PDFs: {pdf_dir}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}[SUCCESS] Pipeline execute avec succes!{Style.RESET_ALL}\n")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Pipeline interrompu par l'utilisateur{Style.RESET_ALL}")
        return 1
        
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR] Erreur fatale: {e}{Style.RESET_ALL}")
        logging.exception("Fatal error in pipeline")
        return 1


if __name__ == "__main__":
    sys.exit(main())
