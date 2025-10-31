while true; do
start_time=$(date +%s)
./get_$1.sh
end_time=$(date +%s)
timestamp=$(date +%Y-%m-%d_%H:%M:%S)
echo "$timestamp $1 get: $((end_time - start_time)) seconds" >> loop.log
cd ../server
export NAME=$1
export BLOCK_DB_PATH=/mnt
start_time=$(date +%s)
python3 updater_sqlite.py
python3 cache_overview.py
end_time=$(date +%s)
timestamp=$(date +%Y-%m-%d_%H:%M:%S)
echo "$timestamp $1 update: $((end_time - start_time)) seconds" >> loop.log
cd -
done;