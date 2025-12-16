python3 get_block.py --name base --endpoints \
https://base.llamarpc.com \
https://base.api.onfinality.io/public \
https://base-mainnet.public.blastapi.io \
https://base-pokt.nodies.app \
https://base.drpc.org \
https://base.meowrpc.com \
https://1rpc.io/base \
https://endpoints.omniatech.io/v1/base/mainnet/public \
https://mainnet.base.org \
https://api.zan.top/base-mainnet \
https://base.gateway.tenderly.co \
https://base.rpc.subquery.network/public \
https://base.gateway.tenderly.co \
--num_threads 5 \
--start_block 37900000

python3 get_tvl.py --name base --contract 0x16Eef38116c2081fbC4d4E54F81d0D08640ff00F  --endpoints \
https://base.api.onfinality.io/public \
https://base-mainnet.public.blastapi.io \
https://base-pokt.nodies.app \
https://base.drpc.org \
https://base.meowrpc.com \
https://endpoints.omniatech.io/v1/base/mainnet/public \
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
https://mainnet.base.org \
https://api.zan.top/base-mainnet \
https://base.gateway.tenderly.co \
https://base.rpc.subquery.network/public \
https://base.gateway.tenderly.co \
--num_threads 5