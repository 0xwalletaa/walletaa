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

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='处理区块链交易数据')
parser.add_argument('--name', help='区块链网络名称')
parser.add_argument('--endpoints', nargs='+',  help='Web3 端点列表')

parser.add_argument('--num_threads', type=int, default=4, help='并行线程数')
parser.add_argument('--data_expiry', type=int, default=86400000, help='数据过期时间（秒）')

args = parser.parse_args()

NAME = args.name
WEB3_ENPOINTS = args.endpoints

# 并行线程数
NUM_THREADS = args.num_threads
# 数据过期时间（秒）
DATA_EXPIRY = args.data_expiry

web3s = [
    Web3(Web3.HTTPProvider(endpoint)) for endpoint in WEB3_ENPOINTS
]

block_db_path = f'{NAME}_block.db'
code_db_path = f'{NAME}_code.db'

# 创建一个线程本地存储
thread_local = threading.local()

def get_db_connection():
    """获取线程本地的数据库连接"""
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect(code_db_path)
        # 创建表存储author余额信息（如果不存在）
        cursor = thread_local.db_connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            code_address TEXT PRIMARY KEY,
            code TEXT,
            timestamp INTEGER
        )
        ''')
        thread_local.db_connection.commit()
    return thread_local.db_connection

def get_code_addresses():
    """从mainnet_blocks数据库获取所有code地址"""
    code_addresses = set()
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(block_db_path)
        cursor = conn.cursor()
        
        # 获取所有type4交易数据
        cursor.execute("SELECT tx_data FROM type4_transactions")
        tx_data_list = cursor.fetchall()
        
        # 遍历所有交易数据
        for (tx_data_str,) in tx_data_list:
            try:
                tx_data = json.loads(tx_data_str)
                
                # 检查是否有authorizationList字段
                if 'authorizationList' in tx_data and tx_data['authorizationList']:
                    for auth in tx_data['authorizationList']:
                        code_addresses.add(auth['address'])
            except json.JSONDecodeError as e:
                print(f"解析交易数据时出错: {e}")
                continue
        
        conn.close()
        print(f"从数据库中获取到 {len(code_addresses)} 个唯一code地址")
        return list(code_addresses)
    except Exception as e:
        print(f"获取code地址时出错: {e}")
        return []

def get_code(code_address):
    """获取指定地址的代码"""
    try:
        # 随机选择一个Web3节点
        web3 = random.choice(web3s)
        code = web3.eth.get_code(Web3.to_checksum_address(code_address))
        return HexBytes(code).hex()
    except Exception as e:
        print(f"获取地址 {code_address} 代码时出错: {e}")
        return None

def is_data_fresh(code_address):
    """检查数据是否在过期时间内"""
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
    """更新作者地址的代码信息"""
    try:
        # 获取代码
        code = get_code(code_address)
        print(f"获取到地址 {code_address} 的代码: {code}")
        
        if code is not None:
            # 更新数据库
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO codes (code_address, code, timestamp) 
                VALUES (?, ?, ?) 
                ON CONFLICT(code_address) 
                DO UPDATE SET code = ?, timestamp = ?
                """,
                (code_address, code, int(time.time()), code, int(time.time()))
            )
            conn.commit()
            print(f"已更新地址 {code_address} 的代码: {code}")
    except Exception as e:
        print(f"更新地址 {code_address} 信息时出错: {e}")

def main():
    # 初始化数据库连接（主线程）
    get_db_connection()
    
    # 获取所有author地址
    time_start = time.time()
    code_addresses = get_code_addresses()
    time_end = time.time()  
    print(f"获取到 {len(code_addresses)} 个code地址，用时 {time_end - time_start} 秒")

    if not code_addresses:
        print("未找到code地址，退出程序")
        return
    
    unfresh_code_addresses = []
    for address in code_addresses:
        if not is_data_fresh(address):
            print(f"地址 {address} 的代码已过期")
            unfresh_code_addresses.append(address)
    
    # 使用线程池并行获取余额
    print(f"开始更新 {len(unfresh_code_addresses)} 个地址的代码数据...")
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for address in unfresh_code_addresses:
            futures.append(
                executor.submit(update_code, address)
            )
        
        # 等待所有任务完成
        for future in futures:
            try:
                future.result()
                success_count += 1
                if success_count % 100 == 0:
                    print(f"已处理 {success_count} 个地址...")
            except Exception as e:
                print(f"处理地址时出错: {e}")
                error_count += 1
    
    print(f"\n处理完成! 成功: {success_count}, 失败: {error_count}")
    
    print("\n程序完成")

if __name__ == "__main__":
    main() 