#!/bin/bash

# Configuration
WORKSPACE="/home/ymkim7/.openclaw/workspace"
JOB_NAME="auto_build"
JOB_PATH="$WORKSPACE/jobs/$JOB_NAME"

echo "=== Starting Parallel Auto Build Job: $JOB_NAME ==="

# Execute builds in background
bash "$JOB_PATH/build_hp2236b.sh" &
PID1=$!

bash "$JOB_PATH/build_hp2272b.sh" &
PID2=$!

# Wait for builds to complete
wait $PID1
RET1=$?
wait $PID2
RET2=$?

echo "HP2236B Result: $RET1"
echo "HP2272B Result: $RET2"

# Post-build: Finalize data collection
# This script handles updating both local and github staging paths correctly
# Targeted paths: jobs/auto_build/webs/index.html (Internal) and webs/auto_build/index.html (Public)
python3 "$JOB_PATH/finalize.py"

# GitHub Auto-Push
echo "Pushing updates to GitHub..."
cd "$WORKSPACE"
# Only track the specific job dashboard, DO NOT touch the root portal index.html
git add webs/auto_build/index.html
git commit -m "Auto-update Build Dashboard: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

echo "All tasks completed successfully. Job dashboard is live! :-)"
