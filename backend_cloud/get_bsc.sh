#!/bin/bash
# endpoints 省略时由 rpc_manager 自动从 chainlist 缓存中探测存活端点
# batch_size 省略时使用 rpc_manager.CHAIN_CONFIG 里该链的默认批大小

python3 get_block_batch.py --name bsc --num_threads 5 --start_block 85280000

python3 get_tvl.py --name bsc --contract 0x27c81Cb1281a9643E7Ace9E843579316Be56456E --num_threads 5

python3 get_code.py --name bsc --num_threads 5

python3 clean_block.py --name bsc
