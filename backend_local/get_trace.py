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

parser = argparse.ArgumentParser()
parser.add_argument('--openethereumx_url', required=True, help='Openethereumx URL (e.g., http://server:5000)')
parser.add_argument('--db_path', type=str, default='../info_local', help='Local database path')

args = parser.parse_args()
OPENETHEREUMX_URL = args.openethereumx_url
DB_PATH = args.db_path

NAME = "mainnet"
#TODO: provide public url on walletaa,com
WEB3_ENPOINTS = [OPENETHEREUMX_URL] 
START_BLOCK = 22431084

trace_db_path = f'{DB_PATH}/{NAME}_trace.db'

web3s = [
    Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 10})) for endpoint in WEB3_ENPOINTS
]

# Thread-local storage for database connections
thread_local = threading.local()

# Convert AttributeDict to regular dict for JSON serialization
def attributedict_to_dict(obj):
    if hasattr(obj, 'items'):
        return {k: attributedict_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [attributedict_to_dict(item) for item in obj]
    elif isinstance(obj, HexBytes):
        return obj.hex()
    else:
        return obj

# Get thread-local database connection
def get_db_connection():
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect(trace_db_path)
    return thread_local.db_connection


# Initialize database
def init_db():
    conn = sqlite3.connect(trace_db_path)
    cursor = conn.cursor()
    
    # Check if traces table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traces'")
    if not cursor.fetchone():
        # Create traces table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS traces (
            block_number INTEGER PRIMARY KEY,
            traces TEXT,
            used BOOLEAN DEFAULT 0
        )
        ''')
        print("Created traces table")
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_traces_block_number 
        ON traces(block_number ASC);
        ''')
        print("Created idx_traces_block_number index")
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_traces_used 
        ON traces(used ASC);
        ''')
        print("Created idx_traces_used index")
    conn.commit()
    return conn


# Process and store block information
def process_block(block_number):
    conn = get_db_connection()
    try:
        # Get complete block information
        print(f"Processing block #{block_number}")
        web3_instance = random.choice(web3s)
        req = web3_instance.manager.request_blocking("trace_filter_7702_calls", [{"fromBlock": hex(block_number), "toBlock": hex(block_number)}])
        traces = req
        
        # Convert AttributeDict objects to regular dicts for JSON serialization
        traces_dict = attributedict_to_dict(traces)
        """
        traces_dict=[{'action': {'callType': 'call', 'from': '0xf4ae64c5c4fb632d0e0d77097b957941c399d26e', 'gas': '0x26498', 'input': '0x3f707e6b00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000dadb0d80178819f2319190d340ce9a924f783711000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000', 'isEip7702': True, 'originalCodeAddress': '0xf4ae64c5c4fb632d0e0d77097b957941c399d26e', 'parsedCodeAddress': '0x775c8d470cc8d4530b8f233322480649f4fab758', 'to': '0xf4ae64c5c4fb632d0e0d77097b957941c399d26e', 'value': '0x0'}, 'blockHash': '0x58bd192ac34ab266597704f6bf26f8064d4b218bdee8086aadf9408f09a63a70', 'blockNumber': 22431337, 'result': {'gasUsed': '0xb0c8', 'output': '0x'}, 'subtraces': 2, 'traceAddress': [], 'transactionHash': '0x69d80eedfb1bb114bf67fae0012cce7a36e3278e305c05d111b1d467527030f1', 'transactionPosition': 74, 'type': 'call'}]
        """
        # Store block information
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO traces (block_number, traces) VALUES (?, ?)",
            (block_number, json.dumps(traces_dict))
        )
        
        conn.commit()
        print(f"Block #{block_number}: {len(traces)} traces")
        return True
    
    except Exception as e:
        print(f"Block #{block_number} error: {str(e)}")
        conn.rollback()
        return False

# Get all existing block numbers from database
def get_existing_blocks(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT block_number FROM traces WHERE block_number >= ?", (START_BLOCK,))
    existing_blocks = set(row[0] for row in cursor.fetchall())
    return existing_blocks

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
                if len(blocks_needed) > 10000000:
                    break
        
        del existing_blocks
                
        print(f"Number of blocks to process: {len(blocks_needed)}")
        time.sleep(1)
        
        for block_number in blocks_needed:
            process_block(block_number)
        
    except Exception as e:
        print(f"Program error: {e}")
    finally:
        conn.close()
        
    print("\nProgram finished")

if __name__ == "__main__":
    main() 
