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
import requests

# Add command line argument parsing
parser = argparse.ArgumentParser(description='Process blockchain transaction data')
parser.add_argument('--name', help='Blockchain network name')
parser.add_argument('--endpoints', nargs='+', help='List of Web3 endpoints')
parser.add_argument('--start_block', type=int, help='Starting block number')
parser.add_argument('--num_threads', type=int, default=4, help='Number of parallel threads')
parser.add_argument('--block_db_path', type=str, default='', help='block_db_path')
parser.add_argument('--batch_size', type=int, default=10, help='Number of blocks per batch request')

args = parser.parse_args()

NAME = args.name
WEB3_ENPOINTS = args.endpoints
START_BLOCK = args.start_block
NUM_THREADS = args.num_threads
BLOCK_DB_PATH = args.block_db_path
BATCH_SIZE = args.batch_size

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

# Process and store block information in batch
def process_block_batch(block_numbers):
    """
    Batch process multiple blocks using JSON-RPC batch requests
    :param block_numbers: List of block numbers to process
    :return: True if all blocks processed successfully, False otherwise
    """
    if not block_numbers:
        return True
    
    conn = get_db_connection()
    try:
        # Select a web3 instance and get its endpoint URL
        web3_instance = random.choice(web3s)
        endpoint_url = web3_instance.provider.endpoint_uri
        
        # Prepare batch requests
        batch_requests = []
        for block_number in block_numbers:
            batch_requests.append({
                'jsonrpc': '2.0',
                'method': 'eth_getBlockByNumber',
                'params': [hex(block_number), True],  # True for full transactions
                'id': block_number
            })
        
        # Send batch request using requests library
        response = requests.post(
            endpoint_url,
            json=batch_requests,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        
        # Handle case where response might be a single object or a list
        if isinstance(response_data, dict):
            response_data = [response_data]
        
        # Process each block response
        all_block_data = []
        all_type4_txs = []
        
        for block_resp in response_data:
            if not isinstance(block_resp, dict):
                print(f"Unexpected response format: {type(block_resp)}")
                continue
                
            if 'result' not in block_resp or block_resp['result'] is None:
                block_number = block_resp.get('id', 'unknown')
                print(f"Block #{block_number} not found in response")
                continue
            
            block_data = block_resp['result']
            block_number = int(block_data['number'], 16)
            timestamp = int(block_data['timestamp'], 16)
            transactions = block_data.get('transactions', [])
            
            # Calculate number of type=4 transactions
            type4_count = 0
            for tx in transactions:
                tx_type = int(tx.get('type', '0x0'), 16)
                if tx_type == 4:
                    type4_count += 1
                    tx_hash = tx['hash']
                    # Store transaction data as JSON
                    tx_data = json.dumps(tx)
                    all_type4_txs.append((tx_hash, block_number, tx_data))
            
            # Collect block information
            all_block_data.append((block_number, len(transactions), type4_count, timestamp))
            print(f"Block #{block_number}: {len(transactions)} txs, {type4_count} type4")
        
        # Batch insert into database - single commit
        cursor = conn.cursor()
        if all_block_data:
            cursor.executemany(
                "INSERT INTO blocks (block_number, tx_count, type4_tx_count, timestamp) VALUES (?, ?, ?, ?)",
                all_block_data
            )
        
        if all_type4_txs:
            cursor.executemany(
                "INSERT INTO type4_transactions (tx_hash, block_number, tx_data) VALUES (?, ?, ?)",
                all_type4_txs
            )
        
        conn.commit()
        print(f"Batch committed: {len(all_block_data)} blocks")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Network error for blocks {block_numbers[0]}-{block_numbers[-1]}: {str(e)}")
        conn.rollback()
        
        return False
    except Exception as e:
        print(f"Batch processing error for blocks {block_numbers[0]}-{block_numbers[-1]}: {str(e)}")
        conn.rollback()
        return False

def process_block_batch_with_retry(block_numbers):
    """
    Retry mechanism for batch processing with binary split on failure
    :param block_numbers: List of block numbers to process
    :return: True if successful, False otherwise
    """
    if not block_numbers:
        return True
    
    # Try processing the batch with retries
    max_retries = 3
    for retry in range(max_retries):
        if process_block_batch(block_numbers):
            return True
        else:
            if retry < max_retries - 1:
                print(f"Retrying batch {block_numbers[0]}-{block_numbers[-1]}, attempt {retry+1}/{max_retries}")
    
    # If all retries failed, use binary split
    print(f"All retries failed for batch {block_numbers[0]}-{block_numbers[-1]}")
    
    # If only one block, cannot split further - fail
    if len(block_numbers) == 1:
        print(f"Failed to process single block #{block_numbers[0]}, skipping...")
        return False
    
    # Binary split: divide the batch into two halves
    mid = len(block_numbers) // 2
    left_half = block_numbers[:mid]
    right_half = block_numbers[mid:]
    
    print(f"Binary splitting batch into {len(left_half)} + {len(right_half)} blocks")
    
    # Process both halves sequentially (recursive)
    result_left = process_block_batch_with_retry(left_half)
    result_right = process_block_batch_with_retry(right_half)
    
    # Return True only if both halves succeed
    return result_left and result_right

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

        # Split blocks into batches
        batches = []
        for i in range(0, len(blocks_needed), BATCH_SIZE):
            batch = blocks_needed[i:i + BATCH_SIZE]
            batches.append(batch)
        
        print(f"Split into {len(batches)} batches (batch size: {BATCH_SIZE})")

        # Use thread pool to process batches in parallel
        print(f"Starting to process batches in parallel using {NUM_THREADS} threads...")
        success_count = 0
        error_count = 0
        processed_blocks = 0
        
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = []
            for batch in batches:
                futures.append(
                    executor.submit(process_block_batch_with_retry, batch)
                )
            
            # Wait for all tasks to complete
            for idx, future in enumerate(futures):
                try:
                    result = future.result()
                    batch = batches[idx]
                    if result:
                        success_count += len(batch)
                    else:
                        error_count += len(batch)
                    
                    processed_blocks += len(batch)
                    if processed_blocks % 100 == 0 or idx % 10 == 0:
                        print(f"Processed {processed_blocks}/{len(blocks_needed)} blocks ({idx+1}/{len(batches)} batches)...")
                except Exception as e:
                    batch = batches[idx]
                    print(f"Error processing batch: {e}")
                    error_count += len(batch)
        
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
