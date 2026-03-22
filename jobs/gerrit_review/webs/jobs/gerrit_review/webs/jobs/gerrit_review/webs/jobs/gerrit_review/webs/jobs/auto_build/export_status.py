import sqlite3
import json
import os
import glob
from datetime import datetime

WORKSPACE = "/home/ymkim7/.openclaw/workspace"
DB_PATH = os.path.join(WORKSPACE, "jobs/auto_build/data/builds.db")
RELEASE_DIR = os.path.join(WORKSPACE, "jobs/auto_build/release")
WEB_JSON = os.path.join(WORKSPACE, "webs/local/builds.json")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS builds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            git_hash TEXT,
            bin_size TEXT,
            rootfs_files TEXT,
            filename TEXT UNIQUE,
            file_exists INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    return conn

def sync_release_with_db(conn):
    cursor = conn.cursor()
    # Scan for new .json files in release/ not yet in DB
    meta_files = glob.glob(os.path.join(RELEASE_DIR, "*.json"))
    for meta_path in meta_files:
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
                if "timestamp" in meta and "filename" in meta:
                    cursor.execute('''
                        INSERT OR IGNORE INTO builds 
                        (timestamp, model, git_hash, bin_size, rootfs_files, filename, file_exists)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        meta['timestamp'], meta.get('model', 'HP2236B'), meta.get('git_hash'),
                        meta.get('bin_size'), meta.get('rootfs_files'), meta['filename'],
                        1 if os.path.exists(os.path.join(RELEASE_DIR, meta['filename'])) else 0
                    ))
        except Exception:
            continue
    
    # Update file_exists status for existing records
    cursor.execute("SELECT id, filename FROM builds")
    records = cursor.fetchall()
    for row_id, filename in records:
        exists = 1 if os.path.exists(os.path.join(RELEASE_DIR, filename)) else 0
        cursor.execute("UPDATE builds SET file_exists = ? WHERE id = ?", (exists, row_id))
    
    conn.commit()

def export_to_web(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, model, git_hash, bin_size, rootfs_files, filename, file_exists FROM builds ORDER BY timestamp DESC LIMIT 100")
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        data.append({
            "timestamp": row[0], "model": row[1], "git_hash": row[2],
            "bin_size": row[3], "rootfs_files": row[4], "filename": row[5],
            "file_exists": bool(row[6])
        })
        
    with open(WEB_JSON, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    connection = init_db()
    sync_release_with_db(connection)
    export_to_web(connection)
    connection.close()
    print(f"Build database updated and exported to web.")
