while true; do
    python3 get_block.py --name sepolia --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep --start_block 8000000
    python3 get_address.py --name sepolia --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep
    sleep 10
done