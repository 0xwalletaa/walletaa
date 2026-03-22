#!/bin/bash
echo "Starting sync..."
echo ""

# Sync mainnet
python3 syncer_client.py --name mainnet --server_url "$SERVER_URL" --start_block 24710000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name bsc --server_url "$SERVER_URL" --start_block 88130000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name op --server_url "$SERVER_URL" --start_block 149300000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name arb --server_url "$SERVER_URL" --start_block 444500000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name base --server_url "$SERVER_URL" --start_block 43700000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name bera --server_url "$SERVER_URL" --start_block 18590000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name gnosis --server_url "$SERVER_URL" --start_block 45280000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name ink --server_url "$SERVER_URL" --start_block 40710000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name uni --server_url "$SERVER_URL" --start_block 41360000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name scroll --server_url "$SERVER_URL" --start_block 32370000 --db_path "$DB_PATH" --download

echo ""
echo "Sync download completed!"

