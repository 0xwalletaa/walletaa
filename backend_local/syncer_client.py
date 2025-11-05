#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sqlite3
import requests
import time
import argparse

# Add command line argument parsing
parser = argparse.ArgumentParser(description='Syncer client for blockchain data')
parser.add_argument('--name', required=True, help='Blockchain network name')
parser.add_argument('--server_url', required=True, help='Syncer server URL (e.g., http://server:5000)')
parser.add_argument('--start_block', type=int, default=0, help='Starting block number')
parser.add_argument('--db_path', type=str, default='../info_local', help='Local database path')

# Add mutually exclusive required group for download/upload
mode_group = parser.add_mutually_exclusive_group(required=True)
mode_group.add_argument('--download', action='store_true', help='Download data from server (blocks, TVL, code)')
mode_group.add_argument('--upload', action='store_true', help='Upload pending addresses to server')

args = parser.parse_args()

NAME = args.name
SERVER_URL = args.server_url.rstrip('/')
START_BLOCK = args.start_block
DB_PATH = args.db_path

# 读取token文件
def load_token():
    """Load authentication token from syncer_token.txt"""
    token_file = os.path.join(os.path.dirname(__file__), 'syncer_token.txt')
    try:
        with open(token_file, 'r') as f:
            token = f.read().strip()
            if not token:
                print("WARNING: syncer_token.txt is empty!")
                return None
            return token
    except FileNotFoundError:
        print("WARNING: syncer_token.txt not found! Requests will be sent without authentication.")
        return None
    except Exception as e:
        print(f"ERROR reading syncer_token.txt: {e}")
        return None

AUTH_TOKEN = load_token()

def get_auth_headers():
    """Get headers with authentication token"""
    if AUTH_TOKEN:
        return {'Authorization': f'Bearer {AUTH_TOKEN}'}
    return {}

def generate_blocks_string(block_numbers):
    """将块号列表转换为紧凑的字符串格式，如 '3,5,7,9,12-20,23-55'
    
    Args:
        block_numbers: 块号列表（需要已排序）
        
    Returns:
        str: 紧凑格式的块字符串
    """
    if not block_numbers:
        return ''
    
    # 确保排序
    block_numbers = sorted(block_numbers)
    
    ranges = []
    range_start = block_numbers[0]
    range_end = block_numbers[0]
    
    for i in range(1, len(block_numbers)):
        if block_numbers[i] == range_end + 1:
            # 连续的块，扩展范围
            range_end = block_numbers[i]
        else:
            # 不连续，保存当前范围
            if range_start == range_end:
                ranges.append(str(range_start))
            else:
                ranges.append(f'{range_start}-{range_end}')
            
            # 开始新范围
            range_start = block_numbers[i]
            range_end = block_numbers[i]
    
    # 保存最后一个范围
    if range_start == range_end:
        ranges.append(str(range_start))
    else:
        ranges.append(f'{range_start}-{range_end}')
    
    return ','.join(ranges)

def get_db_paths(name):
    """Get database paths for specified chain"""
    block_db_path = f'{DB_PATH}/{name}_block.db'
    code_db_path = f'{DB_PATH}/{name}_code.db'
    tvl_db_path = f'{DB_PATH}/{name}_tvl.db'
    return block_db_path, code_db_path, tvl_db_path

def init_block_db(name):
    """Initialize block database"""
    block_db_path, _, _ = get_db_paths(name)
    conn = sqlite3.connect(block_db_path)
    return conn

def init_code_db(name):
    """Initialize code database"""
    _, code_db_path, _ = get_db_paths(name)
    conn = sqlite3.connect(code_db_path)
    return conn

def init_tvl_db(name):
    """Initialize tvl database"""
    _, _, tvl_db_path = get_db_paths(name)
    conn = sqlite3.connect(tvl_db_path)
    return conn

