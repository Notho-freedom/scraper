# Pipeline Récursif de Correction - Architecture v3.0

## Vue d'ensemble

Nouveau workflow en **3 phases distinctes** pour téléchargement ciblé + correction offline + génération PDF:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: TÉLÉCHARGEMENT                      │
│           RecursiveDownloader - Clone ciblé du site             │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: CORRECTION                          │
│          OfflineCorrector - Analyse + Injection                 │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: PDF                                 │
│            WeasyPrintGenerator - HTML → PDF                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Téléchargement Récursif Ciblé

### Module: `RecursiveDownloader`

**Rôle**: Télécharger une page et toutes ses pages liées (même domaine) avec leurs ressources

```python
from scraper.core.recursive_downloader import RecursiveDownloader

downloader = RecursiveDownloader(
    base_url="https://multi-tess-sarl.vercel.app",
    output_dir="output/downloaded_site",
    max_depth=10,      # Profondeur maximale de récursion
    max_pages=100,     # Nombre maximum de pages
    timeout=15         # Timeout par requête
)

# Lance le téléchargement récursif
success = downloader.download_page("https://multi-tess-sarl.vercel.app")

# Récupère le résumé
summary = downloader.get_summary()
print(f"Pages téléchargées: {summary['pages_downloaded']}")
print(f"Fichiers totaux: {summary['total_files']}")

downloader.cleanup()
```

### Fonctionnement

1. **Téléchargement initial**: Page de départ + ressources (CSS, JS, images)
2. **Extraction liens**: Parse HTML, identifie tous les liens internes (même domaine)
3. **Récursion**: Pour chaque lien interne non visité → re-télécharge récursivement
4. **Cache**: Évite re-téléchargement des URLs déjà visitées
5. **Réécriture**: Convertit tous les liens vers chemins locaux relatifs

### Structure de sortie

```
output/downloaded_site/
├── pages/
│   ├── index.html
│   ├── about.html
│   └── contact.html
└── assets/
    ├── css/
    │   ├── main.css
    │   └── style.css
    ├── js/
    │   └── bundle.js
    └── images/
        ├── logo.png
        └── banner.jpg
```

### Avantages

✅ **Ciblé**: Télécharge uniquement les pages liées (pas tout le domaine)  
✅ **Complet**: Si les liens mènent au site entier → télécharge tout naturellement  
✅ **Efficace**: Cache pour éviter doublons  
✅ **Prêt pour offline**: Chemins relatifs pour navigation locale  

---

## Phase 2: Correction Offline

### Module: `OfflineCorrector`

**Rôle**: Parcourir les pages téléchargées, détecter erreurs, injecter corrections

```python
from scraper.core.offline_corrector import OfflineCorrector

corrector = OfflineCorrector(
    pages_dir="output/downloaded_site/pages",
    output_dir="output/corrected_pages",
    language="fr",
    aggressive=True  # Mode agressif (seuil confiance 50%)
)

# Corriger toutes les pages
summary = corrector.correct_all_pages(
    pages_list=download_summary['pages_list']  # Ordre de téléchargement
)

print(f"Pages corrigées: {summary['corrected_successfully']}")
print(f"Erreurs trouvées: {summary['total_errors_found']}")
print(f"Corrections appliquées: {summary['total_corrections_applied']}")

corrector.cleanup()
```

### Fonctionnement

1. **Extraction texte**: Parse HTML, extrait texte via BeautifulSoup
2. **Analyse**: GrammarChecker détecte erreurs grammaticales/orthographe
3. **Correction**: TextCorrector applique corrections (mode agressif = seuil 50%)
4. **Injection HTML**: HTMLReconstructor insère `<del>`/`<ins>` dans le HTML original
5. **Légende**: Ajoute explication visuelle des corrections en haut de page
6. **Sauvegarde**: Génère fichiers HTML corrigés

### Format des corrections

```html
<!-- Original -->
<p>Nous sommes une entreprise spécialisé dans...</p>

<!-- Après correction -->
<p>Nous sommes une entreprise 
<del style="text-decoration:line-through;color:#dc3545;background:#f8d7da;">spécialisé</del>
<ins style="color:#28a745;background:#d4edda;font-weight:500;">spécialisée</ins>
 dans...</p>
```

