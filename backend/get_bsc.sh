while true; do
python3 get_block.py --name bsc --endpoints \
https://api.zan.top/bsc-mainnet \
https://endpoints.omniatech.io/v1/bsc/mainnet/public \
https://bsc-mainnet.public.blastapi.io \
https://bsc.drpc.org \
https://bsc-dataseed4.bnbchain.org \
https://binance.llamarpc.com \
https://bnb.rpc.subquery.network/public \
https://bsc-mainnet.public.blastapi.io \
https://bsc.meowrpc.com \
https://rpc-bsc.48.club \
https://rpc.therpc.io/bsc \
https://bsc.rpc.blxrbdn.com \
https://bsc.blockrazor.xyz \
--num_threads 10 \
--start_block 47600000
sleep 1
done