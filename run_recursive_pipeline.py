"""
ULTRACORE REAPER v3.0 - Recursive Site Correction Pipeline

Workflow:
1. Téléchargement récursif ciblé (site + ressources)
2. Correction offline des pages téléchargées
3. Génération PDF avec WeasyPrint
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from colorama import Fore, Style, init

# Direct imports to avoid circular dependencies
sys.path.insert(0, str(Path(__file__).parent))

from scraper.core.recursive_downloader import RecursiveDownloader
from scraper.core.offline_corrector import OfflineCorrector
from scraper.exporters.weasyprint_generator import WeasyPrintGenerator
from scraper.utils.logging_config import setup_logging

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
    
    # Print header
    print_header()
    
    # Get URL
    if args.url:
        target_url = args.url
    else:
        target_url = input(f"{Fore.YELLOW}🌐 Entrez l'URL de départ : {Style.RESET_ALL}").strip()
    
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    print(f"{Fore.GREEN}🎯 URL cible: {target_url}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}⚙️  Max depth: {args.max_depth}, Max pages: {args.max_pages}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}⚙️  Langue: {args.language}, Mode agressif: {args.aggressive}{Style.RESET_ALL}")
    
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
        print_phase(1, "TÉLÉCHARGEMENT RÉCURSIF")
        
        downloader = RecursiveDownloader(
            base_url=target_url,
            output_dir=str(downloaded_dir),
            max_depth=args.max_depth,
            max_pages=args.max_pages,
            timeout=args.timeout
        )
        
        print(f"{Fore.CYAN}📥 Démarrage du téléchargement récursif...{Style.RESET_ALL}")
        success = downloader.download_page(target_url)
        
        if not success:
            print(f"{Fore.RED}❌ Échec du téléchargement initial{Style.RESET_ALL}")
            return 1
        
        download_summary = downloader.get_summary()
        downloader.cleanup()
        
        print(f"\n{Fore.GREEN}✅ Téléchargement terminé{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages téléchargées: {download_summary['pages_downloaded']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Fichiers totaux: {download_summary['total_files']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Répertoire: {download_summary['output_directory']}{Style.RESET_ALL}")
        
        if download_summary['pages_downloaded'] == 0:
            print(f"{Fore.RED}❌ Aucune page téléchargée{Style.RESET_ALL}")
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
        
        print(f"{Fore.CYAN}✏️  Correction des pages téléchargées...{Style.RESET_ALL}")
        correction_summary = corrector.correct_all_pages(
            pages_list=download_summary['pages_list']
        )
        corrector.cleanup()
        
        print(f"\n{Fore.GREEN}✅ Correction terminée{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages corrigées: {correction_summary['corrected_successfully']}/{correction_summary['total_pages']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Erreurs trouvées: {correction_summary['total_errors_found']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Corrections appliquées: {correction_summary['total_corrections_applied']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Répertoire: {correction_summary['output_directory']}{Style.RESET_ALL}")
        
        # ============================================================
        # PHASE 3: PDF GENERATION
        # ============================================================
        if not args.skip_pdf:
            print_phase(3, "GÉNÉRATION PDF")
            
            pdf_generator = WeasyPrintGenerator(output_dir=str(pdf_dir))
            
            # Get corrected HTML files
            corrected_files = list(Path(corrected_dir).glob('*.html'))
            
            if not corrected_files:
                print(f"{Fore.RED}❌ Aucun fichier HTML corrigé trouvé{Style.RESET_ALL}")
                return 1
            
            print(f"{Fore.CYAN}📄 Génération PDF à partir de {len(corrected_files)} pages...{Style.RESET_ALL}")
            
            pdf_paths = []
            
            # Generate single combined PDF
            if args.pdf in ["single", "both"]:
                print(f"{Fore.CYAN}   Génération du PDF combiné...{Style.RESET_ALL}")
                combined_pdf = pdf_generator.generate_multi_page_pdf(
                    corrected_files,
                    output_name="rapport_corrections_complet.pdf"
                )
                pdf_paths.append(combined_pdf)
                print(f"{Fore.GREEN}   ✓ PDF combiné: {combined_pdf}{Style.RESET_ALL}")
            
            # Generate individual PDFs
            if args.pdf in ["individual", "both"]:
                print(f"{Fore.CYAN}   Génération des PDFs individuels...{Style.RESET_ALL}")
                individual_pdfs = pdf_generator.generate_pdfs_batch(corrected_files)
                pdf_paths.extend(individual_pdfs)
                print(f"{Fore.GREEN}   ✓ {len(individual_pdfs)} PDFs individuels générés{Style.RESET_ALL}")
            
            print(f"\n{Fore.GREEN}✅ Génération PDF terminée{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   PDFs créés: {len(pdf_paths)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Répertoire: {pdf_dir}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⏭️  Génération PDF ignorée (--skip-pdf){Style.RESET_ALL}")
        
        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        duration = time.time() - start_time
        
        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{'PIPELINE TERMINÉ AVEC SUCCÈS':^70}")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}📊 RÉSUMÉ GLOBAL{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Durée totale: {duration:.2f}s{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages téléchargées: {download_summary['pages_downloaded']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Fichiers téléchargés: {download_summary['total_files']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages corrigées: {correction_summary['corrected_successfully']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Erreurs détectées: {correction_summary['total_errors_found']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Corrections appliquées: {correction_summary['total_corrections_applied']}{Style.RESET_ALL}")
        
        if not args.skip_pdf:
            print(f"{Fore.CYAN}   PDFs générés: {len(pdf_paths)}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}📁 FICHIERS DE SORTIE{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Site téléchargé: {downloaded_dir}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Pages corrigées: {corrected_dir}{Style.RESET_ALL}")
        
        if not args.skip_pdf:
            print(f"{Fore.CYAN}   PDFs: {pdf_dir}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✨ Pipeline exécuté avec succès!{Style.RESET_ALL}\n")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Pipeline interrompu par l'utilisateur{Style.RESET_ALL}")
        return 1
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ Erreur fatale: {e}{Style.RESET_ALL}")
        logging.exception("Fatal error in pipeline")
        return 1


if __name__ == "__main__":
    sys.exit(main())
