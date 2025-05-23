counter=29
while true; do
python3 get_block.py --name bsc --endpoints \
https://api.zan.top/bsc-mainnet \
https://bsc-mainnet.public.blastapi.io \
https://bsc.drpc.org \
https://bsc-dataseed4.bnbchain.org \
https://binance.llamarpc.com \
https://bnb.rpc.subquery.network/public \
https://bsc-mainnet.public.blastapi.io \
https://bsc.meowrpc.com \
https://rpc-bsc.48.club \
https://bsc.rpc.blxrbdn.com \
https://bsc.blockrazor.xyz \
--num_threads 5 \
--start_block 47600000

counter=$((counter + 1))
if [ $counter -eq 30 ]; then
    python3 get_tvl.py --name bsc --endpoints \
    https://api.zan.top/bsc-mainnet \
    https://bsc-mainnet.public.blastapi.io \
    https://bsc.drpc.org \
    https://bsc-dataseed4.bnbchain.org \
    https://binance.llamarpc.com \
    https://bnb.rpc.subquery.network/public \
    https://bsc-mainnet.public.blastapi.io \
    https://bsc.meowrpc.com \
    https://rpc-bsc.48.club \
    https://bsc.rpc.blxrbdn.com \
    https://bsc.blockrazor.xyz \
    --num_threads 5

    python3 get_code.py --name bsc --endpoints \
    https://api.zan.top/bsc-mainnet \
    https://bsc-mainnet.public.blastapi.io \
    https://bsc.drpc.org \
    https://bsc-dataseed4.bnbchain.org \
    https://binance.llamarpc.com \
    https://bnb.rpc.subquery.network/public \
    https://bsc-mainnet.public.blastapi.io \
    https://bsc.meowrpc.com \
    https://rpc-bsc.48.club \
    https://bsc.rpc.blxrbdn.com \
    https://bsc.blockrazor.xyz \
    --num_threads 5
    counter=0
fi

sleep 60
done