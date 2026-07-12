#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sqlite3
from flask import Flask, jsonify, request
import argparse
from functools import wraps
import watermark
import time
import threading
from collections import deque, defaultdict

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

def parse_blocks_string(blocks_str):
    """解析块字符串，如 '3,5,7,9,12-20,23-55' 返回块号列表
    
    Args:
        blocks_str: 块字符串，支持单个块号和范围
        
    Returns:
        list: 排序后的块号列表
    """
    if not blocks_str or blocks_str.strip() == '':
        return []
    
    block_numbers = set()
    parts = blocks_str.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            # 处理范围，如 12-20
            try:
                start, end = part.split('-', 1)
                start_num = int(start.strip())
                end_num = int(end.strip())
                if start_num <= end_num:
                    block_numbers.update(range(start_num, end_num + 1))
            except ValueError:
                continue
        else:
            # 处理单个块号
            try:
                block_numbers.add(int(part))
            except ValueError:
                continue
    
    return sorted(list(block_numbers))

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

@app.route('/<name>/get_block_txs', methods=['POST'])
@require_token
def get_block_txs(name):
    """Get blocks and type4 transactions for specified blocks
    
    Request body:
        blocks: string - 块字符串，支持零散块号和区间
                例如: '3,5,7,9,12-20,23-55'
    
    Returns:
        List of blocks with their type4 transactions
    """
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        data = request.get_json()
        if not data or 'blocks' not in data:
            return jsonify({
                'success': False,
                'error': 'blocks field is required in request body (e.g., "3,5,7,9,12-20,23-55")'
            }), 400
        
        blocks_str = data['blocks']
        
        if not blocks_str:
            return jsonify({
                'success': False,
                'error': 'blocks parameter cannot be empty'
            }), 400
        
        # 解析块字符串
        block_numbers = parse_blocks_string(blocks_str)
        
        if not block_numbers:
            return jsonify({
                'success': False,
                'error': 'No valid block numbers found in blocks parameter'
            }), 400
        
        conn = get_block_db_connection(name)
        cursor = conn.cursor()
        
        # 为了性能，使用 IN 查询
        placeholders = ','.join(['?'] * len(block_numbers))
        cursor.execute(f"""
            SELECT block_number, tx_count, type4_tx_count, timestamp
            FROM blocks
            WHERE block_number IN ({placeholders})
            ORDER BY block_number ASC
        """, block_numbers)
        
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
            'count': len(blocks),
            'requested_count': len(block_numbers)
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

        _record_stats(name, 'tvl_down', updated=len(tvl_data), ok=1)
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

        _record_stats(name, 'code_down', updated=len(code_data), ok=1)
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
        existed_data = []
        
        for address in addresses:
            try:
                # Try to insert with default values
                cursor.execute("""
                    INSERT OR IGNORE INTO author_balances 
                    (author_address, eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp, last_update_timestamp)
                    VALUES (?, 0, 0, 0, 0, 0, 0, ?, ?)
                """, (address, 0, current_timestamp))
                if cursor.rowcount > 0:
                    added_count += 1
                else:
                    # Address already exists, read its data
                    cursor.execute("""
                        SELECT author_address, eth_balance, weth_balance, wbtc_balance,
                               usdt_balance, usdc_balance, dai_balance, timestamp, last_update_timestamp
                        FROM author_balances
                        WHERE author_address = ?
                    """, (address,))
                    row = cursor.fetchone()
                    if row:
                        existed_data.append({
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
            except Exception as e:
                print(f"Error adding TVL address {address}: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'chain': name,
            'added_count': added_count,
            'total_addresses': len(addresses),
            'existed': existed_data,
            'existed_count': len(existed_data)
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
        existed_data = []
        
        for address in addresses:
            try:
                # Try to insert with empty code
                cursor.execute("""
                    INSERT OR IGNORE INTO codes 
                    (code_address, code, timestamp, last_update_timestamp)
                    VALUES (?, '', ?, ?)
                """, (address, 0, current_timestamp))
                if cursor.rowcount > 0:
                    added_count += 1
                else:
                    # Address already exists, read its data
                    cursor.execute("""
                        SELECT code_address, code, timestamp, last_update_timestamp
                        FROM codes
                        WHERE code_address = ?
                    """, (address,))
                    row = cursor.fetchone()
                    if row:
                        existed_data.append({
                            'code_address': row['code_address'],
                            'code': row['code'],
                            'timestamp': row['timestamp'],
                            'last_update_timestamp': row['last_update_timestamp']
                        })
            except Exception as e:
                print(f"Error adding code address {address}: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'chain': name,
            'added_count': added_count,
            'total_addresses': len(addresses),
            'existed': existed_data,
            'existed_count': len(existed_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/<name>/confirm_height', methods=['POST'])
@require_token
def confirm_height(name):
    """接收本地上报的确认高度: 该高度以下的块本地已全部下载+解析+验证。

    收到时只记录 {name}_confirmed_{height} 文件 (只前进), 不做任何删除;
    实际瘦身由 clean_block.py 在抓块循环的安静点执行。
    """
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    try:
        data = request.get_json()
        if not data or 'height' not in data:
            return jsonify({
                'success': False,
                'error': 'height field is required in request body'
            }), 400

        height = int(data['height'])
        if height <= 0:
            return jsonify({'success': False, 'error': 'height must be positive'}), 400

        block_db_path, _, _ = get_db_paths(name)
        db_dir = os.path.dirname(os.path.abspath(block_db_path))
        effective = watermark.write_confirmed(db_dir, name, height)

        return jsonify({
            'success': True,
            'chain': name,
            'confirmed_height': effective
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/<name>/delete_wrong_block', methods=['POST'])
@require_token
def delete_wrong_block(name):
    """Delete wrong blocks and their type4 transactions
    
    Request body:
        block_numbers: list of block numbers to delete
    
    Returns:
        Success status and count of deleted blocks
    """
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        data = request.get_json()
        if not data or 'block_numbers' not in data:
            return jsonify({
                'success': False,
                'error': 'block_numbers field is required in request body'
            }), 400
        
        block_numbers = data['block_numbers']
        if not isinstance(block_numbers, list):
            return jsonify({
                'success': False,
                'error': 'block_numbers must be a list'
            }), 400
        
        if len(block_numbers) == 0:
            return jsonify({
                'success': True,
                'chain': name,
                'deleted_blocks': 0,
                'deleted_transactions': 0,
                'message': 'No block numbers provided'
            })
        
        # Get block database connection
        conn = get_block_db_connection(name)
        cursor = conn.cursor()
        
        deleted_blocks = 0
        deleted_transactions = 0
        
        for block_number in block_numbers:
            try:
                # Delete type4 transactions for this block
                cursor.execute("DELETE FROM type4_transactions WHERE block_number = ?", (block_number,))
                deleted_transactions += cursor.rowcount
                
                # Delete block
                cursor.execute("DELETE FROM blocks WHERE block_number = ?", (block_number,))
                deleted_blocks += cursor.rowcount
                
            except Exception as e:
                print(f"Error deleting block {block_number}: {e}")
        
        conn.commit()
        conn.close()

        # 回退水位线: 否则被删的块在 get_block 的水位线之前, 永远不会被重新获取
        try:
            block_db_path, _, _ = get_db_paths(name)
            db_dir = os.path.dirname(os.path.abspath(block_db_path))
            watermark.rollback_watermark(db_dir, name, min(block_numbers) - 1)
        except Exception as e:
            print(f"Error rolling back watermark for {name}: {e}")

        return jsonify({
            'success': True,
            'chain': name,
            'deleted_blocks': deleted_blocks,
            'deleted_transactions': deleted_transactions,
            'total_requested': len(block_numbers)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ---- 抓取脚本上报的运行统计 (纯内存, 重启即清零) ----
STATS_WINDOW = 3600  # 看板统计最近 1 小时
# block=抓块, tvl/code=余额与代码刷新 (脚本上报);
# tvl_down/code_down=本地增量拉取 (get_tvl/get_code 接口服务端直接计数)
STATS_KINDS = ('block', 'tvl', 'code', 'tvl_down', 'code_down')
STATS_LOCK = threading.Lock()
STATS_EVENTS = defaultdict(deque)  # (name, kind) -> deque[(ts, updated, success, failed)]


def _record_stats(name, kind, updated=0, ok=0, fail=0):
    """服务端内部直接记一笔统计 (与 /report_stats 同一存储)"""
    now = time.time()
    with STATS_LOCK:
        events = STATS_EVENTS[(name, kind)]
        events.append((now, updated, ok, fail))
        _prune_stats(events, now)


def _prune_stats(events, now):
    while events and now - events[0][0] > STATS_WINDOW * 2:
        events.popleft()


@app.route('/<name>/report_stats', methods=['POST'])
@require_token
def report_stats(name):
    """接收抓取脚本上报的增量统计。

    kind 区分来源: block (get_block_batch, 不传时的默认值, 兼容旧脚本) /
    tvl (get_tvl) / code (get_code)。blocks_added 在 tvl/code 语义下是
    成功更新的记录数。
    """
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    try:
        data = request.get_json() or {}
        kind = data.get('kind', 'block')
        if kind not in STATS_KINDS:
            return jsonify({'success': False,
                            'error': f'unknown kind: {kind}'}), 400
        updated = int(data.get('blocks_added', 0))
        success = int(data.get('success_requests', 0))
        failed = int(data.get('failed_requests', 0))
        now = time.time()
        with STATS_LOCK:
            events = STATS_EVENTS[(name, kind)]
            events.append((now, updated, success, failed))
            _prune_stats(events, now)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _stats_1h_kind(name, kind):
    """单一 kind 最近 1 小时的统计汇总"""
    now = time.time()
    updated = success = failed = 0
    with STATS_LOCK:
        events = STATS_EVENTS.get((name, kind))
        if events:
            _prune_stats(events, now)
            for ts, u, ok, fail in events:
                if now - ts <= STATS_WINDOW:
                    updated += u
                    success += ok
                    failed += fail
    return updated, success, failed


def _stats_1h(name):
    """最近 1 小时的统计汇总: block 沿用旧字段名, tvl/code 挂子字典"""
    blocks_added, success, failed = _stats_1h_kind(name, 'block')
    result = {'blocks_added': blocks_added,
              'success_requests': success,
              'failed_requests': failed}
    for kind in ('tvl', 'code', 'tvl_down', 'code_down'):
        updated, ok, fail = _stats_1h_kind(name, kind)
        result[kind] = {'updated': updated,
                        'success_requests': ok,
                        'failed_requests': fail}
    return result


def _chain_status(name):
    """收集单条链的同步状态 (只用走索引的查询, 保证看板秒开)"""
    status = {'chain': name}
    block_db_path, code_db_path, tvl_db_path = get_db_paths(name)

    try:
        if not os.path.exists(block_db_path):
            status['block'] = None
        else:
            # timeout=2: 抓取进程频繁提交时别为看板等锁太久, 拿不到就下轮再看
            conn = sqlite3.connect(block_db_path, timeout=2)
            cursor = conn.cursor()
            # 注意: MIN/MAX 必须分开查, 合并写会让 SQLite 放弃索引优化走全表扫描
            cursor.execute("SELECT MIN(block_number) FROM blocks")
            min_block = cursor.fetchone()[0]
            cursor.execute("SELECT MAX(block_number) FROM blocks")
            max_block = cursor.fetchone()[0]
            latest_timestamp = None
            if max_block is not None:
                cursor.execute("SELECT timestamp FROM blocks WHERE block_number = ?", (max_block,))
                row = cursor.fetchone()
                latest_timestamp = row[0] if row else None
            conn.close()
            status['block'] = {
                'min_block': min_block,
                'max_block': max_block,
                'latest_timestamp': latest_timestamp,
                'db_size': os.path.getsize(block_db_path),
            }
    except Exception as e:
        status['block'] = {'error': str(e)}

    for key, db_path, table in (('tvl', tvl_db_path, 'author_balances'),
                                ('code', code_db_path, 'codes')):
        try:
            if not os.path.exists(db_path):
                status[key] = None
                continue
            conn = sqlite3.connect(db_path, timeout=2)
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX(last_update_timestamp) FROM {table}")
            last_update = cursor.fetchone()[0]
            conn.close()
            status[key] = {
                'last_update_timestamp': last_update,
                'db_size': os.path.getsize(db_path),
            }
        except Exception as e:
            status[key] = {'error': str(e)}

    status['stats_1h'] = _stats_1h(name)
    return status


@app.route('/dashboard_data', methods=['GET'])
def dashboard_data():
    """看板数据: 所有链的起始块/最高块/最新块时间/库文件大小/最近1小时统计"""
    chains = [_chain_status(name) for name in sorted(ALLOWED_NAMES)]
    return jsonify({
        'success': True,
        'server_time': int(time.time()),
        'chains': chains,
    })


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WalletAA Syncer Dashboard</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; margin: 24px;
         background: #0d1117; color: #c9d1d9; }
  h1 { font-size: 20px; }
  .meta { color: #8b949e; font-size: 13px; margin-bottom: 16px; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; }
  th, td { padding: 8px 12px; border-bottom: 1px solid #21262d; text-align: right;
           font-variant-numeric: tabular-nums; white-space: nowrap; }
  th { color: #8b949e; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  .ok { color: #3fb950; }
  .warn { color: #d29922; }
  .bad { color: #f85149; }
  .dim { color: #8b949e; }
  .tablewrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  th:first-child, td:first-child {
    position: sticky; left: 0; background: #0d1117;
  }
  @media (max-width: 600px) {
    body { margin: 12px; }
    h1 { font-size: 16px; }
    th, td { padding: 6px 8px; font-size: 12px; }
  }
</style>
</head>
<body>
<h1>WalletAA Syncer Dashboard <span id="total" class="dim" style="font-size:14px; font-weight:400;"></span></h1>
<div class="meta" id="meta">loading...</div>
<div class="tablewrap">
<table>
  <thead><tr>
    <th>chain</th><th>start block</th><th>highest block</th><th>latest block time</th>
    <th>behind</th><th>blocks +1h</th><th>req ok 1h</th><th>req fail 1h</th>
    <th>tvl req 1h</th><th>code req 1h</th>
    <th>tvl dl 1h</th><th>code dl 1h</th>
    <th>block db</th><th>tvl db</th><th>code db</th>
    <th>tvl updated</th><th>code updated</th>
  </tr></thead>
  <tbody id="tbody"></tbody>
</table>
</div>
<script>
function fmtSize(b) {
  if (b == null) return '-';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (b >= 1024 && i < units.length - 1) { b /= 1024; i++; }
  return b.toFixed(1) + ' ' + units[i];
}
function fmtTime(ts) {
  if (!ts) return '-';
  return new Date(ts * 1000).toLocaleString('sv-SE');
}
function fmtBehind(ts, now) {
  if (!ts) return {text: '-', cls: 'dim'};
  let s = now - ts;
  if (s < 0) s = 0;
  const d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600),
        m = Math.floor(s % 3600 / 60);
  const text = d > 0 ? d + 'd ' + h + 'h' : (h > 0 ? h + 'h ' + m + 'm' : m + 'm');
  const cls = s < 3600 ? 'ok' : (s < 86400 ? 'warn' : 'bad');
  return {text, cls};
}
async function refresh() {
  const resp = await fetch('dashboard_data');
  const data = await resp.json();
  document.getElementById('meta').textContent =
    'server time: ' + fmtTime(data.server_time) + ' | auto refresh 30s';
  const rows = data.chains.map(c => {
    const b = c.block || {};
    const behind = fmtBehind(b.latest_timestamp, data.server_time);
    const s = c.stats_1h || {};
    const failCls = s.failed_requests > 0 ? 'bad' : 'dim';
    const addCls = s.blocks_added > 0 ? 'ok' : 'dim';
    const fmtKind = k => {
      if (!k || (!k.success_requests && !k.failed_requests)) return '<td class="dim">-</td>';
      const cls = k.failed_requests > 0 ? 'bad' : 'ok';
      return '<td class="' + cls + '" title="updated: ' + (k.updated || 0).toLocaleString() + '">' +
        k.success_requests.toLocaleString() + ' / ' + k.failed_requests.toLocaleString() + '</td>';
    };
    const fmtDown = k => {
      if (!k || !k.success_requests) return '<td class="dim">-</td>';
      return '<td class="ok" title="requests: ' + k.success_requests.toLocaleString() + '">' +
        (k.updated || 0).toLocaleString() + '</td>';
    };
    return '<tr><td>' + c.chain + '</td>' +
      '<td>' + (b.min_block != null ? b.min_block.toLocaleString() : '-') + '</td>' +
      '<td>' + (b.max_block != null ? b.max_block.toLocaleString() : '-') + '</td>' +
      '<td>' + fmtTime(b.latest_timestamp) + '</td>' +
      '<td class="' + behind.cls + '">' + behind.text + '</td>' +
      '<td class="' + addCls + '">' + (s.blocks_added || 0).toLocaleString() + '</td>' +
      '<td>' + (s.success_requests || 0).toLocaleString() + '</td>' +
      '<td class="' + failCls + '">' + (s.failed_requests || 0).toLocaleString() + '</td>' +
      fmtKind(s.tvl) + fmtKind(s.code) +
      fmtDown(s.tvl_down) + fmtDown(s.code_down) +
      '<td>' + fmtSize(b.db_size) + '</td>' +
      '<td>' + fmtSize(c.tvl ? c.tvl.db_size : null) + '</td>' +
      '<td>' + fmtSize(c.code ? c.code.db_size : null) + '</td>' +
      '<td>' + (c.tvl ? fmtTime(c.tvl.last_update_timestamp) : '-') + '</td>' +
      '<td>' + (c.code ? fmtTime(c.code.last_update_timestamp) : '-') + '</td></tr>';
  });
  const totalSize = data.chains.reduce((sum, c) =>
    sum + ((c.block && c.block.db_size) || 0) + ((c.tvl && c.tvl.db_size) || 0) +
    ((c.code && c.code.db_size) || 0), 0);
  document.getElementById('total').textContent = 'total db size: ' + fmtSize(totalSize);
  document.getElementById('tbody').innerHTML = rows.join('');
}
refresh();
setInterval(refresh, 30000);
</script>
</body>
</html>"""


@app.route('/dashboard', methods=['GET'])
def dashboard():
    """看板页面"""
    return DASHBOARD_HTML


if __name__ == '__main__':
    print(f"Starting syncer server on port {PORT}")
    print(f"Allowed chains: {', '.join(ALLOWED_NAMES)}")
    print(f"Block DB path: {BLOCK_DB_PATH if BLOCK_DB_PATH else 'current directory'}")
    if AUTH_TOKEN:
        print(f"Authentication: ENABLED (token loaded)")
    else:
        print(f"Authentication: DISABLED (no token.txt found)")
    print("")
    # threaded: tvl/code 全量刷新期间写库频繁, 单线程模式下一个慢请求
    # (或被写锁拖住的看板查询) 会堵死包括 report_stats 在内的所有请求
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)

