#!/bin/bash
set -e

# Job Configuration
JOB_NAME="hp2236b_analysis"
WORKSPACE_JOB_DIR="/home/ymkim7/.openclaw/workspace/jobs/$JOB_NAME"
BUILD_DIR_CONTAINER="/home/ymkim7/.openclaw/workspace/jobs/$JOB_NAME/build"
MASTER_LOG="$WORKSPACE_JOB_DIR/analysis_build.log"
CONTAINER="ymkim7-airoha"

echo "=== [$(date)] Analysis Build Started ===" | tee -a "$MASTER_LOG"

# Step 1: Repo Sync
docker exec -u ymkim7 $CONTAINER bash -c "rm -rf $BUILD_DIR_CONTAINER && mkdir -p $BUILD_DIR_CONTAINER"
if docker exec -u ymkim7 $CONTAINER bash -c "cd $BUILD_DIR_CONTAINER && /bin/repo init -u ssh://git.humax-networks.com:29418/econet/repo/ -b ais -m hp2236b.xml --repo-branch=maint < /dev/null && /bin/repo sync -j8 --force-sync" >> "$MASTER_LOG" 2>&1; then
    echo "<< [Step 1] Sync Success." | tee -a "$MASTER_LOG"
else
    echo "!! [ERROR] Step 1 Failed." | tee -a "$MASTER_LOG"
    exit 1
fi

# Step 2: Setup
docker exec -u ymkim7 $CONTAINER bash -c "cd $BUILD_DIR_CONTAINER/2025q3 && ./airoha_script/airoha-compile.sh -c 7583 -f -m HP2236B -w Griffin_logan" >> "$MASTER_LOG" 2>&1

# Step 3: Compilation (Needed to generate build_dir artifacts)
echo ">> [Step 3] Compiling to generate analysis artifacts..." | tee -a "$MASTER_LOG"
docker exec -u ymkim7 $CONTAINER bash -c "cd $BUILD_DIR_CONTAINER/2025q3/openwrt-21.02/openwrt-21.02.1_dev && make -j1 MSDK=1 V=s" >> "$MASTER_LOG" 2>&1

echo "=== [$(date)] Analysis Build Finished ===" | tee -a "$MASTER_LOG"
