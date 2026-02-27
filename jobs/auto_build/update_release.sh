#!/bin/bash
# Mock script to simulate adding a new build to release
# Sets up a pair of .bin and .json in jobs/auto_build/release

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
FILENAME="tclinux_$(date +%Y%m%d_%H%M%S).bin"
META="jobs/auto_build/release/${FILENAME%.bin}.json"

echo "Creating dummy build ${FILENAME}..."
touch "jobs/auto_build/release/${FILENAME}"

cat <<EOF > "$META"
{
  "timestamp": "$TIMESTAMP",
  "model": "HP2236B",
  "git_hash": "a1b2c3d4",
  "bin_size": "58M",
  "rootfs_files": "4300",
  "filename": "$FILENAME"
}
EOF

python3 jobs/auto_build/export_status.py
echo "Release sync complete."