def get_local_highest_block(name):
    """Get the highest block number from local database"""
    try:
        block_db_path, _, _ = get_db_paths(name)
        conn = sqlite3.connect(block_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(block_number) FROM blocks")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] is not None else 0
    except Exception as e:
        print(f"Error getting local highest block: {e}")
        return 0

def check_block_exists(cursor, block_number):
    """Check if a specific block exists in local database"""
    cursor.execute("SELECT 1 FROM blocks WHERE block_number = ? LIMIT 1", (block_number,))
    return cursor.fetchone() is not None

def sync_block_batch(conn, name, block_numbers):
    """Request and sync a batch of blocks from server
    
    Args:
        conn: database connection
        name: chain name
        block_numbers: list of block numbers to sync
    
    Returns:
        int: number of blocks synced
    """
    try:
        # 生成blocks字符串
        blocks_str = generate_blocks_string(block_numbers)
        
        response = requests.post(
            f"{SERVER_URL}/{name}/get_block_txs",
            json={'blocks': blocks_str},
            headers={**get_auth_headers(), 'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"    HTTP Error {response.status_code} for blocks: {blocks_str}")
            return 0
        
        data = response.json()
        if not data.get('success'):
            print(f"    Error: {data.get('error')} for blocks: {blocks_str}")
            return 0
        
        blocks = data.get('blocks', [])
        
        # Insert blocks and transactions
        cursor = conn.cursor()
        synced_count = 0
        for block in blocks:
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO blocks (block_number, tx_count, type4_tx_count, timestamp) VALUES (?, ?, ?, ?)",
                    (block['block_number'], block['tx_count'], block['type4_tx_count'], block['timestamp'])
                )
                
                for tx in block.get('type4_txs', []):
                    cursor.execute(
                        "INSERT OR REPLACE INTO type4_transactions (tx_hash, block_number, tx_data) VALUES (?, ?, ?)",
                        (tx['tx_hash'], block['block_number'], tx['tx_data'])
                    )
                synced_count += 1
            except Exception as e:
                print(f"    Error inserting block {block['block_number']}: {e}")
        
        conn.commit()
        return synced_count
    except Exception as e:
        print(f"    Exception syncing blocks: {e}")
        return 0

def get_last_update_timestamp(name, table_name):
    """Get the last update timestamp from local database"""
    try:
        if table_name == 'codes':
            _, db_path, _ = get_db_paths(name)
        else:  # author_balances
            _, _, db_path = get_db_paths(name)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT MAX(last_update_timestamp) FROM {table_name}")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] is not None else 0
    except Exception as e:
        print(f"Error getting last update timestamp: {e}")
        return 0

def sync_highest_block(name):
    """Sync highest block information"""
    try:
        print(f"\n[{name}] Syncing highest block...")
        response = requests.get(
            f"{SERVER_URL}/{name}/get_highest_block",
            headers=get_auth_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                remote_highest = data.get('highest_block', 0)
                local_highest = get_local_highest_block(name)
                print(f"  Remote highest block: {remote_highest}")
                print(f"  Local highest block: {local_highest}")
                print(f"  Blocks behind: {remote_highest - local_highest}")
                return True
            else:
                print(f"  Error: {data.get('error')}")
                return False
        else:
            print(f"  HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def sync_blocks(name, start_block):
    """Sync block and transaction data - fills in missing blocks"""
    try:
        print(f"\n[{name}] Syncing blocks...")
        
        # Initialize database
        conn = init_block_db(name)
        cursor = conn.cursor()
        
        # Get remote highest block
        response = requests.get(
            f"{SERVER_URL}/{name}/get_highest_block",
            headers=get_auth_headers(),
            timeout=30
        )
        if response.status_code != 200:
            print(f"  Failed to get remote highest block")
            conn.close()
            return False
        
        remote_data = response.json()
        if not remote_data.get('success'):
            print(f"  Error: {remote_data.get('error')}")
            conn.close()
            return False
        
        remote_highest = remote_data.get('highest_block', 0)
        
        # Get local highest block
        local_highest = get_local_highest_block(name)
        
        print(f"  Start block: {start_block}")
        print(f"  Local highest: {local_highest}")
        print(f"  Remote highest: {remote_highest}")
        
        if start_block > remote_highest:
            print(f"  No blocks to sync")
            conn.close()
            return True
        
        # Iterate through blocks and collect missing ones
        batch_size = 1000
        total_synced = 0
        missing_blocks = []
        
        print(f"  Scanning blocks from {start_block} to {remote_highest}...")
        
        for block_num in range(start_block, remote_highest + 1):
            exists = check_block_exists(cursor, block_num)
            
            if not exists:
                # Block is missing, add to list
                missing_blocks.append(block_num)
                
                # Check if batch is full
                if len(missing_blocks) >= batch_size:
                    # Request this batch
                    blocks_str = generate_blocks_string(missing_blocks)
                    print(f"  Syncing {len(missing_blocks)} missing blocks: {blocks_str}")
                    synced = sync_block_batch(conn, name, missing_blocks)
                    total_synced += synced
                    
                    # Clear batch
                    missing_blocks = []
            
            # Progress indicator every 10000 blocks
            if (block_num - start_block) % 10000 == 0 and block_num > start_block:
                print(f"  Scanned up to block {block_num}...")
        
        # Don't forget the last batch if it exists
        if missing_blocks:
            blocks_str = generate_blocks_string(missing_blocks)
            print(f"  Syncing {len(missing_blocks)} missing blocks: {blocks_str}")
            synced = sync_block_batch(conn, name, missing_blocks)
            total_synced += synced
        
        conn.close()
        print(f"  Total blocks synced: {total_synced}")
        return True
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def sync_tvl(name):
    """Sync TVL data"""
    try:
        print(f"\n[{name}] Syncing TVL data...")
        
        # Initialize database
        conn = init_tvl_db(name)
        
        # Get last update timestamp
        last_timestamp = get_last_update_timestamp(name, 'author_balances')
        print(f"  Last update timestamp: {last_timestamp}")
        
        total_synced = 0
        while True:
            response = requests.get(
                f"{SERVER_URL}/{name}/get_tvl",
                params={'last_update_timestamp': last_timestamp},
                headers=get_auth_headers(),
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"  HTTP Error: {response.status_code}")
                break
            
            data = response.json()
            if not data.get('success'):
                print(f"  Error: {data.get('error')}")
                break
            
            tvl_data = data.get('tvl_data', [])
            if not tvl_data:
                print(f"  No new TVL data to sync")
                break
            
            # Insert TVL data
            cursor = conn.cursor()
            for record in tvl_data:
                try:
                    cursor.execute(
                        """INSERT OR REPLACE INTO author_balances 
                        (author_address, eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp, last_update_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (record['author_address'], record['eth_balance'], record['weth_balance'],
                         record['wbtc_balance'], record['usdt_balance'], record['usdc_balance'],
                         record['dai_balance'], record['timestamp'], record['last_update_timestamp'])
                    )
                    last_timestamp = max(last_timestamp, record['last_update_timestamp'])
                except Exception as e:
                    print(f"  Error inserting TVL record: {e}")
            
            conn.commit()
            total_synced += len(tvl_data)
            print(f"  Synced {len(tvl_data)} TVL records")
            
            # If we got less than 10000 records, we're done
            if len(tvl_data) < 10000:
                break
        
        conn.close()
        print(f"  Total TVL records synced: {total_synced}")
        return True
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def sync_code(name):
    """Sync code data"""
    try:
        print(f"\n[{name}] Syncing code data...")
        
        # Initialize database
        conn = init_code_db(name)
        
        # Get last update timestamp
        last_timestamp = get_last_update_timestamp(name, 'codes')
        print(f"  Last update timestamp: {last_timestamp}")
        
        total_synced = 0
        while True:
            response = requests.get(
                f"{SERVER_URL}/{name}/get_code",
                params={'last_update_timestamp': last_timestamp},
                headers=get_auth_headers(),
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"  HTTP Error: {response.status_code}")
                break
            
            data = response.json()
            if not data.get('success'):
                print(f"  Error: {data.get('error')}")
                break
            
            code_data = data.get('code_data', [])
            if not code_data:
                print(f"  No new code data to sync")
                break
            
            # Insert code data
            cursor = conn.cursor()
            for record in code_data:
                try:
                    cursor.execute(
                        """INSERT OR REPLACE INTO codes 
                        (code_address, code, timestamp, last_update_timestamp)
                        VALUES (?, ?, ?, ?)""",
                        (record['code_address'], record['code'], record['timestamp'], record['last_update_timestamp'])
                    )
                    last_timestamp = max(last_timestamp, record['last_update_timestamp'])
                except Exception as e:
                    print(f"  Error inserting code record: {e}")
            
            conn.commit()
            total_synced += len(code_data)
            print(f"  Synced {len(code_data)} code records")
            
            # If we got less than 10000 records, we're done
            if len(code_data) < 10000:
                break
        
        conn.close()
        print(f"  Total code records synced: {total_synced}")
        return True
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def get_pending_db_path(name):
    """Get path to pending database"""
    return f'../info_local/{name}_pending.db'

def sync_pending(name):
    """Sync pending addresses to server
    
    This function reads pending addresses from the local pending.db
    and sends them to the server in batches of up to 1000 addresses.
    After successful sync, the addresses are removed from pending.db.
    """
    try:
        print(f"\n[{name}] Syncing pending addresses...")
        
        pending_db_path = get_pending_db_path(name)
        
        # Check if pending database exists
        if not os.path.exists(pending_db_path):
            print(f"  No pending database found at {pending_db_path}")
            return True
        
        conn = sqlite3.connect(pending_db_path)
        cursor = conn.cursor()
        
        # Sync pending TVL addresses
        total_tvl_synced = 0
        while True:
            try:
                # Read up to 10000 addresses
                cursor.execute("SELECT address FROM tvl LIMIT 10000")
                rows = cursor.fetchall()
                
                if not rows:
                    print(f"  No pending TVL addresses to sync")
                    break
                
                addresses = [row[0] for row in rows]
                print(f"  Syncing {len(addresses)} pending TVL addresses...")
                
                # Send to server
                response = requests.post(
                    f"{SERVER_URL}/{name}/add_tvl_addresses",
                    json={'addresses': addresses},
                    headers={**get_auth_headers(), 'Content-Type': 'application/json'},
                    timeout=60
                )
                
                if response.status_code != 200:
                    print(f"  HTTP Error {response.status_code} for TVL addresses")
                    break
                
                data = response.json()
                if not data.get('success'):
                    print(f"  Error: {data.get('error')}")
                    break
                
                # Delete successfully synced addresses
                placeholders = ','.join(['?' for _ in addresses])
                cursor.execute(f"DELETE FROM tvl WHERE address IN ({placeholders})", addresses)
                conn.commit()
                
                total_tvl_synced += len(addresses)
                print(f"  Synced and removed {len(addresses)} TVL addresses (added: {data.get('added_count', 0)})")
                
                # If we got less than 10000 rows, we're done
                if len(addresses) < 10000:
                    break
                    
            except Exception as e:
                print(f"  Error syncing TVL addresses: {e}")
                continue
        
        # Sync pending code addresses
        total_code_synced = 0
        while True:
            try:
                # Read up to 10000 addresses
                cursor.execute("SELECT address FROM code LIMIT 10000")
                rows = cursor.fetchall()
                
                if not rows:
                    print(f"  No pending code addresses to sync")
                    break
                
                addresses = [row[0] for row in rows]
                print(f"  Syncing {len(addresses)} pending code addresses...")
                
                # Send to server
                response = requests.post(
                    f"{SERVER_URL}/{name}/add_code_addresses",
                    json={'addresses': addresses},
                    headers={**get_auth_headers(), 'Content-Type': 'application/json'},
                    timeout=60
                )
                
                if response.status_code != 200:
                    print(f"  HTTP Error {response.status_code} for code addresses")
                    break
                
                data = response.json()
                if not data.get('success'):
                    print(f"  Error: {data.get('error')}")
                    break
                
                # Delete successfully synced addresses
                placeholders = ','.join(['?' for _ in addresses])
                cursor.execute(f"DELETE FROM code WHERE address IN ({placeholders})", addresses)
                conn.commit()
                
                total_code_synced += len(addresses)
                print(f"  Synced and removed {len(addresses)} code addresses (added: {data.get('added_count', 0)})")
                
                # If we got less than 10000 rows, we're done
                if len(addresses) < 10000:
                    break
                    
            except Exception as e:
                print(f"  Error syncing code addresses: {e}")
                continue
        
        conn.close()
        
        print(f"  Total pending addresses synced: TVL={total_tvl_synced}, Code={total_code_synced}")
        return True
        
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def main():
    """Main synchronization function"""
    mode = "DOWNLOAD" if args.download else "UPLOAD"
    
    print(f"=" * 80)
    print(f"Starting syncer client")
    print(f"Mode: {mode}")
    print(f"Chain: {NAME}")
    print(f"Server: {SERVER_URL}")
    print(f"Start block: {START_BLOCK}")
    print(f"Local DB path: {DB_PATH}")
    if AUTH_TOKEN:
        print(f"Authentication: ENABLED (token loaded)")
    else:
        print(f"Authentication: DISABLED (no syncer_token.txt found)")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 80)
    
    start_time = time.time()
    
    if args.download:
        # Download mode: Sync data from server
        # 1. Sync highest block info
        sync_highest_block(NAME)
        
        # 2. Sync blocks and transactions
        sync_blocks(NAME, START_BLOCK)
        
        # 3. Sync TVL data
        sync_tvl(NAME)
        
        # 4. Sync code data
        sync_code(NAME)
    
    elif args.upload:
        # Upload mode: Sync pending addresses to server
        sync_pending(NAME)
    
    elapsed_time = time.time() - start_time
    print(f"\n" + "=" * 80)
    print(f"{mode} sync for {NAME} completed in {elapsed_time:.2f} seconds")
    print(f"=" * 80)

if __name__ == "__main__":
    main()

