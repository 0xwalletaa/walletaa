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
    cursor.execute("SELECT tx_hash, block_number FROM type4_transactions ORDER BY block_number")
    type4_txs = cursor.fetchall()
    
    for i, (tx_hash, block_number) in enumerate(type4_txs):
        print(f"区块 #{block_number} - 交易哈希: {tx_hash}")
        
        # 只显示前20个交易哈希，避免输出过多
        if i >= 19 and len(type4_txs) > 30:
            remaining = len(type4_txs) - i - 1
            print(f"... 还有 {remaining} 笔type=4交易 ...")
            break
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    query_database() 