while true; do
    python3 get_block.py --name mainnet --endpoints https://api.zan.top/eth-mainnet https://endpoints.omniatech.io/v1/eth/mainnet/public https://eth-mainnet.public.blastapi.io https://eth.drpc.org https://0xrpc.io/eth --start_block 22430866
    python3 get_address.py --name mainnet --endpoints https://api.zan.top/eth-mainnet https://endpoints.omniatech.io/v1/eth/mainnet/public https://eth-mainnet.public.blastapi.io https://eth.drpc.org https://0xrpc.io/eth
    python3 get_code.py --name mainnet --endpoints https://api.zan.top/eth-mainnet https://endpoints.omniatech.io/v1/eth/mainnet/public https://eth-mainnet.public.blastapi.io https://eth.drpc.org https://0xrpc.io/eth
    sleep 60
done