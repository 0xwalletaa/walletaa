#!/bin/bash

# Start syncer server for multiple chains (foreground mode)
# Usage: ./run_syncer_server.sh

# 定义允许访问的链名称列表（用逗号分隔）
export ALLOWED_NAMES="mainnet,bsc,op,arb,base,bera,gnosis,ink,uni,scroll"
export BLOCK_DB_PATH="/mnt"
export PORT=5000

# Change to script directory
cd "$(dirname "$0")"

echo "Starting syncer server..."
echo "Port: $PORT"
echo "Allowed chains: $ALLOWED_NAMES"
echo ""

# 如果设置了 BLOCK_DB_PATH，添加到参数中
if [ -n "$BLOCK_DB_PATH" ]; then
    python3 syncer_server.py --port "$PORT" --block_db_path "$BLOCK_DB_PATH"
else
    python3 syncer_server.py --port "$PORT"
fi

