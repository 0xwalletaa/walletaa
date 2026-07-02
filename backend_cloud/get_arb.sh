#!/bin/bash
# endpoints 省略时由 rpc_manager 自动从 chainlist 缓存中探测存活端点
# batch_size 省略时使用 rpc_manager.CHAIN_CONFIG 里该链的默认批大小

python3 get_block_batch.py --name arb --num_threads 10 --start_block 429900000

python3 get_tvl.py --name arb --contract 0x3aF42ae5A628e7bC0824B9b786DA512cFd18D4e9 --num_threads 5

python3 get_code.py --name arb --num_threads 5