### Avantages

✅ **100% backend**: Pas de dépendance externe (WebCopy, etc.)  
✅ **Préserve structure**: HTML original conservé, seules corrections injectées  
✅ **Mode agressif**: Détecte plus d'erreurs (confiance ≥50%)  
✅ **Traçabilité**: Chaque correction documentée avec confiance, position, type  

---

## Phase 3: Génération PDF

### Module: `WeasyPrintGenerator`

**Rôle**: Convertir HTML corrigé en PDF professionnel

```python
from scraper.exporters.weasyprint_generator import WeasyPrintGenerator
from pathlib import Path

pdf_generator = WeasyPrintGenerator(output_dir="output/pdf")

# Récupérer les fichiers HTML corrigés
corrected_files = list(Path("output/corrected_pages").glob('*.html'))

# Option 1: PDF combiné (toutes les pages en un seul PDF)
combined_pdf = pdf_generator.generate_multi_page_pdf(
    corrected_files,
    output_name="rapport_corrections_complet.pdf"
)

# Option 2: PDFs individuels
individual_pdfs = pdf_generator.generate_pdfs_batch(corrected_files)

# Option 3: PDF d'une seule page
single_pdf = pdf_generator.generate_single_pdf(
    corrected_files[0],
    output_name="page_index.pdf"
)
```

### Fonctionnement

1. **Parsing HTML**: WeasyPrint parse le HTML corrigé
2. **Rendu CSS**: Applique styles originaux + styles de correction
3. **Formatage PDF**: A4, marges 2cm, pagination, headers/footers
4. **Préservation**: `<del>`/`<ins>` visibles avec couleurs rouge/vert
5. **Export**: PDF final avec toutes corrections visibles

### CSS personnalisé

