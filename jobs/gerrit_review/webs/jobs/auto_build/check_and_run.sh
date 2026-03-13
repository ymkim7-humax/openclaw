#!/bin/bash
# Connection Check and Auto-Build Trigger (with temporary -j12)
# Managed by OC v2

SERVER_IP="10.250.21.112"
WORKSPACE="/home/ymkim7/.openclaw/workspace"
JOB_PATH="$WORKSPACE/jobs/auto_build"

echo "Checking connectivity to $SERVER_IP..."

# Try connection on multiple ports
if ssh -o ConnectTimeout=10 -p 29418 ymkim7@$SERVER_IP "echo connection_test" 2>&1 | grep -q "connection_test" || \
   ssh -o ConnectTimeout=10 -p 22 ymkim7@$SERVER_IP "echo connection_test" 2>&1 | grep -q "connection_test" || \
   ssh -o ConnectTimeout=10 -p 29418 ymkim7@$SERVER_IP exit 2>&1 | grep -v "Connection timed out"; then
    
    echo "Success! Connection to Git server restored."
    
    # 1. Temporarily apply -j12 for speed as requested
    sed -i 's/make -j1/make -j12/g' "$JOB_PATH/build_hp2236b.sh"
    sed -i 's/make -j1/make -j12/g' "$JOB_PATH/build_hp2272b.sh"
    
    echo "Starting automated build with -j12..."
    
    # 2. Run the build job
    bash "$JOB_PATH/run.sh"
    
    # 3. IMMEDIATELY revert to -j1 to leave no traces as strictly ordered
    sed -i 's/make -j12/make -j1/g' "$JOB_PATH/build_hp2236b.sh"
    sed -i 's/make -j12/make -j1/g' "$JOB_PATH/build_hp2272b.sh"
    
    echo "Build finished and scripts reverted to -j1."
    exit 0
else
    echo "Still unreachable. Retrying in 10 minutes."
    exit 1
fi
