"""Markdown exporter with ultra-personalized formatting"""

import logging
import time
from typing import List, Dict
from datetime import datetime
from urllib.parse import urlparse


def export_markdown(state, config) -> str:
    """
    Export scraped data to ultra-personalized Markdown format.
    
    Args:
        state: CrawlerState object with results and stats
        config: Config object
        
    Returns:
        Path to created Markdown file
    """
    filename = f"{config.output_dir}/scraper_results_{int(time.time())}.md"
    
    pages = state.results
    stats = state.stats
    duration = time.time() - stats.get('start', 0)
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Header with beautiful formatting
            f.write("# 🚀 ULTRACORE REAPER v2.0\n")
            f.write("## 📊 Rapport d'Analyse Web Complet\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## 📈 Résumé Exécutif\n\n")
            duration = stats.get('duration', 0)
            f.write(f"- **Date d'analyse**: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            f.write(f"- **Durée totale**: {duration:.2f}s\n")
            f.write(f"- **Pages analysées**: {stats.get('pages', 0)}\n")
            f.write(f"- **Pages en erreur**: {stats.get('errors', 0)}\n")
            f.write(f"- **Vitesse moyenne**: {stats.get('pages', 0) / duration if duration > 0 else 0:.2f} pages/s\n")
            f.write(f"- **Mots extraits**: {stats.get('words', 0):,}\n")
            f.write(f"- **Images trouvées**: {stats.get('images', 0)}\n\n")
            
            # Performance Metrics
            if stats.get('response_times'):
                avg_time = sum(stats['response_times']) / len(stats['response_times'])
                min_time = min(stats['response_times'])
                max_time = max(stats['response_times'])
                
                f.write("### ⚡ Métriques de Performance\n\n")
                f.write(f"- **Temps de réponse moyen**: {avg_time:.3f}s\n")
                f.write(f"- **Temps minimal**: {min_time:.3f}s\n")
                f.write(f"- **Temps maximal**: {max_time:.3f}s\n\n")
            
            f.write("---\n\n")
            
            # Process each page
            for idx, page in enumerate(pages, 1):
                url = page.get('url', 'Unknown')
                parsed = urlparse(url)
                
                f.write(f"## 📄 Page {idx}: {parsed.path or '/'}\n\n")
                f.write(f"**URL complète**: [{url}]({url})\n\n")
                
                # Metadata section
                metadata = page.get('metadata', {})
                if metadata.get('title'):
                    f.write(f"### 🏷️ Métadonnées\n\n")
                    f.write(f"- **Titre**: {metadata.get('title')}\n")
                    if metadata.get('description'):
                        f.write(f"- **Description**: {metadata.get('description')}\n")
                    if metadata.get('language'):
                        f.write(f"- **Langue**: {metadata.get('language')}\n")
                    if metadata.get('author'):
                        f.write(f"- **Auteur**: {metadata.get('author')}\n")
                    f.write("\n")
                
                # Technical info
                f.write(f"### ⚙️ Informations Techniques\n\n")
                f.write(f"- **Profondeur**: Niveau {page.get('depth', 0)}\n")
                f.write(f"- **Temps de réponse**: {page.get('response_time', 0):.3f}s\n")
                f.write(f"- **Timestamp**: {page.get('timestamp', 'N/A')}\n")
                if page.get('is_duplicate'):
                    f.write(f"- ⚠️ **Contenu dupliqué détecté**\n")
                f.write("\n")
                
                # NLP Analysis (if available)
                text_data = page.get('text', {})
                if text_data.get('nlp_enabled'):
                    f.write(f"### 🧠 Analyse NLP ({text_data.get('nlp_language', 'N/A')})\n\n")
                    f.write("#### 📊 Statistiques Linguistiques\n\n")
                    f.write(f"| Métrique | Valeur |\n")
                    f.write(f"|----------|--------|\n")
                    f.write(f"| Phrases | {text_data.get('sentence_count', 0)} |\n")
                    f.write(f"| Paragraphes | {text_data.get('paragraph_count', 0)} |\n")
                    f.write(f"| Mots totaux | {text_data.get('word_count', 0):,} |\n")
                    f.write(f"| Mots uniques | {text_data.get('unique_words', 0):,} |\n")
                    f.write(f"| Richesse vocabulaire | {text_data.get('vocabulary_richness', 0):.2%} |\n")
                    f.write(f"| Score de lisibilité | {text_data.get('readability_score', 0):.1f}/100 |\n")
                    f.write(f"| Longueur moy. phrase | {text_data.get('avg_sentence_length', 0):.1f} mots |\n")
                    f.write("\n")
                    
                    # Keywords
                    keywords = text_data.get('keywords', [])
                    if keywords:
                        f.write("#### 🔑 Mots-Clés Principaux\n\n")
                        for i, kw in enumerate(keywords[:10], 1):
                            f.write(f"{i}. **{kw}**\n")
                        f.write("\n")
                    
                    # Named entities
                    entities = text_data.get('named_entities', [])
                    if entities:
                        f.write("#### 👤 Entités Nommées\n\n")
                        entity_types = {}
                        for entity in entities[:20]:
                            etype = entity.get('type', 'OTHER')
                            if etype not in entity_types:
                                entity_types[etype] = []
                            entity_types[etype].append(entity.get('text', ''))
                        
                        for etype, texts in entity_types.items():
                            f.write(f"**{etype}**: {', '.join(texts[:5])}\n\n")
                    
                    # Sample paragraphs
                    paragraphs = text_data.get('paragraphs', [])
                    if paragraphs:
                        f.write("#### 📝 Extraits de Contenu\n\n")
                        for i, para in enumerate(paragraphs[:3], 1):
                            preview = para[:300] + '...' if len(para) > 300 else para
                            f.write(f"**Paragraphe {i}**:\n> {preview}\n\n")
                
                else:
                    # Basic text stats
                    f.write(f"### 📝 Contenu Textuel\n\n")
                    f.write(f"- **Mots**: {text_data.get('word_count', 0):,}\n")
                    f.write(f"- **Caractères**: {text_data.get('char_count', 0):,}\n")
                    f.write(f"- **Phrases**: {text_data.get('sentence_count', 0)}\n")
                    f.write(f"- **Mots uniques**: {text_data.get('unique_words', 0):,}\n")
                    
                    keywords = text_data.get('keywords', [])
                    if keywords:
                        f.write(f"- **Mots-clés**: {', '.join(keywords[:8])}\n")
                    f.write("\n")
                    
                    # Sample sentences
                    sentences = text_data.get('sentences', [])
                    if sentences:
                        f.write("#### 💬 Phrases Exemples\n\n")
                        for i, sent in enumerate(sentences[:5], 1):
                            preview = sent[:150] + '...' if len(sent) > 150 else sent
                            f.write(f"{i}. {preview}\n")
                        f.write("\n")
                
                # Resources
                resources = page.get('resources', {})
                if resources:
                    f.write("### 🖼️ Ressources\n\n")
                    
                    images = resources.get('images', [])
                    if images:
                        f.write(f"#### Images ({len(images)})\n\n")
                        for img in images[:10]:
                            alt = img.get('alt', 'Sans description')
                            src = img.get('src', '')
                            f.write(f"- ![{alt}]({src})\n")
                        if len(images) > 10:
                            f.write(f"\n*...et {len(images) - 10} autres images*\n")
                        f.write("\n")
                    
                    scripts = resources.get('scripts', [])
                    if scripts:
                        f.write(f"#### Scripts ({len(scripts)})\n\n")
                        for script in scripts[:5]:
                            f.write(f"- `{script}`\n")
                        if len(scripts) > 5:
                            f.write(f"\n*...et {len(scripts) - 5} autres scripts*\n")
                        f.write("\n")
                
                # Links
                links = page.get('links', {})
                if links:
                    f.write("### 🔗 Liens\n\n")
                    f.write(f"- **Liens internes**: {links.get('internal_count', 0)}\n")
                    f.write(f"- **Liens externes**: {links.get('external_count', 0)}\n")
                    
                    ext_domains = links.get('external_domains', [])
                    if ext_domains:
                        f.write(f"- **Domaines externes**: {', '.join(ext_domains[:10])}\n")
                    f.write("\n")
                
                f.write("---\n\n")
            
            # Footer with depth distribution
            if stats.get('depths'):
                f.write("## 🌳 Distribution par Profondeur\n\n")
                f.write("| Niveau | Pages |\n")
                f.write("|--------|-------|\n")
                for depth, count in sorted(stats['depths'].items()):
                    f.write(f"| {depth} | {count} |\n")
                f.write("\n")
            
            # HTTP status codes
            if stats.get('status_codes'):
                f.write("## 📡 Codes de Statut HTTP\n\n")
                f.write("| Code | Occurrences |\n")
                f.write("|------|-------------|\n")
                for code, count in sorted(stats['status_codes'].items()):
                    f.write(f"| {code} | {count} |\n")
                f.write("\n")
            
            # Final signature
            f.write("---\n\n")
            f.write("*Rapport généré par **ULTRACORE REAPER v2.0** avec NLP avancé*\n")
            f.write(f"*🕐 {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*\n")
        
        logging.info(f"Markdown export: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Markdown export failed: {e}")
        raise