- **Format A4** avec marges 2cm
- **Corrections visibles**:
  - `<del>`: Texte barré rouge (#dc3545) sur fond rose (#f8d7da)
  - `<ins>`: Texte vert (#28a745) sur fond vert clair (#d4edda)
- **Pagination automatique**: "Page X of Y" en footer
- **Header**: "Site Correction Report" en top
- **Gestion breaks**: Évite coupures au milieu de corrections

### Avantages

✅ **Professionnel**: PDF formaté, paginé, avec headers/footers  
✅ **Corrections visibles**: Couleurs préservées (rouge/vert)  
✅ **Flexible**: PDF combiné OU individuels OU les deux  
✅ **Prêt distribution**: Envoyable aux clients tel quel  

---

## Utilisation du Pipeline Complet

### Script principal: `run_recursive_pipeline.py`

```bash
# Exécution basique
python run_recursive_pipeline.py https://multi-tess-sarl.vercel.app

# Options avancées
python run_recursive_pipeline.py https://example.com \
  --max-depth 15 \
  --max-pages 200 \
  --language fr \
  --aggressive \
  --pdf both \
  --output-dir output/mon_projet
```

### Options disponibles

```
Téléchargement:
  --max-depth N        Profondeur maximale récursion (défaut: 10)
  --max-pages N        Nombre max de pages (défaut: 100)
  --timeout N          Timeout par requête (défaut: 15s)

Correction:
  --language fr|en     Langue pour correction (défaut: fr)
  --aggressive         Mode agressif activé (défaut)
  --no-aggressive      Mode agressif désactivé

PDF:
  --pdf single         PDF combiné uniquement (défaut)
  --pdf individual     PDFs individuels uniquement
  --pdf both           PDF combiné + PDFs individuels
  --skip-pdf           Pas de génération PDF

Sortie:
  --output-dir DIR     Répertoire de sortie
  --log-level LEVEL    DEBUG|INFO|WARNING|ERROR
```

### Exemple complet

```bash
# Télécharger Multi-Tess (max 50 pages, profondeur 5)
# Corriger en mode agressif
# Générer PDF combiné + individuels
python run_recursive_pipeline.py https://multi-tess-sarl.vercel.app \
  --max-pages 50 \
  --max-depth 5 \
  --aggressive \
  --pdf both \
  --output-dir output/multi_tess_corrections
```

### Structure de sortie finale

```
output/multi_tess_corrections/
├── downloaded_site/
│   ├── pages/
│   │   ├── index.html
│   │   ├── services.html
│   │   └── contact.html
│   └── assets/
│       ├── css/
│       ├── js/
│       └── images/
├── corrected_pages/
│   ├── index.html (avec corrections <del>/<ins>)
│   ├── services.html
│   └── contact.html
└── pdf/
    ├── rapport_corrections_complet.pdf  (toutes pages)
    ├── index.pdf
    ├── services.pdf
    └── contact.pdf
```

---

## Comparaison: Ancien vs Nouveau Workflow

| Aspect | Ancien (v2.0) | Nouveau (v3.0) |
|--------|---------------|----------------|
| **Téléchargement** | Crawl complet du domaine | Téléchargement récursif ciblé |
| **Ressources** | URL resolution (absolues) | Téléchargement local + chemins relatifs |
| **Correction** | En ligne pendant crawl | Offline après téléchargement |
| **Séparation** | Couplé (crawl + correction) | Modulaire (3 phases distinctes) |
| **Contrôle** | Concurrent, complexe | Séquentiel, simple |
| **PDF** | Template custom | WeasyPrint (HTML → PDF direct) |
| **Offline** | Non (besoin internet pour CSS/JS) | Oui (tout téléchargé localement) |

---

## Avantages du nouveau workflow

### 1. **Séparation des responsabilités**

Chaque phase est indépendante:
- Téléchargement ≠ Correction ≠ PDF
- Peut exécuter chaque phase séparément si besoin
- Facilite debug et maintenance

### 2. **Téléchargement ciblé intelligent**

- Commence par la page demandée
- Suit uniquement les liens internes
- Si ça mène au site entier → télécharge tout naturellement
- Sinon → télécharge seulement ce qui est lié

### 3. **Correction offline robuste**

- Pas de contraintes de temps (pas de timeout réseau)
- Peut re-corriger sans re-télécharger
- Backend 100% maîtrisé (pas de dépendance WebCopy)

### 4. **PDF professionnel**

- WeasyPrint = rendu HTML fidèle en PDF
- Styles CSS préservés
- Corrections visibles (rouge/vert)
- Format publication ready

### 5. **Workflow distribué**

1. **Client**: Télécharge site → envoie à serveur
2. **Serveur**: Corrige pages téléchargées → génère PDF
3. **Client**: Reçoit PDF final

---

## Tests

### Test unitaire

```bash
# Test avec page locale
python tests/test_recursive_pipeline.py
```

### Test complet sur site réel

```bash
# Test Multi-Tess (limité à 10 pages)
python run_recursive_pipeline.py https://multi-tess-sarl.vercel.app \
  --max-pages 10 \
  --max-depth 3 \
  --pdf both \
  --output-dir output/test_multi_tess
```

---

## Prochaines étapes

- [ ] Tester sur vrai site Multi-Tess (download complet)
- [ ] Optimiser matching corrections → HTML (problème 1/26 injections)
- [ ] Ajouter support multi-langue (détection auto)
- [ ] Compression PDF (réduire taille fichiers)
- [ ] Interface CLI interactive (TUI avec Rich)
- [ ] Support assets externes (CDN, Google Fonts, etc.)

---

## Fichiers créés

```
scraper/core/recursive_downloader.py      (340 lignes)
scraper/core/offline_corrector.py         (210 lignes)
scraper/exporters/weasyprint_generator.py (360 lignes)
run_recursive_pipeline.py                 (245 lignes)
tests/test_recursive_pipeline.py          (130 lignes)
```

**Total**: ~1,285 lignes de nouveau code pour le pipeline v3.0

---

## Performance estimée

| Tâche | Temps (10 pages) | Temps (100 pages) |
|-------|------------------|-------------------|
| Téléchargement | ~30s | ~5min |
| Correction | ~2min | ~20min |
| PDF (combiné) | ~5s | ~30s |
| **TOTAL** | **~2.5min** | **~25min** |

Note: Temps dépend de:
- Taille des pages
- Nombre de ressources (CSS/JS/images)
- Vitesse réseau
- Nombre d'erreurs grammaticales
