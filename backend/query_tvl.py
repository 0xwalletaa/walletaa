#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import glob
from decimal import Decimal

def get_non_zero_counts(db_path):
    """获取指定数据库中各个代币的非零余额记录数"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有代币余额列
        cursor.execute("PRAGMA table_info(author_balances)")
        columns = [col[1] for col in cursor.fetchall() if col[1].endswith('_balance')]
        
        # 统计每个代币的非零记录数
        counts = {}
        for col in columns:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM author_balances 
                WHERE {col} != '0' AND {col} != '0.0' AND {col} IS NOT NULL
            """)
            count = cursor.fetchone()[0]
            token_name = col.replace('_balance', '').upper()
            counts[token_name] = count
        
        conn.close()
        return counts
    except Exception as e:
        print(f"处理数据库 {db_path} 时出错: {e}")
        return {}

def main():
    # 获取当前目录下所有的 *_tvl.db 文件
    db_files = glob.glob('*_tvl.db')
    
    if not db_files:
        print("未找到任何 *_tvl.db 文件")
        return
    
    print("\nTVL 数据库统计信息:")
    print("-" * 50)
    
    # 处理每个数据库文件
    for db_file in db_files:
        network_name = db_file.replace('_tvl.db', '')
        print(f"\n网络: {network_name}")
        print("-" * 30)
        
        counts = get_non_zero_counts(db_file)
        if counts:
            for token, count in counts.items():
                print(f"{token}: {count} 个地址")
        else:
            print("无法获取统计数据")
    
    print("\n统计完成")

if __name__ == "__main__":
    main() 