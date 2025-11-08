"""JSON exporter"""

import json
import time
from datetime import datetime
import logging


def export_json(state, config):
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
