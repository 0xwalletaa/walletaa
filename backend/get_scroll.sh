while true; do
python3 get_block.py --name scroll --endpoints \
https://scroll.drpc.org \
https://rpc.scroll.io \
https://rpc.ankr.com/scroll \
https://1rpc.io/scroll \
https://scroll-mainnet.chainstacklabs.com \
https://scroll-mainnet.public.blastapi.io \
https://scroll.api.onfinality.io/public \
https://scroll-rpc.publicnode.com \
--num_threads 5 \
--start_block 14900000

python3 get_tvl.py --name scroll --contract 0xc86bDf9661c62646194ef29b1b8f5Fe226E8C97E --endpoints \
https://scroll.drpc.org \
https://rpc.scroll.io \
https://rpc.ankr.com/scroll \
https://1rpc.io/scroll \
https://scroll-mainnet.chainstacklabs.com \
https://scroll-mainnet.public.blastapi.io \
https://scroll.api.onfinality.io/public \
https://scroll-rpc.publicnode.com \
--num_threads 5

python3 get_code.py --name scroll --endpoints \
https://scroll.drpc.org \
https://rpc.scroll.io \
https://rpc.ankr.com/scroll \
https://1rpc.io/scroll \
https://scroll-mainnet.chainstacklabs.com \
https://scroll-mainnet.public.blastapi.io \
https://scroll.api.onfinality.io/public \
https://scroll-rpc.publicnode.com \
--num_threads 5

sleep 60
done