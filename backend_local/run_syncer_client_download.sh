#!/bin/bash
echo "Starting sync..."
echo ""

# Sync mainnet
python3 syncer_client.py --name mainnet --server_url "$SERVER_URL" --start_block 23750000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name bsc --server_url "$SERVER_URL" --start_block 67834000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name op --server_url "$SERVER_URL" --start_block 143490000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name arb --server_url "$SERVER_URL" --start_block 398010000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name base --server_url "$SERVER_URL" --start_block 37900000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name bera --server_url "$SERVER_URL" --start_block 12780000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name gnosis --server_url "$SERVER_URL" --start_block 43030000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name ink --server_url "$SERVER_URL" --start_block 29090000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name uni --server_url "$SERVER_URL" --start_block 30940000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name scroll --server_url "$SERVER_URL" --start_block 24530000 --db_path "$DB_PATH" --download

echo ""
echo "Sync download completed!"

