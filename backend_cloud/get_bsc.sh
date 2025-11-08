# while true; do
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
--start_block 67454000 \
--block_db_path /mnt

python3 get_tvl.py --name bsc --contract 0x27c81Cb1281a9643E7Ace9E843579316Be56456E  --endpoints \
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
--block_db_path /mnt

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
--num_threads 5 \
--block_db_path /mnt

# sleep 60
# done