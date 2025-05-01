#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import csv
import os

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('author_tvl.db')
    return conn

def export_to_csv(data, filename='author_tvl_data.csv'):
    """将数据导出到CSV文件"""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['地址', '余额(ETH)'])
        writer.writerows(data)
    print(f"数据已导出到 {filename}")

def export_to_console(data):
    """将数据输出到控制台"""
    print("\n地址                                        余额(ETH)")
    print("-" * 70)
    for address, balance in data:
        print(f"{address}  {balance}")

def main():
    try:
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询所有地址和余额，按余额降序排列
        cursor.execute("SELECT author_address, eth_balance FROM author_balances ORDER BY CAST(eth_balance AS REAL) DESC")
        data = cursor.fetchall()
        
        if not data:
            print("数据库中没有找到任何记录")
            return
            
        # 输出到控制台
        export_to_console(data)
        
        # 询问是否导出到CSV
        choice = input("\n是否要导出到CSV文件？(y/n): ").strip().lower()
        if choice == 'y':
            export_to_csv(data)
            
        # 关闭数据库连接
        conn.close()
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main() 