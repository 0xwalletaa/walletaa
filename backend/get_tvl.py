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

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='处理区块链交易数据')
parser.add_argument('--name', help='区块链网络名称')
parser.add_argument('--endpoints', nargs='+',  help='Web3 端点列表')
parser.add_argument('--contract', required=True, help='合约地址')
parser.add_argument('--num_threads', type=int, default=4, help='并行线程数')
parser.add_argument('--data_expiry', type=int, default=864000, help='数据过期时间（秒）')
parser.add_argument('--limit', type=int, default=10000, help='限制处理数量')

args = parser.parse_args()

NAME = args.name
WEB3_ENPOINTS = args.endpoints
CONTRACT_ADDRESS = args.contract

# 并行线程数
NUM_THREADS = args.num_threads
# 数据过期时间（秒）
DATA_EXPIRY = args.data_expiry
# 限制处理数量
LIMIT = args.limit

web3s = [
    Web3(Web3.HTTPProvider(endpoint)) for endpoint in WEB3_ENPOINTS
]

block_db_path = f'{NAME}_block.db'
tvl_db_path = f'{NAME}_tvl.db'

# another db
info_db_path = f'../server/db/{NAME}.db'

# 创建一个线程本地存储
thread_local = threading.local()

# 合约地址和ABI配置
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
        thread_local.db_connection = sqlite3.connect(tvl_db_path)
        # 创建表存储author余额信息（如果不存在）
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
    
    """从info_db_path获取所有author地址"""
    if os.path.exists(info_db_path):
        conn = sqlite3.connect(info_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT authorizer_address FROM authorizers")
        for row in cursor:
            if not is_data_fresh(row[0]):
                author_addresses.add(row[0])
            if len(author_addresses) >= LIMIT:
                break
        conn.close()
        print(f"从info_db_path获取到 {len(author_addresses)} 个author地址")
        print(author_addresses)
        return list(author_addresses)
    
    """从mainnet_blocks数据库获取所有author地址"""
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(block_db_path)
        cursor = conn.cursor()
        
        # 获取所有type4交易数据
        cursor.execute("SELECT tx_data FROM type4_transactions")
        
        # 遍历所有交易数据
        for (tx_data_str,) in cursor:
            try:
                tx_data = json.loads(tx_data_str)
                
                # 检查是否有authorizationList字段
                if 'authorizationList' in tx_data and tx_data['authorizationList']:
                    for auth in tx_data['authorizationList']:
                        try:
                            author = ecrecover(auth)
                            if author and not is_data_fresh(author.lower()):
                                author_addresses.add(author.lower())
                        except Exception as e:
                            print(f"处理签名恢复时出错: {e}, 数据: {auth}")
                            continue
                
                if len(author_addresses) >= LIMIT:
                    break
            except json.JSONDecodeError as e:
                print(f"解析交易数据时出错: {e}")
                continue
        
        conn.close()
        print(f"从数据库中获取到 {len(author_addresses)} 个唯一author地址")
        return list(author_addresses)
    except Exception as e:
        print(f"获取author地址时出错: {e}")
        return []

def get_address_balances(author_addresses):
    """批量获取指定地址列表的所有代币余额"""
    try:
        # 随机选择一个Web3节点
        web3 = random.choice(web3s)
        
        # 创建合约实例
        contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        
        # 将地址转换为checksum格式
        checksum_addresses = [Web3.to_checksum_address(addr) for addr in author_addresses]
        
        # 调用合约获取所有代币余额
        result = contract.functions.get(checksum_addresses).call()
        
        # 解析结果
        all_balances = {}
        for i, address in enumerate(author_addresses):
            balances = result[i]
            all_balances[address] = {
                'eth_balance': str(web3.from_wei(balances[0], 'ether')),
                'weth_balance': str(web3.from_wei(balances[1], 'ether')),
                'wbtc_balance': str(balances[2] / (10 ** 8)),  # WBTC使用8位小数
                'usdt_balance': str(web3.from_wei(balances[3], 'mwei')),
                'usdc_balance': str(web3.from_wei(balances[4], 'mwei')),
                'dai_balance': str(web3.from_wei(balances[5], 'ether'))
            }
        
        return all_balances
    except Exception as e:
        print(f"批量获取地址余额时出错: {e} from {web3.provider.endpoint_uri}")
        return None

def is_data_fresh(author_address):
    """检查数据是否在过期时间内"""
    if author_address == 'error':
        return True
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
    """更新作者地址的余额信息"""
    try:
        # 获取所有代币余额
        balances = get_address_balances(author_addresses)
        
        if balances is not None:
            # 更新数据库
            conn = get_db_connection()
            cursor = conn.cursor()
            current_time = int(time.time())
            
            for address, balance in balances.items():
                cursor.execute(
                    """
                    INSERT INTO author_balances (
                        author_address, 
                        eth_balance, 
                        weth_balance,
                        wbtc_balance,
                        usdt_balance,
                        usdc_balance,
                        dai_balance,
                        timestamp
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
                    ON CONFLICT(author_address) 
                    DO UPDATE SET 
                        eth_balance = ?,
                        weth_balance = ?,
                        wbtc_balance = ?,
                        usdt_balance = ?,
                        usdc_balance = ?,
                        dai_balance = ?,
                        timestamp = ?
                    """,
                    (
                        address,
                        balance['eth_balance'],
                        balance['weth_balance'],
                        balance['wbtc_balance'],
                        balance['usdt_balance'],
                        balance['usdc_balance'],
                        balance['dai_balance'],
                        current_time,
                        balance['eth_balance'],
                        balance['weth_balance'],
                        balance['wbtc_balance'],
                        balance['usdt_balance'],
                        balance['usdc_balance'],
                        balance['dai_balance'],
                        current_time
                    )
                )
            conn.commit()
            print(f"已批量更新 {len(author_addresses)} 个地址的余额")
            for address, balance in balances.items():
                print(f"{address}: ETH={balance['eth_balance']}, WETH={balance['weth_balance']}, WBTC={balance['wbtc_balance']}, USDT={balance['usdt_balance']}, USDC={balance['usdc_balance']}, DAI={balance['dai_balance']}")
    except Exception as e:
        print(f"更新地址 {', '.join(author_addresses)} 信息时出错: {e}")

def main():
    # 初始化数据库连接（主线程）
    get_db_connection()
    
    # 获取所有author地址
    time_start = time.time()
    unfresh_author_addresses = get_author_addresses()
    time_end = time.time()  
    print(f"获取到 {len(unfresh_author_addresses)} 个author地址，用时 {time_end - time_start} 秒")
    
    if not unfresh_author_addresses:
        print("未找到author地址，退出程序")
        return
    
    # 使用线程池并行获取余额
    print(f"开始更新 {len(unfresh_author_addresses)} 个地址的余额数据...")
    success_count = 0
    error_count = 0
    
    unfresh_author_addresses_split_by_100 = [unfresh_author_addresses[i:i+100] for i in range(0, len(unfresh_author_addresses), 100)]
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for addresses in unfresh_author_addresses_split_by_100:
            futures.append(
                executor.submit(update_author_balance, addresses)
            )
        
        # 等待所有任务完成
        for future in futures:
            try:
                future.result()
                success_count += 1
                if success_count % 100 == 0:
                    print(f"已处理 {success_count} 批地址...")
            except Exception as e:
                print(f"处理地址时出错: {e}")
                error_count += 1
    
    print(f"\n处理完成! 成功: {success_count}, 失败: {error_count}")
    
    print("\n程序完成")

if __name__ == "__main__":
    main() 