while true; do
python3 get_block.py --name gnosis --endpoints \
https://gnosis.oat.farm \
https://gnosis-pokt.nodies.app \
https://rpc.ap-southeast-1.gateway.fm/v4/gnosis/non-archival/mainnet \
https://1rpc.io/gnosis \
https://gnosis-mainnet.public.blastapi.io \
https://gnosis-rpc.publicnode.com \
https://endpoints.omniatech.io/v1/gnosis/mainnet/public \
https://gnosis.drpc.org \
https://rpc.gnosischain.com \
https://rpc.gnosis.gateway.fm \
--num_threads 5 \
--start_block 39800000 #TODO: is it right?

python3 get_tvl.py --name gnosis --contract 0xc86bDf9661c62646194ef29b1b8f5Fe226E8C97E --endpoints \
https://gnosis.oat.farm \
https://gnosis-pokt.nodies.app \
https://rpc.ap-southeast-1.gateway.fm/v4/gnosis/non-archival/mainnet \
https://1rpc.io/gnosis \
https://gnosis-mainnet.public.blastapi.io \
https://gnosis-rpc.publicnode.com \
https://endpoints.omniatech.io/v1/gnosis/mainnet/public \
https://gnosis.drpc.org \
https://rpc.gnosischain.com \
https://rpc.gnosis.gateway.fm \
--num_threads 5

python3 get_code.py --name gnosis --endpoints \
https://gnosis.oat.farm \
https://gnosis-pokt.nodies.app \
https://rpc.ap-southeast-1.gateway.fm/v4/gnosis/non-archival/mainnet \
https://1rpc.io/gnosis \
https://gnosis-mainnet.public.blastapi.io \
https://gnosis-rpc.publicnode.com \
https://endpoints.omniatech.io/v1/gnosis/mainnet/public \
https://gnosis.drpc.org \
https://rpc.gnosischain.com \
https://rpc.gnosis.gateway.fm \
--num_threads 5

sleep 60
done