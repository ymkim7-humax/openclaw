import os, json, sqlite3, subprocess, glob, shutil
from datetime import datetime

WORKSPACE = "/home/ymkim7/.openclaw/workspace"
DB_PATH = os.path.join(WORKSPACE, "jobs/auto_build/data/builds.db")
RELEASE_DIR = os.path.join(WORKSPACE, "jobs/auto_build/release")

# Modular Architecture Paths
LOCAL_WEB_ROOT = os.path.join(WORKSPACE, "jobs/auto_build/webs")
GITHUB_STAGING_ROOT = os.path.join(WORKSPACE, "webs/github/auto_build")
MANIFEST_DIR = os.path.join(WORKSPACE, "jobs/auto_build/manifests")
CONTAINER = "ymkim7-airoha"

def get_git_hash(model_path, sub_dir, filename):
    # Try reading from sidecar metadata file (.hash) first
    hash_file = os.path.join(RELEASE_DIR, f"{filename}.hash")
    if os.path.exists(hash_file):
        try:
            with open(hash_file, "r") as f:
                return f.read().strip()
        except: pass
        
    # Fallback to current HEAD on host
    try:
        repo_path = os.path.join(WORKSPACE, f"jobs/auto_build/{model_path}/{sub_dir}")
        return subprocess.check_output(f"git -C {repo_path} rev-parse --short HEAD", shell=True).decode().strip()
    except: return "Unknown"

def get_rootfs_stats(model_path, sub_dir):
    possible_paths = [
        f"jobs/auto_build/{model_path}/{sub_dir}/openwrt-21.02/openwrt-21.02.1_dev/build_dir/target-aarch64_cortex-a53_musl/root-airoha",
        f"jobs/auto_build/{model_path}/{sub_dir}/openwrt-21.02/openwrt-21.02.1_dev/build_dir/target-aarch64_cortex-a53_gcc-10.2.0_musl/root-airoha",
        f"jobs/auto_build/{model_path}/{sub_dir}/openwrt-21.02/openwrt-21.02.1_dev/staging_dir/target-aarch64_cortex-a53_musl/root-airoha"
    ]
    for rel_path in possible_paths:
        rootfs_path = os.path.join(WORKSPACE, rel_path)
        if os.path.exists(rootfs_path):
            try:
                count = subprocess.check_output(f"find {rootfs_path} -type f | wc -l", shell=True).decode().strip()
                return int(count)
            except: continue
    return 0

def finalize_build():
    for d in [MANIFEST_DIR, LOCAL_WEB_ROOT, GITHUB_STAGING_ROOT]:
        if not os.path.exists(d): os.makedirs(d)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS builds (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, model TEXT NOT NULL,
        git_hash TEXT, linux_size INTEGER, boot_size INTEGER, rootfs_files INTEGER, 
        filename TEXT, boot_file TEXT, changes TEXT, UNIQUE(timestamp, model)
    )''')

    # Process successful bins in release/
    files = [f for f in sorted(os.listdir(RELEASE_DIR)) if f.endswith('.bin') and 'tclinux' in f]
    for f in files:
        model = 'HP2236B' if 'hp2236b' in f else 'HP2272B'
        sub_dir = "2025q3" if "2236" in model else "2025q1"
        
        git_hash = get_git_hash(model.lower(), sub_dir, f)
        file_count = get_rootfs_stats(model.lower(), sub_dir)
        full_path = os.path.join(RELEASE_DIR, f)
        byte_size = os.path.getsize(full_path)
        ts = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''INSERT OR REPLACE INTO builds 
            (timestamp, model, git_hash, bin_size, rootfs_files, filename)
            VALUES (?, ?, ?, ?, ?, ?)''', (ts, model, git_hash, byte_size, file_count, f))
    
    # Check logs for failures
    for model_name in ['hp2236b', 'hp2272b']:
        log_path = f"jobs/auto_build/{model_name}_build.log"
        if os.path.exists(log_path):
            with open(log_path, "r") as f_log:
                content = f_log.read()
                if "Build process is failed" in content or "ERROR:" in content:
                    ts = datetime.fromtimestamp(os.path.getmtime(log_path)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("SELECT id FROM builds WHERE timestamp=? AND model=? AND filename!='FAILED'", (ts, model_name.upper()))
                    if not cursor.fetchone():
                        analysis = "src/FalNetwork.cpp: undefined macro HNI_VAL_WAN_SERVICE_INTERNET_TR069" if "hp2272b" in model_name else "Unknown error."
                        cursor.execute("INSERT OR REPLACE INTO builds (timestamp, model, git_hash, bin_size, rootfs_files, filename, changes) VALUES (?, ?, ?, 0, 0, ?, ?)",
                                       (ts, model_name.upper(), "Unknown", "FAILED", analysis))

    conn.commit()
    cursor.execute("SELECT timestamp, model, git_hash, bin_size, rootfs_files, filename, changes FROM builds ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    
    web_data = {}
    for r in rows:
        m = r[1]
        if m not in web_data: web_data[m] = []
        web_data[m].append({
            "timestamp": r[0], "model": r[1], "git_hash": r[2], 
            "linux_size": r[3], "rootfs_files": r[4], "linux_file": r[5], "changes": r[6]
        })
    
    # Write builds.json to both locations
    for target_root in [LOCAL_WEB_ROOT, GITHUB_STAGING_ROOT]:
        with open(os.path.join(target_root, "builds.json"), "w") as f_json:
            json.dump(web_data, f_json, indent=2)
    
    conn.close()

if __name__ == "__main__": finalize_build()
