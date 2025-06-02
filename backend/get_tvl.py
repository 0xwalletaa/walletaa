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
parser.add_argument('--contract', required=True, help='Contract address')
parser.add_argument('--num_threads', type=int, default=4, help='Number of parallel threads')
parser.add_argument('--data_expiry', type=int, default=86400, help='Data expiry time (seconds)')
parser.add_argument('--limit', type=int, default=10000, help='Processing limit')

args = parser.parse_args()

NAME = args.name
WEB3_ENPOINTS = args.endpoints
CONTRACT_ADDRESS = args.contract

# Number of parallel threads
NUM_THREADS = args.num_threads
# Data expiry time (seconds)
DATA_EXPIRY = args.data_expiry
# Processing limit
LIMIT = args.limit

web3s = [
    Web3(Web3.HTTPProvider(endpoint)) for endpoint in WEB3_ENPOINTS
]

block_db_path = f'{NAME}_block.db'
tvl_db_path = f'{NAME}_tvl.db'

# another db
info_db_path = f'../server/db/{NAME}.db'

# Create thread-local storage
thread_local = threading.local()

# Contract address and ABI configuration
CONTRACT_ABI = [
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "targets",
                "type": "address[]"
            }
        ],
        "name": "get",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "uint256",
                        "name": "ethBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "wethBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "wbtcBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "usdtBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "usdcBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "daiBalance",
                        "type": "uint256"
                    }
                ],
                "internalType": "struct BalanceQuery.TokenBalances[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def ecrecover(auth):
    if type(auth['chainId']) == int:
        auth['chainId'] = hex(auth['chainId'])
    if type(auth['nonce']) == int:
        auth['nonce'] = hex(auth['nonce'])
    if type(auth['yParity']) == int:
        auth['yParity'] = hex(auth['yParity'])
        
    chain_id = to_bytes(hexstr=auth['chainId'])
    address_bytes = to_bytes(hexstr=auth['address'])
    nonce = to_bytes(hexstr=auth['nonce'])

    # RLP encode [chain_id, address, nonce]
    encoded_data = rlp.encode([chain_id, address_bytes, nonce])

    # Construct EIP-7702 message: 0x05 || rlp(...)
    message_bytes = b'\x05' + encoded_data
    # Calculate Keccak-256 hash
    message_hash = keccak(message_bytes)

    # Convert signature components to standard format
    r_bytes = HexBytes(auth['r'])
    s_bytes = HexBytes(auth['s'])
    # yParity (0 or 1) is used directly
    y_parity = int(auth['yParity'], 16)

    # Create vrs tuple
    vrs = (y_parity, r_bytes, s_bytes)
    recovered_address = Account()._recover_hash(message_hash, vrs=vrs)
    
    return recovered_address

