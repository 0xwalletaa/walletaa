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

# 连接到Sepolia测试网的节点列表
web3s = [
    Web3(Web3.HTTPProvider("https://api.zan.top/eth-sepolia")),
    Web3(Web3.HTTPProvider("https://endpoints.omniatech.io/v1/eth/sepolia/public")),
    Web3(Web3.HTTPProvider("https://eth-sepolia.public.blastapi.io")),
    Web3(Web3.HTTPProvider("https://sepolia.drpc.org")),
    Web3(Web3.HTTPProvider("https://0xrpc.io/sep"))
]

# 并行线程数
NUM_THREADS = 4
# 数据过期时间（秒）
DATA_EXPIRY = 86400  # 24小时

# 创建一个线程本地存储
thread_local = threading.local()

def ecrecover(r, s, y_parity):
    """从签名参数恢复以太坊地址"""
    try:
        # 将r, s转换为字节并确保长度正确
        r_bytes = HexBytes(r) if not isinstance(r, bytes) else r
        s_bytes = HexBytes(s) if not isinstance(s, bytes) else s
        
        # 确保r和s是32字节长度
        if len(r_bytes) != 32:
            r_bytes = r_bytes.rjust(32, b'\0') if len(r_bytes) < 32 else r_bytes[-32:]
        if len(s_bytes) != 32:
            s_bytes = s_bytes.rjust(32, b'\0') if len(s_bytes) < 32 else s_bytes[-32:]
        
        # 确保y_parity是单字节(0或1)
        if isinstance(y_parity, int):
            y_parity = y_parity & 1  # 确保只有最低位
        else:
            y_parity = 0  # 默认值
        
        # 创建65字节的签名 (r[32] + s[32] + v[1])
        signature = r_bytes + s_bytes + bytes([y_parity])
        
        # 验证签名长度
        if len(signature) != 65:
            raise ValueError(f"签名长度不正确: {len(signature)}字节, 应为65字节")
        
        # 使用coincurve恢复公钥（这里使用零哈希作为消息）
        null_msg_hash = b'\x00' * 32
        public_key = coincurve.PublicKey.from_signature_and_message(
            signature,
            null_msg_hash,
            hasher=None
        )
        
        # 从公钥计算以太坊地址
        public_key_bytes = public_key.format(compressed=False)[1:]
        address = '0x' + hashlib.sha3_256(public_key_bytes).digest()[-20:].hex()
        return to_checksum_address(address)
    except Exception as e:
        print(f"ecrecover错误: {e}")
        return None

def get_db_connection():
    """获取线程本地的数据库连接"""
    if not hasattr(thread_local, "db_connection"):
        thread_local.db_connection = sqlite3.connect('author_tvl.db')
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
    """从sepolia_blocks数据库获取所有author地址"""
    author_addresses = set()
    
    try:
        # 连接到数据库
        conn = sqlite3.connect('sepolia_blocks.db')
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
                            # 确保r和s是有效的十六进制字符串
                            if not all(k in auth for k in ('r', 's', 'yParity')):
                                continue
                                
                            # 尝试转换yParity
                            if isinstance(auth['yParity'], str):
                                if auth['yParity'].startswith('0x'):
                                    y_parity = int(auth['yParity'], 16)
                                else:
                                    y_parity = int(auth['yParity'])
                            else:
                                y_parity = auth['yParity']
                            
                            author = ecrecover(auth['r'], auth['s'], y_parity)
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
        # 检查数据是否需要更新
        if is_data_fresh(author_address):
            print(f"地址 {author_address} 的数据在24小时内已更新，跳过")
            return
        
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

def get_statistics():
    """获取统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM author_balances")
    total_authors = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(CAST(eth_balance AS REAL)) FROM author_balances")
    total_balance = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT author_address, eth_balance FROM author_balances ORDER BY CAST(eth_balance AS REAL) DESC LIMIT 5")
    top_balances = cursor.fetchall()
    
    return total_authors, total_balance, top_balances

def main():
    # 初始化数据库连接（主线程）
    get_db_connection()
    
    # 获取所有author地址
    author_addresses = get_author_addresses()
    
    if not author_addresses:
        print("未找到author地址，退出程序")
        return
    
    # 使用线程池并行获取余额
    print(f"开始更新 {len(author_addresses)} 个地址的余额数据...")
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = []
        for address in author_addresses:
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
    
    # 获取并显示统计信息
    total_authors, total_balance, top_balances = get_statistics()
    
    print("\n===== 统计结果 =====")
    print(f"总地址数: {total_authors}")
    print(f"总ETH余额: {total_balance:.6f}")
    
    print("\n===== 余额最高的5个地址 =====")
    for address, balance in top_balances:
        print(f"地址: {address}, 余额: {balance} ETH")
    
    print("\n程序完成")

if __name__ == "__main__":
    main() 