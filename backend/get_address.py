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
parser.add_argument('--data_expiry', type=int, default=86400, help='数据过期时间（秒）')

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
address_db_path = f'{NAME}_address.db'

# 创建一个线程本地存储
thread_local = threading.local()

def ecrecover(auth):
    chain_id = to_bytes(hexstr=auth['chainId'])
    address_bytes = to_bytes(hexstr=auth['address'])
    nonce = to_bytes(hexstr=auth['nonce'])

    # RLP 编码 [chain_id, address, nonce]
    encoded_data = rlp.encode([chain_id, address_bytes, nonce])

    # 构造 EIP-7702 消息：0x05 || rlp(...)
    message_bytes = b'\x05' + encoded_data
    # 计算 Keccak-256 哈希
    message_hash = keccak(message_bytes)

    # 将签名组件转换为标准格式
    r_bytes = HexBytes(auth['r'])
    s_bytes = HexBytes(auth['s'])
    # yParity (0 or 1) is used directly
    y_parity = int(auth['yParity'], 16)

    # 创建vrs元组
    vrs = (y_parity, r_bytes, s_bytes)
    recovered_address = Account()._recover_hash(message_hash, vrs=vrs)
    
    return recovered_address

def get_db_connection():
    """获取线程本地的数据库连接"""
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect(address_db_path)
        # 创建表存储author余额信息（如果不存在）
        cursor = thread_local.db_connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS author_balances (
            author_address TEXT PRIMARY KEY,
            eth_balance TEXT,
            timestamp INTEGER
        )
        ''')
        thread_local.db_connection.commit()
    return thread_local.db_connection

def get_author_addresses():
    """从mainnet_blocks数据库获取所有author地址"""
    author_addresses = set()
    
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
                        try:
                            author = ecrecover(auth)
                            if author:
                                author_addresses.add(author.lower())
                        except Exception as e:
                            print(f"处理签名恢复时出错: {e}, 数据: {auth}")
                            continue
            except json.JSONDecodeError as e:
                print(f"解析交易数据时出错: {e}")
                continue
        
        conn.close()
        print(f"从数据库中获取到 {len(author_addresses)} 个唯一author地址")
        return list(author_addresses)
    except Exception as e:
        print(f"获取author地址时出错: {e}")
        return []

def get_address_balance(author_address):
    """获取指定地址的ETH余额"""
    try:
        # 随机选择一个Web3节点
        web3 = random.choice(web3s)
        balance_wei = web3.eth.get_balance(Web3.to_checksum_address(author_address))
        balance_eth = web3.from_wei(balance_wei, 'ether')
        return str(balance_eth)
    except Exception as e:
        print(f"获取地址 {author_address} 余额时出错: {e}")
        return None

def is_data_fresh(author_address):
    """检查数据是否在过期时间内"""
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

def update_author_balance(author_address):
    """更新作者地址的余额信息"""
    try:
        # 获取余额
        balance = get_address_balance(author_address)
        
        if balance is not None:
            # 更新数据库
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO author_balances (author_address, eth_balance, timestamp) 
                VALUES (?, ?, ?) 
                ON CONFLICT(author_address) 
                DO UPDATE SET eth_balance = ?, timestamp = ?
                """,
                (author_address, balance, int(time.time()), balance, int(time.time()))
            )
            conn.commit()
            print(f"已更新地址 {author_address} 的余额: {balance} ETH")
    except Exception as e:
        print(f"更新地址 {author_address} 信息时出错: {e}")

def main():
    # 初始化数据库连接（主线程）
    get_db_connection()
    
    # 获取所有author地址
    author_addresses = get_author_addresses()
    
    if not author_addresses:
        print("未找到author地址，退出程序")
        return
    
    unfresh_author_addresses = []
    for address in author_addresses:
        if not is_data_fresh(address):
            unfresh_author_addresses.append(address)
    
    # 使用线程池并行获取余额
    print(f"开始更新 {len(unfresh_author_addresses)} 个地址的余额数据...")
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for address in unfresh_author_addresses:
            futures.append(
                executor.submit(update_author_balance, address)
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