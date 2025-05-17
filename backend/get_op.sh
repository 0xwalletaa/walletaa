while true; do
python3 get_block.py --name op --endpoints \
https://api.zan.top/opt-mainnet \
https://gateway.tenderly.co/public/optimism \
https://optimism-mainnet.public.blastapi.io \
https://optimism.gateway.tenderly.co \
https://optimism-rpc.publicnode.com \
https://optimism.drpc.org \
https://0xrpc.io/op \
https://optimism.lava.build \
https://optimism.blockpi.network/v1/rpc/public \
https://op-pokt.nodies.app \
https://optimism.rpc.subquery.network/public \
https://optimism.api.onfinality.io/public \
--num_threads 5 \
--start_block 135600000
python3 get_address.py --name op --endpoints \
https://api.zan.top/opt-mainnet \
https://gateway.tenderly.co/public/optimism \
https://optimism-mainnet.public.blastapi.io \
https://optimism.gateway.tenderly.co \
https://optimism-rpc.publicnode.com \
https://optimism.drpc.org \
https://0xrpc.io/op \
https://optimism.lava.build \
https://optimism.blockpi.network/v1/rpc/public \
https://op-pokt.nodies.app \
https://optimism.rpc.subquery.network/public \
https://optimism.api.onfinality.io/public \
--num_threads 5
python3 get_code.py --name op --endpoints \
https://api.zan.top/opt-mainnet \
https://gateway.tenderly.co/public/optimism \
https://optimism-mainnet.public.blastapi.io \
https://optimism.gateway.tenderly.co \
https://optimism-rpc.publicnode.com \
https://optimism.drpc.org \
https://0xrpc.io/op \
https://optimism.lava.build \
https://optimism.blockpi.network/v1/rpc/public \
https://op-pokt.nodies.app \
https://optimism.rpc.subquery.network/public \
https://optimism.api.onfinality.io/public \
--num_threads 5
sleep 60
done