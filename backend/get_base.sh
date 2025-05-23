counter=29
while true; do
python3 get_block.py --name base --endpoints \
https://base.llamarpc.com \
https://base.api.onfinality.io/public \
https://base-mainnet.public.blastapi.io \
https://base-pokt.nodies.app \
https://base.drpc.org \
https://base.meowrpc.com \
https://1rpc.io/base \
https://endpoints.omniatech.io/v1/base/mainnet/public \
https://base.blockpi.network/v1/rpc/public \
https://0xrpc.io/base \
https://mainnet.base.org \
https://api.zan.top/base-mainnet \
https://base.gateway.tenderly.co \
https://base.rpc.subquery.network/public \
https://base.gateway.tenderly.co \
--num_threads 5 \
--start_block 30000000

counter=$((counter + 1))
if [ $counter -eq 30 ]; then
    python3 get_tvl.py --name base --endpoints \
    https://base.llamarpc.com \
    https://base.api.onfinality.io/public \
    https://base-mainnet.public.blastapi.io \
    https://base-pokt.nodies.app \
    https://base.drpc.org \
    https://base.meowrpc.com \
    https://1rpc.io/base \
    https://endpoints.omniatech.io/v1/base/mainnet/public \
    https://base.blockpi.network/v1/rpc/public \
    https://0xrpc.io/base \
    https://mainnet.base.org \
    https://api.zan.top/base-mainnet \
    https://base.gateway.tenderly.co \
    https://base.rpc.subquery.network/public \
    https://base.gateway.tenderly.co \
    --num_threads 5

    python3 get_code.py --name base --endpoints \
    https://base.llamarpc.com \
    https://base.api.onfinality.io/public \
    https://base-mainnet.public.blastapi.io \
    https://base-pokt.nodies.app \
    https://base.drpc.org \
    https://base.meowrpc.com \
    https://1rpc.io/base \
    https://endpoints.omniatech.io/v1/base/mainnet/public \
    https://base.blockpi.network/v1/rpc/public \
    https://0xrpc.io/base \
    https://mainnet.base.org \
    https://api.zan.top/base-mainnet \
    https://base.gateway.tenderly.co \
    https://base.rpc.subquery.network/public \
    https://base.gateway.tenderly.co \
    --num_threads 5
    counter=0
fi

sleep 60
done