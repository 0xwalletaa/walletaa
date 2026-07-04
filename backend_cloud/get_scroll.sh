#!/bin/bash
# endpoints 省略时由 rpc_manager 自动从 chainlist 缓存中探测存活端点
# batch_size 省略时使用 rpc_manager.CHAIN_CONFIG 里该链的默认批大小

python3 get_block_batch.py --name scroll --num_threads 5 --start_block 31890000

python3 get_tvl.py --name scroll --contract 0xc86bDf9661c62646194ef29b1b8f5Fe226E8C97E --num_threads 5

python3 get_code.py --name scroll --num_threads 5

python3 clean_block.py --name scroll
