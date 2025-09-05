python3 get_block.py --name arb --endpoints \
https://arbitrum.rpc.subquery.network/public \
https://arbitrum.meowrpc.com \
https://arbitrum.gateway.tenderly.co \
https://rpc.therpc.io/arbitrum \
https://arbitrum.drpc.org \
https://arbitrum-one-rpc.publicnode.com \
https://arb-pokt.nodies.app \
https://arb1.lava.build \
https://arbitrum-one.public.blastapi.io \
https://1rpc.io/arb \
https://arb1.arbitrum.io/rpc \
--num_threads 10 \
--start_block 369760000 \
--block_db_path /mnt

python3 get_tvl.py --name arb --contract 0x3aF42ae5A628e7bC0824B9b786DA512cFd18D4e9  --endpoints \
https://arbitrum.rpc.subquery.network/public \
https://arbitrum.meowrpc.com \
https://arbitrum.gateway.tenderly.co \
https://rpc.therpc.io/arbitrum \
https://arbitrum.drpc.org \
https://arbitrum-one-rpc.publicnode.com \
https://arb-pokt.nodies.app \
https://arb1.lava.build \
https://arbitrum-one.public.blastapi.io \
https://1rpc.io/arb \
https://arb1.arbitrum.io/rpc \
--num_threads 5 \
--block_db_path /mnt

python3 get_code.py --name arb --endpoints \
https://arbitrum.rpc.subquery.network/public \
https://arbitrum.meowrpc.com \
https://arbitrum.gateway.tenderly.co \
https://rpc.therpc.io/arbitrum \
https://arbitrum.drpc.org \
https://arbitrum-one-rpc.publicnode.com \
https://arb-pokt.nodies.app \
https://arb1.lava.build \
https://arbitrum-one.public.blastapi.io \
https://1rpc.io/arb \
https://arb1.arbitrum.io/rpc \
--num_threads 5 \
--block_db_path /mnt