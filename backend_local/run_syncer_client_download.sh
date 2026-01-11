#!/bin/bash
echo "Starting sync..."
echo ""

# Sync mainnet
python3 syncer_client.py --name mainnet --server_url "$SERVER_URL" --start_block 24180000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name bsc --server_url "$SERVER_URL" --start_block 74300000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name op --server_url "$SERVER_URL" --start_block 146000000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name arb --server_url "$SERVER_URL" --start_block 418000000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name base --server_url "$SERVER_URL" --start_block 40500000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name bera --server_url "$SERVER_URL" --start_block 15300000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name gnosis --server_url "$SERVER_URL" --start_block 44000000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name ink --server_url "$SERVER_URL" --start_block 34200000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name uni --server_url "$SERVER_URL" --start_block 37000000 --db_path "$DB_PATH" --download
python3 syncer_client.py --name scroll --server_url "$SERVER_URL" --start_block 27700000 --db_path "$DB_PATH" --download

echo ""
echo "Sync download completed!"

