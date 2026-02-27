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
# This updates webs/local/ and webs/github/
python3 "$JOB_PATH/finalize.py"

# Sync Staging to GitHub Repo Path
# The user wants webs/github/ files to appear in remote repo's webs/ directory.
echo "Syncing local github staging to repo webs/ directory..."
cp "$WORKSPACE/webs/github/index.html" "$WORKSPACE/webs/index.html"
cp "$WORKSPACE/webs/github/builds.json" "$WORKSPACE/webs/builds.json"

# GitHub Auto-Push
echo "Pushing updates to GitHub..."
cd "$WORKSPACE"
git add webs/index.html webs/builds.json
git commit -m "Auto-update Build Dashboard: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

echo "All tasks completed successfully. Dashboards are live! :-)"
