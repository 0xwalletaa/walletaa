#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sqlite3
import time
import threading
import random
from web3 import Web3
from hexbytes import HexBytes
from concurrent.futures import ThreadPoolExecutor
import coincurve
from eth_utils import to_checksum_address
import hashlib

from eth_keys import keys
from hexbytes import HexBytes
from eth_utils import to_checksum_address, to_int, to_bytes
from eth_account import Account
import rlp
from eth_utils import keccak
import argparse
import os

# Add command line argument parsing
parser = argparse.ArgumentParser(description='Process blockchain transaction data')
parser.add_argument('--name', help='Blockchain network name')
parser.add_argument('--endpoints', nargs='+', help='List of Web3 endpoints')

parser.add_argument('--num_threads', type=int, default=4, help='Number of parallel threads')
parser.add_argument('--data_expiry', type=int, default=86400000, help='Data expiry time (seconds)')
parser.add_argument('--block_db_path', type=str, default='', help='block_db_path')

args = parser.parse_args()

NAME = args.name
WEB3_ENPOINTS = args.endpoints

# Number of parallel threads
NUM_THREADS = args.num_threads
# Data expiry time (seconds)
DATA_EXPIRY = args.data_expiry

BLOCK_DB_PATH = args.block_db_path

web3s = [
    Web3(Web3.HTTPProvider(endpoint)) for endpoint in WEB3_ENPOINTS
]

block_db_path = f'{NAME}_block.db'
if BLOCK_DB_PATH != '':
    block_db_path = f'{BLOCK_DB_PATH}/{NAME}_block.db'
code_db_path = f'{NAME}_code.db'

# another db
info_db_path = f'../server/db/{NAME}.db'

# Create thread-local storage
thread_local = threading.local()

def get_db_connection():
    """Get thread-local database connection"""
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect(code_db_path)
        # Create table to store author balance information (if not exists)
        cursor = thread_local.db_connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            code_address TEXT PRIMARY KEY,
            code TEXT,
            timestamp INTEGER,
            last_update_timestamp INTEGER
        )
        ''')
        thread_local.db_connection.commit()
    return thread_local.db_connection

def get_code_addresses():
    code_addresses = set()
    
    """Get all code addresses from info_db_path"""
    if os.path.exists(info_db_path):
        conn = sqlite3.connect(info_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT distinct code_address FROM authorizations")
        for row in cursor:
            if row[0] != 'error':
                code_addresses.add(row[0])
        conn.close()
        print(f"Got {len(code_addresses)} code addresses from info_db_path")
        return list(code_addresses)

    """Get all code addresses from mainnet_blocks database"""
    try:
        # Connect to database
        conn = sqlite3.connect(block_db_path)
        cursor = conn.cursor()
        
        # Get all type4 transaction data
        cursor.execute("SELECT tx_data FROM type4_transactions")
        
        # Iterate through all transaction data
        for row in cursor:
            tx_data_str = row[0]
            try:
                tx_data = json.loads(tx_data_str)
                
                # Check if authorizationList field exists
                if 'authorizationList' in tx_data and tx_data['authorizationList']:
                    for auth in tx_data['authorizationList']:
                        code_addresses.add(auth['address'])
            except json.JSONDecodeError as e:
                print(f"Error parsing transaction data: {e}")
                continue
        
        conn.close()
        print(f"Got {len(code_addresses)} unique code addresses from database")
        return list(code_addresses)
    except Exception as e:
        print(f"Error getting code addresses: {e}")
        return []

def get_code(code_address):
    """Get code for specified address"""
    try:
        # Randomly select a Web3 node
        web3 = random.choice(web3s)
        code = web3.eth.get_code(Web3.to_checksum_address(code_address))
        return HexBytes(code).hex()
    except Exception as e:
        print(f"Error getting code for address {code_address}: {e}")
        return None

def is_data_fresh(code_address):
    """Check if data is within expiry time"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp FROM codes WHERE code_address = ?", 
        (code_address,)
    )
    result = cursor.fetchone()
    
    if result:
        last_update = result[0]
        current_time = int(time.time())
        return (current_time - last_update) < DATA_EXPIRY
    
    return False

def update_code(code_address):
    """Update author address code information"""
    try:
        # Get code
        code = get_code(code_address)
        print(f"Got code for address {code_address}: {code}")
        
        if code is not None:
            # Update database
            conn = get_db_connection()
            cursor = conn.cursor()
            current_timestamp = int(time.time())
            
            # First, get existing code data from database
            cursor.execute(
                """
                SELECT code, last_update_timestamp 
                FROM codes WHERE code_address = ?
                """,
                (code_address,)
            )
            existing_data = cursor.fetchone()
            
            # Check if code has changed
            code_changed = False
            if existing_data:
                existing_code, existing_last_update = existing_data
                
                # Compare code
                if existing_code != code:
                    code_changed = True
            else:
                # New address, consider as changed
                code_changed = True
            
            # Determine last_update_timestamp value
            if code_changed:
                last_update_timestamp = current_timestamp
            else:
                # Keep existing last_update_timestamp if no change
                last_update_timestamp = existing_data[1] if existing_data else current_timestamp
            
            # Insert or update the record
            cursor.execute(
                """
                INSERT INTO codes (code_address, code, timestamp, last_update_timestamp) 
                VALUES (?, ?, ?, ?) 
                ON CONFLICT(code_address) 
                DO UPDATE SET code = ?, timestamp = ?, last_update_timestamp = ?
                """,
                (code_address, code, current_timestamp, last_update_timestamp, 
                 code, current_timestamp, last_update_timestamp)
            )
            conn.commit()
            print(f"Updated code for address {code_address}: {code} (changed: {code_changed})")
    except Exception as e:
        print(f"Error updating address {code_address} information: {e}")

def main():
    # Initialize database connection (main thread)
    get_db_connection()
    
    # Get all author addresses
    time_start = time.time()
    code_addresses = get_code_addresses()
    time_end = time.time()  
    print(f"Got {len(code_addresses)} code addresses in {time_end - time_start} seconds")

    if not code_addresses:
        print("No code addresses found, exiting program")
        return
    
    unfresh_code_addresses = []
    for address in code_addresses:
        if not is_data_fresh(address):
            print(f"Code for address {address} has expired")
            unfresh_code_addresses.append(address)
    
    # Use thread pool to get balances in parallel
    print(f"Starting to update code data for {len(unfresh_code_addresses)} addresses...")
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for address in unfresh_code_addresses:
            futures.append(
                executor.submit(update_code, address)
            )
        
        # Wait for all tasks to complete
        for future in futures:
            try:
                future.result()
                success_count += 1
                if success_count % 100 == 0:
                    print(f"Processed {success_count} addresses...")
            except Exception as e:
                print(f"Error processing address: {e}")
                error_count += 1
    
    print(f"\nProcessing complete! Success: {success_count}, Failed: {error_count}")
    
    print("\nProgram finished")

if __name__ == "__main__":
    main() 