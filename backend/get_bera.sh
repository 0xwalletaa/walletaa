# while true; do
python3 get_block.py --name bera --endpoints \
https://berachain.drpc.org \
https://berachain-rpc.publicnode.com \
https://rpc.berachain.com \
https://rpc.berachain-apis.com \
--num_threads 4 \
--start_block 5900000

python3 get_tvl.py --name bera --contract 0xc86bDf9661c62646194ef29b1b8f5Fe226E8C97E --endpoints \
https://berachain.drpc.org \
https://berachain-rpc.publicnode.com \
https://rpc.berachain.com \
https://rpc.berachain-apis.com \
--num_threads 4

python3 get_code.py --name bera --endpoints \
https://berachain.drpc.org \
https://berachain-rpc.publicnode.com \
https://rpc.berachain.com \
https://rpc.berachain-apis.com \
--num_threads 4

# sleep 60
# done