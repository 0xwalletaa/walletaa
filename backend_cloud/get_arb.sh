python3 get_block_batch.py --name arb --endpoints \
https://rpc.owlracle.info/arb/70d38ce1826c4a60bb2a8e05a6c8b20f \
https://arbitrum-one.rpc.grove.city/v1/01fdb492 \
https://arbitrum-one-public.nodies.app \
https://arbitrum-one-rpc.publicnode.com \
https://arbitrum.drpc.org \
https://rpc.poolz.finance/arbitrum \
https://arbitrum.public.blockpi.network/v1/rpc/public \
https://public-arb-mainnet.fastnode.io \
https://arbitrum.rpc.subquery.network/public \
https://arb-one-mainnet.gateway.tatum.io \
https://arb1.lava.build \
https://api.zan.top/arb-one \
https://arbitrum.gateway.tenderly.co \
https://arb1.arbitrum.io/rpc \
https://arbitrum-one.public.blastapi.io \
https://1rpc.io/arb \
--num_threads 10 \
--start_block 398010000 \
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