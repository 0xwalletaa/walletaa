#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from web3 import Web3
import time
from collections import Counter

# 连接到Sepolia测试网
# 你需要提供一个有效的Infura/Alchemy等节点URL
INFURA_URL = "https://api.zan.top/eth-sepolia"  # 替换为你的API密钥
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

def get_transaction_type(tx_hash):
    """获取交易类型"""
    tx = web3.eth.get_transaction(tx_hash)
    tx_type = tx.get('type', 0)
    return tx_type

def get_block_info(block_number):
    # 获取完整区块信息
    block = web3.eth.get_block(block_number, full_transactions=True)
    txs = block.transactions
    
    print(f"区块 #{block_number} 包含 {len(txs)} 个交易")
    
    # 处理区块中的每个交易
    for tx in txs:
        tx_hash = tx.hash if hasattr(tx, 'hash') else tx
        tx_type = getattr(tx, 'type', 0) if hasattr(tx, 'type') else get_transaction_type(tx_hash)
        
        # 输出交易信息
        print(f"  交易: {tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash}, 类型: {tx_type}")
    


def main():
    # 检查连接
    if not web3.is_connected():
        print("无法连接到Sepolia测试网，请检查你的API密钥")
        return
    
    print(f"已连接到Sepolia测试网，链ID: {web3.eth.chain_id}")
    
    # 获取最新区块号
    latest_block = web3.eth.block_number
    print(f"当前最新区块: {latest_block}")
    
    
    # 获取最近1000个区块
    for i in range(1000):
        block_number = latest_block - i
        ok = False
        while not ok:
            try:
                time.sleep(1)
                get_block_info(block_number)
            except Exception as e:
                print(f"处理区块 #{block_number} 时出错: {str(e)}")
            else:
                ok = True
    
    # 输出统计结果
    print("\n===== 交易类型统计 =====")
    print(f"总交易数: {total_txs}")
    for tx_type, count in sorted(type_counter.items()):
        percentage = (count / total_txs) * 100 if total_txs > 0 else 0
        print(f"类型 {tx_type}: {count} 笔交易 ({percentage:.2f}%)")

if __name__ == "__main__":
    main()
