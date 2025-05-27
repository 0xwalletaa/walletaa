while true; do
python3 get_block.py --name sepolia --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep --start_block 8000000
python3 get_tvl.py --name sepolia --contract 0x89038D59C4Bd24970150c92B4f48A819f38d9c69 --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep
python3 get_code.py --name sepolia --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep
sleep 60
done