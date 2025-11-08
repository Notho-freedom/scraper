"""SQLite exporter"""

import sqlite3
import time
import logging


def export_sqlite(state, config):
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
