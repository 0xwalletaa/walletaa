#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sqlite3
import time
import threading
from web3 import Web3
from collections import Counter
from hexbytes import HexBytes
import random
import argparse
from concurrent.futures import ThreadPoolExecutor

# Add command line argument parsing
parser = argparse.ArgumentParser(description='Process blockchain transaction data')
parser.add_argument('--name', help='Blockchain network name')
parser.add_argument('--endpoints', nargs='+', help='List of Web3 endpoints')
parser.add_argument('--start_block', type=int, help='Starting block number')
parser.add_argument('--num_threads', type=int, default=4, help='Number of parallel threads')
parser.add_argument('--block_db_path', type=str, default='', help='block_db_path')

args = parser.parse_args()

NAME = args.name
WEB3_ENPOINTS = args.endpoints
START_BLOCK = args.start_block
NUM_THREADS = args.num_threads
BLOCK_DB_PATH = args.block_db_path

block_db_path = f'{NAME}_block.db'
if BLOCK_DB_PATH != '':
    block_db_path = f'{BLOCK_DB_PATH}/{NAME}_block.db'

web3s = [
    Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 10})) for endpoint in WEB3_ENPOINTS
]

# Create thread-local storage
thread_local = threading.local()

if NAME == 'bsc' or NAME == 'scroll':
    from web3.middleware import ExtraDataToPOAMiddleware
    for i in range(len(web3s)):
        web3s[i].middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Helper function: handle JSON serialization of HexBytes objects
def serialize_web3_tx(tx_dict):
    result = {}
    for key, value in tx_dict.items():
        if isinstance(value, HexBytes):
            result[key] = value.hex()
        elif isinstance(value, list):
            result[key] = [serialize_web3_tx(item) if hasattr(item, 'items') else 
                          item.hex() if isinstance(item, HexBytes) else item 
                          for item in value]
        elif hasattr(value, 'items'):
            # Handle any dictionary-like objects (including AttributeDict)
            result[key] = serialize_web3_tx(dict(value))
        else:
            result[key] = value
    return result

# Get thread-local database connection
def get_db_connection():
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect(block_db_path)
    return thread_local.db_connection

# Initialize database
def init_db():
    conn = sqlite3.connect(block_db_path)
    cursor = conn.cursor()
    
    # Check if blocks table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blocks'")
    if not cursor.fetchone():
        # Create blocks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            block_number INTEGER PRIMARY KEY,
            tx_count INTEGER,
            type4_tx_count INTEGER,
            timestamp INTEGER
        )
        ''')
        print("Created blocks table")
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_blocks_block_number 
        ON blocks(block_number ASC);
        ''')
        print("Created idx_blocks_block_number index")
    
    # Check if type4_transactions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='type4_transactions'")
    if not cursor.fetchone():
        # Create transaction table (only store type=4 transactions)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS type4_transactions (
            tx_hash TEXT PRIMARY KEY,
            block_number INTEGER,
            tx_data TEXT,
            FOREIGN KEY (block_number) REFERENCES blocks(block_number)
        )
        ''')
        print("Created type4_transactions table")
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_type4_transactions_block_number 
        ON type4_transactions(block_number ASC);
        ''')
        print("Created idx_type4_transactions_block_number index")
    
    conn.commit()
    return conn


# Get all existing block numbers from database
def get_existing_blocks(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT block_number FROM blocks WHERE block_number >= ?", (START_BLOCK,))
    existing_blocks = set(row[0] for row in cursor.fetchall())
    return existing_blocks

# Process and store block information
def process_block(block_number):
    conn = get_db_connection()
    try:
        # Get complete block information
        block = random.choice(web3s).eth.get_block(block_number, full_transactions=True)
        transactions = block.transactions
        
        # Calculate number of type=4 transactions
        type4_count = 0
        type4_txs = []
        
        for tx in transactions:
            tx_type = getattr(tx, 'type', 0)
            if tx_type == 4:
                type4_count += 1
                tx_hash = tx.hash.hex()
                # Use custom function to handle HexBytes serialization issues
                tx_data = json.dumps(serialize_web3_tx(dict(tx)))
                type4_txs.append((tx_hash, block_number, tx_data))
        
        # Store block information
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO blocks (block_number, tx_count, type4_tx_count, timestamp) VALUES (?, ?, ?, ?)",
            (block_number, len(transactions), type4_count, block.timestamp)
        )
        
        # Store type=4 transactions
        if type4_txs:
            cursor.executemany(
                "INSERT INTO type4_transactions (tx_hash, block_number, tx_data) VALUES (?, ?, ?)",
                type4_txs
            )
        
        conn.commit()
        print(f"Block #{block_number}: {len(transactions)} txs, {type4_count} type4")
        return True
    
    except Exception as e:
        print(f"Block #{block_number} error: {str(e)}")
        conn.rollback()
        return False

def process_block_with_retry(block_number):
    # Retry mechanism
    max_retries = 3
    for retry in range(max_retries):
        if process_block(block_number):
            return True
        else:
            print(f"Retrying block #{block_number}, attempt {retry+1}/{max_retries}")
    return False

def main():
    # Initialize database
    conn = init_db()
    
    try:
        # Get latest block number
        latest_block = random.choice(web3s).eth.block_number
        print(f"Current latest block: {latest_block}")
        
        # Get all existing block numbers at once
        existing_blocks = get_existing_blocks(conn)
        print(f"Found {len(existing_blocks)} existing blocks in database")
        
        blocks_needed = []
        for block_number in range(START_BLOCK, latest_block):
            if block_number not in existing_blocks:
                blocks_needed.append(block_number)
                if len(blocks_needed) > 100000:
                    break
        
        del existing_blocks
                
        print(f"Number of blocks to process: {len(blocks_needed)}")
        time.sleep(1)

        # Use thread pool to process blocks in parallel
        print(f"Starting to process blocks in parallel using {NUM_THREADS} threads...")
        success_count = 0
        error_count = 0
        
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = []
            for block_number in blocks_needed:
                futures.append(
                    executor.submit(process_block_with_retry, block_number)
                )
            
            # Wait for all tasks to complete
            for future in futures:
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    if (success_count + error_count) % 100 == 0:
                        print(f"Processed {success_count + error_count} blocks...")
                except Exception as e:
                    print(f"Error processing block: {e}")
                    error_count += 1
        
        print(f"\nProcessing complete! Success: {success_count}, Failed: {error_count}")
        if len(blocks_needed) < 10000:
            time.sleep(60)
        
    except Exception as e:
        print(f"Program error: {e}")
    finally:
        conn.close()
        
    print("\nProgram finished")

if __name__ == "__main__":
    main() 
