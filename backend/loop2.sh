while true; do
start_time=$(date +%s)
./get_bsc.sh
./get_op.sh
./get_gnosis.sh
./get_arb.sh
end_time=$(date +%s)
echo "Loop2 Time taken: $((end_time - start_time)) seconds" >> loop.log
done;