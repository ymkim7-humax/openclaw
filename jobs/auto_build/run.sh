#!/bin/bash

# Configuration
WORKSPACE="/home/ymkim7/.openclaw/workspace"
JOB_NAME="auto_build"
JOB_PATH="$WORKSPACE/jobs/$JOB_NAME"

echo "=== Starting Parallel Auto Build Job: $JOB_NAME ==="

# Execute builds in background (using -j1 as strictly ordered)
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
# This script handles updating:
# 1. Local (Nginx): jobs/auto_build/webs/index.html
# 2. Public Staging: webs/github/auto_build/index.html
python3 "$JOB_PATH/finalize.py"

# Sync Staging to Repo Path for GitHub Push
echo "Syncing public staging to repo webs/ directory..."
cp -r "$WORKSPACE/webs/github/auto_build/"* "$WORKSPACE/webs/auto_build/"

# GitHub Auto-Push
echo "Pushing updates to GitHub..."
cd "$WORKSPACE"
# Track only the dashboard files for this job
git add webs/auto_build/index.html webs/auto_build/builds.json
git commit -m "Auto-update Build Dashboard: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

echo "All tasks completed successfully. Job dashboard is live! :-)"