def get_db_connection():
    """Get thread-local database connection"""
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect(tvl_db_path)
        # Create table to store author balance information (if not exists)
        cursor = thread_local.db_connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS author_balances (
            author_address TEXT PRIMARY KEY,
            eth_balance TEXT,
            weth_balance TEXT,
            wbtc_balance TEXT,
            usdt_balance TEXT,
            usdc_balance TEXT,
            dai_balance TEXT,
            timestamp INTEGER
        )
        ''')
        thread_local.db_connection.commit()
    return thread_local.db_connection

def get_author_addresses():
    author_addresses = set()
    
    """Get all author addresses from info_db_path"""
    if os.path.exists(info_db_path):
        conn = sqlite3.connect(info_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT authorizer_address FROM authorizers WHERE tvl_timestamp < ? LIMIT ?", (int(time.time()) - DATA_EXPIRY, LIMIT))
        for row in cursor:
            if row[0] != 'error':
                author_addresses.add(row[0])
            if len(author_addresses) >= LIMIT:
                break
        conn.close()
        print(f"Got {len(author_addresses)} author addresses from info_db_path")
        # print(author_addresses)
        return list(author_addresses)
    
    """Get all author addresses from mainnet_blocks database"""
    
    try:
        # Connect to database
        conn = sqlite3.connect(block_db_path)
        cursor = conn.cursor()
        
        # Get all type4 transaction data
        cursor.execute("SELECT tx_data FROM type4_transactions")
        
        # Iterate through all transaction data
        for (tx_data_str,) in cursor:
            try:
                tx_data = json.loads(tx_data_str)
                
                # Check if authorizationList field exists
                if 'authorizationList' in tx_data and tx_data['authorizationList']:
                    for auth in tx_data['authorizationList']:
                        try:
                            author = ecrecover(auth)
                            if author and not is_data_fresh(author.lower()):
                                author_addresses.add(author.lower())
                        except Exception as e:
                            print(f"Error processing signature recovery: {e}, data: {auth}")
                            continue
                
                if len(author_addresses) >= LIMIT:
                    break
            except json.JSONDecodeError as e:
                print(f"Error parsing transaction data: {e}")
                continue
        
        conn.close()
        print(f"Got {len(author_addresses)} unique author addresses from database")
        return list(author_addresses)
    except Exception as e:
        print(f"Error getting author addresses: {e}")
        return []

def get_address_balances(author_addresses):
    """Query token balances for specified address list"""
    try:
        # Randomly select a Web3 node
        web3 = random.choice(web3s)
        
        # Create contract instance
        contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        
        # Convert addresses to checksum format
        checksum_addresses = [Web3.to_checksum_address(addr) for addr in author_addresses]
        
        # Call contract to get all token balances
        result = contract.functions.get(checksum_addresses).call()
        
        # Parse results
        balances = []
        for i, balance_data in enumerate(result):
            balances.append({
                'address': author_addresses[i],
                'eth_balance': str(balance_data[0] / (10 ** 18)),
                'weth_balance': str(balance_data[1] / (10 ** 18)),
                'wbtc_balance': str(balance_data[2] / (10 ** 8)),  # WBTC uses 8 decimals
                'usdt_balance': str(balance_data[3] / (10 ** 6)),
                'usdc_balance': str(balance_data[4] / (10 ** 6)),
                'dai_balance': str(balance_data[5] / (10 ** 18)),
            })
        
        return balances
    except Exception as e:
        print(f"Error getting address balances: {e}")
        return []

def is_data_fresh(author_address):
    """Check if data is within expiry time"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp FROM author_balances WHERE author_address = ?", 
        (author_address,)
    )
    result = cursor.fetchone()
    
    if result:
        last_update = result[0]
        current_time = int(time.time())
        return (current_time - last_update) < DATA_EXPIRY
    
    return False

def update_author_balance(author_addresses):
    """Update author address balance information"""
    try:
        # Get all token balances
        balances = get_address_balances(author_addresses)
        print(f"Got balances for {len(balances)} addresses")
        
        if balances:
            # Update database
            conn = get_db_connection()
            cursor = conn.cursor()
            for balance in balances:
                cursor.execute(
                    """
                    INSERT INTO author_balances (author_address, eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
                    ON CONFLICT(author_address) 
                    DO UPDATE SET eth_balance = ?, weth_balance = ?, wbtc_balance = ?, usdt_balance = ?, usdc_balance = ?, dai_balance = ?, timestamp = ?
                    """,
                    (balance['address'], balance['eth_balance'], balance['weth_balance'], balance['wbtc_balance'], 
                     balance['usdt_balance'], balance['usdc_balance'], balance['dai_balance'], int(time.time()),
                     balance['eth_balance'], balance['weth_balance'], balance['wbtc_balance'], 
                     balance['usdt_balance'], balance['usdc_balance'], balance['dai_balance'], int(time.time()))
                )
            conn.commit()
            print(f"Updated balances for {len(balances)} addresses")
    except Exception as e:
        print(f"Error updating author {author_addresses} information: {e}")

def main():
    # Initialize database connection (main thread)
    get_db_connection()
    
    # Get all author addresses
    time_start = time.time()
    author_addresses = get_author_addresses()
    time_end = time.time()  
    print(f"Got {len(author_addresses)} author addresses in {time_end - time_start} seconds")

    if not author_addresses:
        print("No author addresses found, exiting program")
        return
    
    unfresh_author_addresses = []
    for address in author_addresses:
        if not is_data_fresh(address):
            # print(f"Address {address} balance expired")
            unfresh_author_addresses.append(address)
    
    # Use thread pool to get balances in parallel
    print(f"Starting to update balance data for {len(unfresh_author_addresses)} addresses...")
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for i in range(0, len(unfresh_author_addresses), 500):
            batch = unfresh_author_addresses[i:i+500]
            futures.append(
                executor.submit(update_author_balance, batch)
            )
        
        # Wait for all tasks to complete
        for future in futures:
            try:
                future.result()
                success_count += 1
                if success_count % 100 == 0:
                    print(f"Processed {success_count} address groups...")
            except Exception as e:
                print(f"Error processing addresses: {e}")
                error_count += 1
    
    print(f"\nProcessing complete! Success: {success_count}, Failed: {error_count}")
    
    print("\nProgram finished")

if __name__ == "__main__":
    main() 