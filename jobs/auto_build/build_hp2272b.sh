#!/bin/bash
set -e

# Job Configuration
JOB_NAME="auto_build"
BASE_DIR="/home/ymkim7/.openclaw/workspace/jobs/$JOB_NAME"
PROJ_DIR_CONTAINER="$BASE_DIR/hp2272b"
RELEASE_DIR="$BASE_DIR/release"
MASTER_LOG="/home/ymkim7/.openclaw/workspace/jobs/$JOB_NAME/hp2272b_build.log"
LOG_TS=$(date +%Y%m%d_%H%M%S)
CONTAINER="ymkim7-airoha"

# Ensure master log is fresh
rm -f "$MASTER_LOG"

echo "=== [$(date)] HP2272B Build Started (Job: $JOB_NAME) ===" | tee -a "$MASTER_LOG"

# Step 1: Repo Sync
docker exec -u ymkim7 $CONTAINER bash -c "rm -rf $PROJ_DIR_CONTAINER && mkdir -p $PROJ_DIR_CONTAINER"
if docker exec -u ymkim7 $CONTAINER bash -c "cd $PROJ_DIR_CONTAINER && /bin/repo init -u ssh://git.humax-networks.com:29418/econet/repo/ -b ais -m hp2272b.xml --repo-branch=maint < /dev/null && /bin/repo sync -j8 --force-sync" >> "$MASTER_LOG" 2>&1; then
    echo "<< [Step 1] Sync Success." | tee -a "$MASTER_LOG"
else
    echo "!! [ERROR] Step 1 Failed." | tee -a "$MASTER_LOG"
    exit 1
fi

# Step 2: Setup
docker exec -u ymkim7 $CONTAINER bash -c "cd $PROJ_DIR_CONTAINER/2025q1 && ./airoha_script/airoha-compile.sh -c 7583 -f -m HP2272B -w EagleKite_logan" >> "$MASTER_LOG" 2>&1

# Step 3: Compilation (Reverted to -j1 as requested)
docker exec -u ymkim7 $CONTAINER bash -c "cd $PROJ_DIR_CONTAINER/2025q1/openwrt-21.02/openwrt-21.02.1_dev && make -j12 MSDK=1 V=s" >> "$MASTER_LOG" 2>&1

# Step 4: Release
TCLINUX_BIN="$PROJ_DIR_CONTAINER/2025q1/openwrt-21.02/openwrt-21.02.1_dev/bin/targets/airoha/an7581/tclinux.bin"
TCBOOT_BIN="$PROJ_DIR_CONTAINER/2025q1/openwrt-21.02/openwrt-21.02.1_dev/bin/targets/airoha/an7581/tcboot.bin"

docker exec -u ymkim7 $CONTAINER mkdir -p "$RELEASE_DIR"
docker exec -u ymkim7 $CONTAINER bash -c "cp $TCLINUX_BIN $RELEASE_DIR/hp2272b_tclinux_$LOG_TS.bin"
docker exec -u ymkim7 $CONTAINER bash -c "[ -f $TCBOOT_BIN ] && cp $TCBOOT_BIN $RELEASE_DIR/hp2272b_tcboot_$LOG_TS.bin"

echo "=== [$(date)] HP2272B Build Finished Successfully ===" | tee -a "$MASTER_LOG"
