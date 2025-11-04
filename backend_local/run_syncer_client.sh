#!/bin/bash
echo "Starting sync..."
echo ""

# Sync mainnet
python3 syncer_client.py --name mainnet --server_url "$SERVER_URL" --start_block 23300000 --db_path "$DB_PATH"
python3 syncer_client.py --name bsc --server_url "$SERVER_URL" --start_block 64714000 --db_path "$DB_PATH"
python3 syncer_client.py --name op --server_url "$SERVER_URL" --start_block 141000000 --db_path "$DB_PATH"
python3 syncer_client.py --name arb --server_url "$SERVER_URL" --start_block 378200000 --db_path "$DB_PATH"
python3 syncer_client.py --name base --server_url "$SERVER_URL" --start_block 35400000 --db_path "$DB_PATH"
python3 syncer_client.py --name bera --server_url "$SERVER_URL" --start_block 10300000 --db_path "$DB_PATH"
python3 syncer_client.py --name gnosis --server_url "$SERVER_URL" --start_block 42000000 --db_path "$DB_PATH"
python3 syncer_client.py --name ink --server_url "$SERVER_URL" --start_block 24100000 --db_path "$DB_PATH"
python3 syncer_client.py --name uni --server_url "$SERVER_URL" --start_block 26350000 --db_path "$DB_PATH"
python3 syncer_client.py --name scroll --server_url "$SERVER_URL" --start_block 21000000 --db_path "$DB_PATH"

echo ""
echo "Sync completed!"

