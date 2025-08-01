while true; do
start_time=$(date +%s)
./get_$1.sh
end_time=$(date +%s)
echo "$1 get: $((end_time - start_time)) seconds" >> loop.log
cd ../server
export NAME=$1
start_time=$(date +%s)
python3 updater_sqlite.py
python3 cache_overview.py
end_time=$(date +%s)
echo "$1 update: $((end_time - start_time)) seconds" >> loop.log
cd -
done;