while true; do
python3 get_block.py --name ink --endpoints \
https://ink.drpc.org \
https://rpc-qnd.inkonchain.com \
https://rpc-gel.inkonchain.com \
--num_threads 3 \
--start_block 13000000

python3 get_tvl.py --name ink --contract 0xc86bDf9661c62646194ef29b1b8f5Fe226E8C97E --endpoints \
https://ink.drpc.org \
https://rpc-qnd.inkonchain.com \
https://rpc-gel.inkonchain.com \
--num_threads 3

python3 get_code.py --name ink --endpoints \
https://ink.drpc.org \
https://rpc-qnd.inkonchain.com \
https://rpc-gel.inkonchain.com \
--num_threads 3

sleep 60
done