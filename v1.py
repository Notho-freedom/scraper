import asyncio
import aiohttp
from selectolax.parser import HTMLParser
from urllib.parse import urlparse, urljoin
from url_normalize import url_normalize
from colorama import Fore, Style
from tqdm import tqdm
import json
import time
import re

# === CONFIG ===
MAX_DEPTH = 30
MAX_PAGES = 500
CONCURRENT_TASKS = 100
SAVE_FILE = "reaper_index_meta.json"

visited = set()
results = []
stats = {"start": time.time(), "pages": 0, "words": 0, "depths": {}}


# --- FETCH ---
async def fetch(session, url):
    try:
        async with session.get(url, timeout=10) as r:
            if r.status == 200 and "text/html" in r.headers.get("content-type", ""):
                return await r.text()
    except Exception:
        pass
    return None


# --- META EXTRACTION ---
def extract_metadata(html):
    parser = HTMLParser(html)

    # Métadonnées principales
    meta = {
        "title": None,
        "description": None,
        "keywords": None,
        "og": {},
        "twitter": {}
    }

    # Balise title
    title_node = parser.css_first("title")
    if title_node:
        meta["title"] = title_node.text(strip=True)

    # Balises meta classiques
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
        elif prop.startswith("og:"):
            meta["og"][prop[3:]] = content
        elif prop.startswith("twitter:"):
            meta["twitter"][prop[8:]] = content

    return meta


# --- TEXT EXTRACTION ---
def extract_text(html):
    parser = HTMLParser(html)
    texts = [node.text(strip=True) for node in parser.css("body *") if node.text(strip=True)]
    raw_text = " ".join(texts)
    raw_text = re.sub(r"\s+", " ", raw_text)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', raw_text) if s.strip()]
    return sentences


# --- LINK EXTRACTION ---
def extract_links(html, base_url):
    parser = HTMLParser(html)
    domain = urlparse(base_url).netloc
    links = set()
    for tag in parser.css("a[href]"):
        href = tag.attributes.get("href")
        if href:
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            if parsed.netloc == domain:
                norm = url_normalize(parsed.scheme + "://" + parsed.netloc + parsed.path)
                links.add(norm)
    return links


# --- CRAWL ---
async def crawl(url, session, depth=0, sem=None, pbar=None):
    if url in visited or depth > MAX_DEPTH or len(visited) >= MAX_PAGES:
        return

    async with sem:
        visited.add(url)
        html = await fetch(session, url)
        if not html:
            return

        # Analyse du contenu
        meta = extract_metadata(html)
        sentences = extract_text(html)
        word_count = sum(len(s.split()) for s in sentences)

        stats["pages"] += 1
        stats["words"] += word_count
        stats["depths"].setdefault(depth, 0)
        stats["depths"][depth] += 1

        # Enregistrement du résultat
        results.append({
            "url": url,
            "depth": depth,
            "metadata": meta,
            "words": word_count,
            "sentences": sentences[:50]  # aperçu
        })

        if pbar:
            pbar.update(1)
            path = urlparse(url).path[:40]
            pbar.set_description(f"{Fore.CYAN}{path:<40}{Style.RESET_ALL}")

        # Crawl récursif
        tasks = []
        for link in extract_links(html, url):
            if link not in visited:
                tasks.append(asyncio.create_task(crawl(link, session, depth + 1, sem, pbar)))
        if tasks:
            await asyncio.gather(*tasks)


# --- MAIN ---
async def main():
    base_url = input(Fore.YELLOW + "Entrez l'URL de départ : " + Style.RESET_ALL).strip()
    sem = asyncio.Semaphore(CONCURRENT_TASKS)

    async with aiohttp.ClientSession() as session:
        with tqdm(total=MAX_PAGES, desc="Scan en cours", ncols=100) as pbar:
            await crawl(base_url, session, 0, sem, pbar)

    duration = time.time() - stats["start"]
    avg_words = stats["words"] / stats["pages"] if stats["pages"] else 0

    print(Fore.GREEN + "\n===== RAPPORT ULTRACORE META++ =====" + Style.RESET_ALL)
    print(f"Pages analysées : {stats['pages']}")
    print(f"Mots extraits : {stats['words']}")
    print(f"Moyenne mots/page : {int(avg_words)}")
    print(f"Durée totale : {round(duration, 2)}s")
    print(f"Vitesse : {round(stats['pages']/duration, 2)} pages/s")
    print(f"Répartition par profondeur : {stats['depths']}")

    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(Fore.BLUE + f"\nRésultats sauvegardés → {SAVE_FILE}" + Style.RESET_ALL)


if __name__ == "__main__":
    asyncio.run(main())