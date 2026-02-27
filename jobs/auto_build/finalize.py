import os, json, sqlite3, subprocess, glob, shutil
from datetime import datetime

WORKSPACE = "/home/ymkim7/.openclaw/workspace"
DB_PATH = os.path.join(WORKSPACE, "jobs/auto_build/data/builds.db")
RELEASE_DIR = os.path.join(WORKSPACE, "jobs/auto_build/release")

# Defined Paths
LOCAL_WEB_ROOT = os.path.join(WORKSPACE, "webs/local")
GITHUB_STAGING_ROOT = os.path.join(WORKSPACE, "webs/github") # Local master for GitHub
MANIFEST_DIR = os.path.join(WORKSPACE, "jobs/auto_build/manifests")
CONTAINER = "ymkim7-airoha"

def get_git_hash(model_path, sub_dir):
    try:
        repo_path = os.path.join(WORKSPACE, f"jobs/auto_build/{model_path}/{sub_dir}")
        cmd = f"git -C {repo_path} rev-parse --short HEAD"
        return subprocess.check_output(cmd, shell=True).decode().strip()
    except: return "Unknown"

def get_rootfs_stats(model_path, sub_dir):
    possible_paths = [
        f"jobs/auto_build/{model_path}/{sub_dir}/openwrt-21.02/openwrt-21.02.1_dev/build_dir/target-aarch64_cortex-a53_musl/root-airoha",
        f"jobs/auto_build/{model_path}/{sub_dir}/openwrt-21.02/openwrt-21.02.1_dev/build_dir/target-aarch64_cortex-a53_gcc-10.2.0_musl/root-airoha"
    ]
    for rel_path in possible_paths:
        rootfs_path = os.path.join(WORKSPACE, rel_path)
        if os.path.exists(rootfs_path):
            try:
                count = subprocess.check_output(f"find {rootfs_path} -type f | wc -l", shell=True).decode().strip()
                file_list = subprocess.check_output(f"find {rootfs_path} -printf '%P\\n' | sort", shell=True).decode()
                return int(count), file_list
            except: continue
    return 0, ""

def finalize_build():
    for d in [MANIFEST_DIR, LOCAL_WEB_ROOT, GITHUB_STAGING_ROOT]:
        if not os.path.exists(d): os.makedirs(d)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS builds (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, model TEXT NOT NULL,
        git_hash TEXT, bin_size INTEGER, rootfs_files INTEGER, filename TEXT UNIQUE,
        file_exists INTEGER DEFAULT 1, changes TEXT
    )''')

    files = [f for f in sorted(os.listdir(RELEASE_DIR)) if f.endswith('.bin') and 'tclinux' in f]
    for f in files:
        model = 'HP2236B' if 'hp2236b' in f else 'HP2272B'
        sub_dir = "2025q3" if "2236" in model else "2025q1"
        
        git_hash = get_git_hash(model.lower(), sub_dir)
        file_count, current_manifest = get_rootfs_stats(model.lower(), sub_dir)
        full_path = os.path.join(RELEASE_DIR, f)
        byte_size = os.path.getsize(full_path)
        
        changes_str = "N/A"
        manifest_file = os.path.join(MANIFEST_DIR, f"{f}.txt")
        if not os.path.exists(manifest_file) and current_manifest:
            with open(manifest_file, "w") as mf: mf.write(current_manifest)
            prev_manifests = sorted(glob.glob(os.path.join(MANIFEST_DIR, f"*{model.lower()}*tclinux*.txt")), reverse=True)
            if len(prev_manifests) > 1:
                idx = next((i for i, m in enumerate(prev_manifests) if os.path.basename(m) == f"{f}.txt"), 0)
                if idx + 1 < len(prev_manifests):
                    try:
                        cmd = f"diff -u {prev_manifests[idx+1]} {manifest_file} | grep -E '^\\+|^-' | grep -vE '^\\+\\+\\+|^---' | wc -l"
                        diff_count = subprocess.check_output(cmd, shell=True).decode().strip()
                        changes_str = f"+/- {diff_count}"
                    except: pass

        ts = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT OR REPLACE INTO builds 
            (timestamp, model, git_hash, bin_size, rootfs_files, filename, file_exists, changes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (ts, model, git_hash, byte_size, file_count, f, 1, changes_str))
    
    conn.commit()
    cursor.execute("SELECT timestamp, model, git_hash, bin_size, rootfs_files, filename, file_exists, changes FROM builds ORDER BY timestamp DESC")
    data = [{"timestamp": r[0], "model": r[1], "git_hash": r[2], "bin_size": r[3], "rootfs_files": r[4], "filename": r[5], "file_exists": bool(r[6]), "changes": r[7]} for r in cursor.fetchall()]
    
    # Sync to BOTH locations
    for target_root in [LOCAL_WEB_ROOT, GITHUB_STAGING_ROOT]:
        with open(os.path.join(target_root, "builds.json"), "w") as f: json.dump(data, f, indent=2)
        idx_src = os.path.join(WORKSPACE, "jobs/auto_build/webs/index.html")
        if os.path.exists(idx_src): shutil.copy(idx_src, os.path.join(target_root, "index.html"))
    
    conn.close()

if __name__ == "__main__": finalize_build()
