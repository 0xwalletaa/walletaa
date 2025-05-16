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

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='处理区块链交易数据')
parser.add_argument('--name', help='区块链网络名称')
parser.add_argument('--endpoints', nargs='+',  help='Web3 端点列表')
parser.add_argument('--start_block', type=int, help='起始区块号')
parser.add_argument('--num_threads', type=int, default=4, help='并行线程数')

args = parser.parse_args()

NAME = args.name
WEB3_ENPOINTS = args.endpoints
START_BLOCK = args.start_block
NUM_THREADS = args.num_threads

block_db_path = f'{NAME}_block.db'

web3s = [
    Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 10})) for endpoint in WEB3_ENPOINTS
]

# 创建一个线程本地存储
thread_local = threading.local()

if NAME == 'bsc':
    from web3.middleware import ExtraDataToPOAMiddleware
    for i in range(len(web3s)):
        web3s[i].middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# 辅助函数：处理HexBytes对象的JSON序列化
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
            # 处理任何类似字典的对象(包括AttributeDict)
            result[key] = serialize_web3_tx(dict(value))
        else:
            result[key] = value
    return result

# 获取线程本地的数据库连接
def get_db_connection():
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect(block_db_path)
    return thread_local.db_connection

# 初始化数据库
def init_db():
    conn = sqlite3.connect(block_db_path)
    cursor = conn.cursor()
    
    # 检查blocks表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blocks'")
    if not cursor.fetchone():
        # 创建区块表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            block_number INTEGER PRIMARY KEY,
            tx_count INTEGER,
            type4_tx_count INTEGER,
            timestamp INTEGER
        )
        ''')
        print("创建blocks表")
    
    # 检查type4_transactions表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='type4_transactions'")
    if not cursor.fetchone():
        # 创建交易表 (只存储type=4的交易)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS type4_transactions (
            tx_hash TEXT PRIMARY KEY,
            block_number INTEGER,
            tx_data TEXT,
            FOREIGN KEY (block_number) REFERENCES blocks(block_number)
        )
        ''')
        print("创建type4_transactions表")
    
    conn.commit()
    return conn

# 检查区块是否已存在于数据库中
def is_block_exists(conn, block_number):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM blocks WHERE block_number = ?", (block_number,))
    return cursor.fetchone() is not None

# 处理并存储区块信息
def process_block(block_number):
    conn = get_db_connection()
    try:
        # 获取完整区块信息
        block = random.choice(web3s).eth.get_block(block_number, full_transactions=True)
        transactions = block.transactions
        
        # 计算type=4的交易数量
        type4_count = 0
        type4_txs = []
        
        for tx in transactions:
            tx_type = getattr(tx, 'type', 0)
            if tx_type == 4:
                type4_count += 1
                tx_hash = tx.hash.hex()
                # 使用自定义函数处理HexBytes序列化问题
                tx_data = json.dumps(serialize_web3_tx(dict(tx)))
                type4_txs.append((tx_hash, block_number, tx_data))
        
        # 存储区块信息
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO blocks (block_number, tx_count, type4_tx_count, timestamp) VALUES (?, ?, ?, ?)",
            (block_number, len(transactions), type4_count, block.timestamp)
        )
        
        # 存储type=4的交易
        if type4_txs:
            cursor.executemany(
                "INSERT INTO type4_transactions (tx_hash, block_number, tx_data) VALUES (?, ?, ?)",
                type4_txs
            )
        
        conn.commit()
        print(f"区块 #{block_number} 已处理: 共 {len(transactions)} 笔交易，其中 {type4_count} 笔type=4交易")
        return True
    
    except Exception as e:
        print(f"处理区块 #{block_number} 时出错: {str(e)}")
        conn.rollback()
        return False

def process_block_with_retry(block_number):
    # 重试机制
    max_retries = 3
    for retry in range(max_retries):
        if process_block(block_number):
            return True
        else:
            print(f"重试处理区块 #{block_number}，第 {retry+1}/{max_retries} 次尝试")
    return False

def main():
    # 初始化数据库
    conn = init_db()
    
    try:
        # 获取最新区块号
        latest_block = random.choice(web3s).eth.block_number
        print(f"当前最新区块: {latest_block}")
        
        blocks_needed = []
        for block_number in range(START_BLOCK, latest_block):
            if not is_block_exists(conn, block_number):
                blocks_needed.append(block_number)
                if len(blocks_needed) > 10000:
                    break
                
        print(f"需要处理的区块数: {len(blocks_needed)}")
        time.sleep(1)

        # 使用线程池并行处理区块
        print(f"开始使用 {NUM_THREADS} 个线程并行处理区块...")
        success_count = 0
        error_count = 0
        
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = []
            for block_number in blocks_needed:
                futures.append(
                    executor.submit(process_block_with_retry, block_number)
                )
            
            # 等待所有任务完成
            for future in futures:
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    if (success_count + error_count) % 10 == 0:
                        print(f"已处理 {success_count + error_count} 个区块, 成功: {success_count}, 失败: {error_count}")
                except Exception as e:
                    print(f"处理区块时出错: {e}")
                    error_count += 1
        
        print(f"\n处理完成! 成功: {success_count}, 失败: {error_count}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
