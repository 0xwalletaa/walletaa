#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def query_database():
    # 连接到数据库
    conn = sqlite3.connect('sepolia_blocks.db')
    cursor = conn.cursor()
    
    # 查询区块总数
    cursor.execute("SELECT COUNT(*) FROM blocks")
    total_blocks = cursor.fetchone()[0]
    print(f"数据库中总区块数: {total_blocks}")
    
    # 查询交易总数
    cursor.execute("SELECT SUM(tx_count) FROM blocks")
    total_txs = cursor.fetchone()[0] or 0
    print(f"数据库中总交易数: {total_txs}")
    
    # 查询type=4交易总数
    cursor.execute("SELECT SUM(type4_tx_count) FROM blocks")
    total_type4_txs = cursor.fetchone()[0] or 0
    print(f"数据库中type=4交易总数: {total_type4_txs}")
    
    # 查询所有区块信息
    print("\n===== 区块信息 =====")
    cursor.execute("SELECT block_number, tx_count, type4_tx_count FROM blocks ORDER BY block_number")
    blocks = cursor.fetchall()
    
    for i, (block_number, tx_count, type4_tx_count) in enumerate(blocks):
        print(f"区块 #{block_number}: 共 {tx_count} 笔交易，其中 {type4_tx_count} 笔type=4交易")
        
        # 只显示前10个区块详细信息，避免输出过多
        if i >= 9 and len(blocks) > 20:
            remaining = len(blocks) - i - 1
            print(f"... 还有 {remaining} 个区块 ...")
            break
    
    # 查询type=4交易的哈希
    print("\n===== Type=4交易哈希 =====")
    cursor.execute("SELECT tx_hash, block_number, tx_data FROM type4_transactions ORDER BY block_number")
    type4_tx = cursor.fetchone()
    print(type4_tx)
    
    """
    Type4交易示例
    ('ddf4aef622b21511447ee55f417ef76acaeaf8e4d8b4f587bbfa2bf9e24eee97', 8033831, '{"blockHash": "953c5893e1e7c4c9a350fe9778f6dd69965b93207d4b686017f1a1b94ce4c621", "blockNumber": 8033831, "from": "0x54c5E297819D1BF7bbF6a9d3B129b5BBfcA99171", "gas": 4918696, "gasPrice": 708846590, "maxPriorityFeePerGas": 100000000, "maxFeePerGas": 873235169, "hash": "ddf4aef622b21511447ee55f417ef76acaeaf8e4d8b4f587bbfa2bf9e24eee97", "input": "0x0000", "nonce": 68, "to": "0x0000000071727De22E5E9d8BAf0edAc6f37da032", "transactionIndex": 94, "value": 0, "type": 4, "accessList": [], "chainId": 11155111, "authorizationList": [{"chainId": "0xaa36a7", "address": "0x69007702764179f14f51cdce752f4f775d74e139", "nonce": "0x0", "yParity": "0x1", "r": "0xc6763bea75391f2e3ded5de88fc9f37dfb36b4166af73f3732ea31331ca292e0", "s": "0x58bc8fc791548d0f90eefaaa72623b54d1e5b7f0bbf94d23d95dad230e228cad"}], "v": 0, "yParity": 0, "r": "2e87f05f6b1d3352c1cff1b90a1528f002c5c9f99072fa49a7ed2d37153f19df", "s": "5a3f5f3045a41ed862e8814a7eb712c0a9c291bbb63b7527d705683bd0c0c4f1"}')
    """
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    query_database() 