python3 get_block.py --name uni --endpoints \
https://unichain-rpc.publicnode.com \
https://rpc.therpc.io/unichain \
https://0xrpc.io/uni \
https://unichain.drpc.org \
https://mainnet.unichain.org \
https://unichain.api.onfinality.io/public \
--num_threads 5 \
--start_block 33690000

python3 get_tvl.py --name uni --contract 0xc86bDf9661c62646194ef29b1b8f5Fe226E8C97E --endpoints \
https://unichain-rpc.publicnode.com \
https://rpc.therpc.io/unichain \
https://0xrpc.io/uni \
https://unichain.drpc.org \
https://mainnet.unichain.org \
https://unichain.api.onfinality.io/public \
--num_threads 5

python3 get_code.py --name uni --endpoints \
https://unichain-rpc.publicnode.com \
https://rpc.therpc.io/unichain \
https://0xrpc.io/uni \
https://unichain.drpc.org \
https://mainnet.unichain.org \
https://unichain.api.onfinality.io/public \
--num_threads 5