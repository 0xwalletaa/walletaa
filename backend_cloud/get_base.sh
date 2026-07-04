#!/bin/bash
# endpoints 省略时由 rpc_manager 自动从 chainlist 缓存中探测存活端点
# batch_size 省略时使用 rpc_manager.CHAIN_CONFIG 里该链的默认批大小

python3 get_block_batch.py --name base --num_threads 5 --start_block 43360000

python3 get_tvl.py --name base --contract 0x16Eef38116c2081fbC4d4E54F81d0D08640ff00F --num_threads 5

python3 get_code.py --name base --num_threads 5

python3 clean_block.py --name base
