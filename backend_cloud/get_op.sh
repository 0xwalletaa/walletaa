#!/bin/bash
# endpoints 省略时由 rpc_manager 自动从 chainlist 缓存中探测存活端点
# batch_size 省略时使用 rpc_manager.CHAIN_CONFIG 里该链的默认批大小

python3 get_block_batch.py --name op --num_threads 5 --start_block 148950000

python3 get_tvl.py --name op --contract 0x89038D59C4Bd24970150c92B4f48A819f38d9c69 --num_threads 5

python3 get_code.py --name op --num_threads 5

python3 clean_block.py --name op
