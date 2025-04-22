#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from collections import Counter

def analyze_type4_transactions():
    # 连接到数据库
    conn = sqlite3.connect('sepolia_blocks.db')
    cursor = conn.cursor()
    
    # 1. 统计type4交易数量
    cursor.execute("SELECT COUNT(*) FROM type4_transactions")
    total_type4_txs = cursor.fetchone()[0]
    print(f"数据库中type=4交易总数: {total_type4_txs}")
    
    # 获取所有type4交易数据
    cursor.execute("SELECT tx_data FROM type4_transactions")
    tx_data_list = cursor.fetchall()
    
    # 存储address为0和非0的计数
    zero_address_count = 0
    non_zero_address_count = 0
    
    # 存储非0地址的频次
    address_counter = Counter()
    
    # 遍历所有交易数据
    for (tx_data_str,) in tx_data_list:
        try:
            tx_data = json.loads(tx_data_str)
            
            # 检查是否有authorizationList字段
            if 'authorizationList' in tx_data and tx_data['authorizationList']:
                for auth in tx_data['authorizationList']:
                    if 'address' in auth:
                        address = auth['address'].lower()
                        if address == '0x0000000000000000000000000000000000000000' or address == '0x0':
                            zero_address_count += 1
                        else:
                            non_zero_address_count += 1
                            address_counter[address] += 1
        except (json.JSONDecodeError, KeyError) as e:
            print(f"处理交易数据时出错: {e}")
            continue
    
    # 2. 输出address为0和非0的情况
    print(f"\n===== 授权地址统计 =====")
    print(f"address为0的授权数量: {zero_address_count}")
    print(f"address非0的授权数量: {non_zero_address_count}")
    
    # 3. 若address非0，则统计address的频次，从高到低排列
    if address_counter:
        print(f"\n===== 非0地址频次统计(从高到低) =====")
        for address, count in address_counter.most_common():
            print(f"地址: {address}, 出现次数: {count}")
    else:
        print("\n没有找到非0地址的授权。")
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    analyze_type4_transactions() 