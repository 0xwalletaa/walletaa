#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sqlite3
from flask import Flask, jsonify, request
import argparse
from functools import wraps

# Add command line argument parsing
parser = argparse.ArgumentParser(description='Syncer server for blockchain data')
parser.add_argument('--port', type=int, default=5000, help='Server port')
parser.add_argument('--block_db_path', type=str, default='', help='block_db_path')
args = parser.parse_args()

PORT = args.port
BLOCK_DB_PATH = args.block_db_path

# 从环境变量读取允许的链名称列表
ALLOWED_NAMES_STR = os.environ.get("ALLOWED_NAMES", "mainnet")
ALLOWED_NAMES = set(name.strip() for name in ALLOWED_NAMES_STR.split(','))

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
        print("WARNING: syncer_token.txt not found! Server will run without authentication.")
        return None
    except Exception as e:
        print(f"ERROR reading syncer_token.txt: {e}")
        return None

AUTH_TOKEN = load_token()

app = Flask(__name__)

def require_token(f):
    """Decorator to require authentication token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果没有配置token，则不进行认证
        if AUTH_TOKEN is None:
            return f(*args, **kwargs)
        
        # 从请求头获取token
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                'success': False,
                'error': 'Missing authentication token'
            }), 401
        
        # 支持 "Bearer <token>" 格式
        if token.startswith('Bearer '):
            token = token[7:]
        
        # 验证token
        if token != AUTH_TOKEN:
            return jsonify({
                'success': False,
                'error': 'Invalid authentication token'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_chain_name(name):
    """验证链名称是否在允许的列表中"""
    if name not in ALLOWED_NAMES:
        return jsonify({
            'error': f'Chain name "{name}" is not supported',
            'allowed_names': list(ALLOWED_NAMES)
        }), 404
    return None

def get_db_paths(name):
    """Get database paths for specified chain"""
    block_db_path = f'{name}_block.db'
    if BLOCK_DB_PATH != '':
        block_db_path = f'{BLOCK_DB_PATH}/{name}_block.db'
    code_db_path = f'{name}_code.db'
    tvl_db_path = f'{name}_tvl.db'
    return block_db_path, code_db_path, tvl_db_path

def get_block_db_connection(name):
    """Get block database connection"""
    block_db_path, _, _ = get_db_paths(name)
    conn = sqlite3.connect(block_db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_code_db_connection(name):
    """Get code database connection"""
    _, code_db_path, _ = get_db_paths(name)
    conn = sqlite3.connect(code_db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_tvl_db_connection(name):
    """Get tvl database connection"""
    _, _, tvl_db_path = get_db_paths(name)
    conn = sqlite3.connect(tvl_db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'allowed_chains': list(ALLOWED_NAMES)
    })

@app.route('/<name>/get_highest_block', methods=['GET'])
@require_token
def get_highest_block(name):
    """Get the highest block number in the database"""
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        conn = get_block_db_connection(name)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(block_number) as highest_block FROM blocks")
        result = cursor.fetchone()
        conn.close()
        
        highest_block = result['highest_block'] if result['highest_block'] is not None else 0
        
        return jsonify({
            'success': True,
            'chain': name,
            'highest_block': highest_block
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/<name>/get_block_txs', methods=['GET'])
@require_token
def get_block_txs(name):
    """Get blocks and type4 transactions in the specified range
    
    Parameters:
        start_block: int - starting block number
        end_block: int - ending block number
    
    Returns:
        List of blocks with their type4 transactions
    """
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        start_block = request.args.get('start_block', type=int)
        end_block = request.args.get('end_block', type=int)
        
        if start_block is None or end_block is None:
            return jsonify({
                'success': False,
                'error': 'start_block and end_block parameters are required'
            }), 400
        
        if start_block > end_block:
            return jsonify({
                'success': False,
                'error': 'start_block must be less than or equal to end_block'
            }), 400
        
        conn = get_block_db_connection(name)
        cursor = conn.cursor()
        
        # Get blocks in the range
        cursor.execute("""
            SELECT block_number, tx_count, type4_tx_count, timestamp
            FROM blocks
            WHERE block_number >= ? AND block_number <= ?
            ORDER BY block_number ASC
        """, (start_block, end_block))
        
        blocks = []
        for row in cursor.fetchall():
            block = {
                'block_number': row['block_number'],
                'tx_count': row['tx_count'],
                'type4_tx_count': row['type4_tx_count'],
                'timestamp': row['timestamp'],
                'type4_txs': []
            }
            
            # Get type4 transactions for this block
            cursor.execute("""
                SELECT tx_hash, tx_data
                FROM type4_transactions
                WHERE block_number = ?
            """, (row['block_number'],))
            
            for tx_row in cursor.fetchall():
                block['type4_txs'].append({
                    'tx_hash': tx_row['tx_hash'],
                    'tx_data': tx_row['tx_data']
                })
            
            blocks.append(block)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'chain': name,
            'blocks': blocks,
            'count': len(blocks)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/<name>/get_tvl', methods=['GET'])
@require_token
def get_tvl(name):
    """Get TVL data updated after the specified timestamp
    
    Parameters:
        last_update_timestamp: int - last update timestamp (Unix timestamp)
    
    Returns:
        List of author balances (max 10000 rows)
    """
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        last_update_timestamp = request.args.get('last_update_timestamp', type=int, default=0)
        
        conn = get_tvl_db_connection(name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT author_address, eth_balance, weth_balance, wbtc_balance,
                   usdt_balance, usdc_balance, dai_balance, timestamp, last_update_timestamp
            FROM author_balances
            WHERE last_update_timestamp > ?
            ORDER BY last_update_timestamp ASC
            LIMIT 10000
        """, (last_update_timestamp,))
        
        tvl_data = []
        for row in cursor.fetchall():
            tvl_data.append({
                'author_address': row['author_address'],
                'eth_balance': row['eth_balance'],
                'weth_balance': row['weth_balance'],
                'wbtc_balance': row['wbtc_balance'],
                'usdt_balance': row['usdt_balance'],
                'usdc_balance': row['usdc_balance'],
                'dai_balance': row['dai_balance'],
                'timestamp': row['timestamp'],
                'last_update_timestamp': row['last_update_timestamp']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'chain': name,
            'tvl_data': tvl_data,
            'count': len(tvl_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/<name>/get_code', methods=['GET'])
@require_token
def get_code(name):
    """Get code data updated after the specified timestamp
    
    Parameters:
        last_update_timestamp: int - last update timestamp (Unix timestamp)
    
    Returns:
        List of code data (max 10000 rows)
    """
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        last_update_timestamp = request.args.get('last_update_timestamp', type=int, default=0)
        
        conn = get_code_db_connection(name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT code_address, code, timestamp, last_update_timestamp
            FROM codes
            WHERE last_update_timestamp >= ?
            ORDER BY last_update_timestamp ASC
            LIMIT 10000
        """, (last_update_timestamp,))
        
        code_data = []
        for row in cursor.fetchall():
            code_data.append({
                'code_address': row['code_address'],
                'code': row['code'],
                'timestamp': row['timestamp'],
                'last_update_timestamp': row['last_update_timestamp']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'chain': name,
            'code_data': code_data,
            'count': len(code_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/<name>/add_tvl_addresses', methods=['POST'])
@require_token
def add_tvl_addresses(name):
    """Batch add addresses to TVL database
    
    Request body:
        addresses: list of address strings
    
    Returns:
        Success status and count of added addresses
    """
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        data = request.get_json()
        if not data or 'addresses' not in data:
            return jsonify({
                'success': False,
                'error': 'addresses field is required in request body'
            }), 400
        
        addresses = data['addresses']
        if not isinstance(addresses, list):
            return jsonify({
                'success': False,
                'error': 'addresses must be a list'
            }), 400
        
        if len(addresses) == 0:
            return jsonify({
                'success': True,
                'chain': name,
                'added_count': 0,
                'message': 'No addresses provided'
            })
        
        # Get TVL database connection
        conn = get_tvl_db_connection(name)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(author_balances)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Batch insert addresses
        import time as time_module
        current_timestamp = int(time_module.time())
        added_count = 0
        
        for address in addresses:
            try:
                # Insert with default values
                cursor.execute("""
                    INSERT OR IGNORE INTO author_balances 
                    (author_address, eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp, last_update_timestamp)
                    VALUES (?, 0, 0, 0, 0, 0, 0, ?, ?)
                """, (address, current_timestamp, current_timestamp))
                if cursor.rowcount > 0:
                    added_count += 1
            except Exception as e:
                print(f"Error adding TVL address {address}: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'chain': name,
            'added_count': added_count,
            'total_addresses': len(addresses)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/<name>/add_code_addresses', methods=['POST'])
@require_token
def add_code_addresses(name):
    """Batch add addresses to code database
    
    Request body:
        addresses: list of address strings
    
    Returns:
        Success status and count of added addresses
    """
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        data = request.get_json()
        if not data or 'addresses' not in data:
            return jsonify({
                'success': False,
                'error': 'addresses field is required in request body'
            }), 400
        
        addresses = data['addresses']
        if not isinstance(addresses, list):
            return jsonify({
                'success': False,
                'error': 'addresses must be a list'
            }), 400
        
        if len(addresses) == 0:
            return jsonify({
                'success': True,
                'chain': name,
                'added_count': 0,
                'message': 'No addresses provided'
            })
        
        # Get code database connection
        conn = get_code_db_connection(name)
        cursor = conn.cursor()
        
        # Batch insert addresses
        import time as time_module
        current_timestamp = int(time_module.time())
        added_count = 0
        
        for address in addresses:
            try:
                # Insert with empty code
                cursor.execute("""
                    INSERT OR IGNORE INTO codes 
                    (code_address, code, timestamp, last_update_timestamp)
                    VALUES (?, '', ?, ?)
                """, (address, current_timestamp, current_timestamp))
                if cursor.rowcount > 0:
                    added_count += 1
            except Exception as e:
                print(f"Error adding code address {address}: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'chain': name,
            'added_count': added_count,
            'total_addresses': len(addresses)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Starting syncer server on port {PORT}")
    print(f"Allowed chains: {', '.join(ALLOWED_NAMES)}")
    print(f"Block DB path: {BLOCK_DB_PATH if BLOCK_DB_PATH else 'current directory'}")
    if AUTH_TOKEN:
        print(f"Authentication: ENABLED (token loaded)")
    else:
        print(f"Authentication: DISABLED (no token.txt found)")
    print("")
    app.run(host='0.0.0.0', port=PORT, debug=False)

