#!/bin/bash
# endpoints 省略时由 rpc_manager 自动从 chainlist 缓存中探测存活端点
# batch_size 省略时使用 rpc_manager.CHAIN_CONFIG 里该链的默认批大小

python3 get_block_batch.py --name mainnet --num_threads 4 --start_block 24650000

python3 get_tvl.py --name mainnet --contract 0x042A73966C7C5e8F16107abf1E9bD0448e1476ED --num_threads 4

python3 get_code.py --name mainnet --num_threads 4

python3 clean_block.py --name mainnet
