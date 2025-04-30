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
    
    # 创建一个集合存储交易的from地址
    from_addresses = set()
    
    """
    Type4交易示例
    ('ddf4aef622b21511447ee55f417ef76acaeaf8e4d8b4f587bbfa2bf9e24eee97', 8033831, '{"blockHash": "953c5893e1e7c4c9a350fe9778f6dd69965b93207d4b686017f1a1b94ce4c621", "blockNumber": 8033831, "from": "0x54c5E297819D1BF7bbF6a9d3B129b5BBfcA99171", "gas": 4918696, "gasPrice": 708846590, "maxPriorityFeePerGas": 100000000, "maxFeePerGas": 873235169, "hash": "ddf4aef622b21511447ee55f417ef76acaeaf8e4d8b4f587bbfa2bf9e24eee97", "input": "0x0000", "nonce": 68, "to": "0x0000000071727De22E5E9d8BAf0edAc6f37da032", "transactionIndex": 94, "value": 0, "type": 4, "accessList": [], "chainId": 11155111, "authorizationList": [{"chainId": "0xaa36a7", "address": "0x69007702764179f14f51cdce752f4f775d74e139", "nonce": "0x0", "yParity": "0x1", "r": "0xc6763bea75391f2e3ded5de88fc9f37dfb36b4166af73f3732ea31331ca292e0", "s": "0x58bc8fc791548d0f90eefaaa72623b54d1e5b7f0bbf94d23d95dad230e228cad"}], "v": 0, "yParity": 0, "r": "2e87f05f6b1d3352c1cff1b90a1528f002c5c9f99072fa49a7ed2d37153f19df", "s": "5a3f5f3045a41ed862e8814a7eb712c0a9c291bbb63b7527d705683bd0c0c4f1"}')
    """
    
    
    # 遍历所有交易数据
    for (tx_data_str,) in tx_data_list:
        try:
            tx_data = json.loads(tx_data_str)
            
            # 记录交易的from地址
            if 'from' in tx_data:
                from_address = tx_data['from'].lower()
                from_addresses.add(from_address)
            
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
    
    # 4. 输出唯一from地址的数量
    print(f"\n===== 发送方(from)地址统计 =====")
    print(f"唯一发送方地址数量: {len(from_addresses)}")
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    analyze_type4_transactions() 