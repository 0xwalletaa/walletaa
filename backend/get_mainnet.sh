# while true; do
python3 get_block.py --name mainnet --endpoints \
https://api.zan.top/eth-mainnet \
https://endpoints.omniatech.io/v1/eth/mainnet/public \
https://eth-mainnet.public.blastapi.io \
https://eth.drpc.org \
--start_block 22430866
python3 get_tvl.py --name mainnet --contract 0x042A73966C7C5e8F16107abf1E9bD0448e1476ED  --endpoints \
https://api.zan.top/eth-mainnet \
https://endpoints.omniatech.io/v1/eth/mainnet/public \
https://eth-mainnet.public.blastapi.io \
https://eth.drpc.org \
python3 get_code.py --name mainnet --endpoints \
https://api.zan.top/eth-mainnet \
https://endpoints.omniatech.io/v1/eth/mainnet/public \
https://eth-mainnet.public.blastapi.io \
https://eth.drpc.org \
# sleep 60
# done