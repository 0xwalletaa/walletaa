#!/bin/bash
echo "Starting sync..."
echo ""

# Sync mainnet
python3 syncer_client.py --name mainnet --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name bsc --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name op --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name arb --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name base --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name bera --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name gnosis --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name ink --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name uni --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload
python3 syncer_client.py --name scroll --server_url "$SERVER_URL" --db_path "$DB_PATH" --upload

echo ""
echo "Sync upload completed!"

