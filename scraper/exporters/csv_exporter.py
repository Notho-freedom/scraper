"""CSV exporter"""

import csv
import time
import logging


def export_csv(state, config):
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
