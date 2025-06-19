while true; do
start_time=$(date +%s)
./get_mainnet.sh
./get_sepolia.sh
./get_base.sh
./get_ink.sh
./get_uni.sh
./get_scroll.sh
./get_bera.sh
end_time=$(date +%s)
echo "Loop1 Time taken: $((end_time - start_time)) seconds" >> loop.log
done;