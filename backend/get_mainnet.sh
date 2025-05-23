counter=29
while true; do
    python3 get_block.py --name mainnet --endpoints https://api.zan.top/eth-mainnet https://endpoints.omniatech.io/v1/eth/mainnet/public https://eth-mainnet.public.blastapi.io https://eth.drpc.org https://0xrpc.io/eth --start_block 22430866
    
    counter=$((counter + 1))
    if [ $counter -eq 30 ]; then
        python3 get_tvl.py --name mainnet --contract 0xB020fedD0684E6B8Dc5048004542a03721798df8  --endpoints https://api.zan.top/eth-mainnet https://endpoints.omniatech.io/v1/eth/mainnet/public https://eth-mainnet.public.blastapi.io https://eth.drpc.org https://0xrpc.io/eth
        python3 get_code.py --name mainnet --endpoints https://api.zan.top/eth-mainnet https://endpoints.omniatech.io/v1/eth/mainnet/public https://eth-mainnet.public.blastapi.io https://eth.drpc.org https://0xrpc.io/eth
        counter=0
    fi
    
    sleep 60
done