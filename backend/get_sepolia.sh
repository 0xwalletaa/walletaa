counter=0
while true; do
    python3 get_block.py --name sepolia --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep --start_block 8000000
    
    counter=$((counter + 1))
    if [ $counter -eq 30 ]; then
        python3 get_address.py --name sepolia --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep
        python3 get_code.py --name sepolia --endpoints https://api.zan.top/eth-sepolia https://eth-sepolia.public.blastapi.io https://sepolia.drpc.org https://0xrpc.io/sep
        counter=0
    fi
    
    sleep 60
done