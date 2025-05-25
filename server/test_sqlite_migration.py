#!/usr/bin/env python3
"""
测试SQLite数据库迁移的脚本
"""

import os
import sys
import sqlite3
import json
import time

# 添加当前目录到Python路径
sys.path.append('.')

def test_database_structure(db_path):
    """测试数据库结构是否正确"""
    print(f"测试数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    expected_tables = [
        'transactions', 'authorizations', 'authorizers', 'authorizers_with_zero',
        'codes', 'relayers', 'overview', 'last_update_time'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    actual_tables = [row[0] for row in cursor.fetchall()]
    
    for table in expected_tables:
        if table in actual_tables:
            print(f"✅ 表 {table} 存在")
        else:
            print(f"❌ 表 {table} 不存在")
            conn.close()
            return False
    
    # 检查索引是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"✅ 找到 {len(indexes)} 个索引")
    
    # 检查数据量
    for table in expected_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"📊 表 {table}: {count} 条记录")
    
    conn.close()
    return True

def test_search_functionality():
    """测试搜索功能"""
    print("\n🔍 测试搜索功能...")
    
    # 导入新的server模块进行测试
    try:
        import server_sqlite
        
        # 测试数据库连接
        conn = server_sqlite.get_db_connection()
        cursor = conn.cursor()
        
        # 测试交易搜索
        print("测试交易搜索...")
        query, params = server_sqlite.build_transaction_search_query('0x1234567890123456789012345678901234567890')
        print(f"  42位地址查询: {query[:50]}...")
        
        query, params = server_sqlite.build_transaction_search_query('0x1234567890123456789012345678901234567890123456789012345678901234')
        print(f"  66位哈希查询: {query[:50]}...")
        
        # 测试授权者搜索
        print("测试授权者搜索...")
        query, params = server_sqlite.build_authorizer_search_query('0x1234567890123456789012345678901234567890')
        print(f"  地址查询: {query[:50]}...")
        
        query, params = server_sqlite.build_authorizer_search_query('test')
        print(f"  提供者名称查询: {query[:50]}...")
        
        conn.close()
        print("✅ 搜索功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 搜索功能测试失败: {e}")
        return False

def benchmark_performance(db_path):
    """性能基准测试"""
    print(f"\n⚡ 性能测试: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 测试基本查询性能
    start_time = time.time()
    cursor.execute('SELECT COUNT(*) FROM transactions')
    tx_count = cursor.fetchone()[0]
    end_time = time.time()
    print(f"COUNT查询耗时: {(end_time - start_time)*1000:.2f}ms")
    
    # 测试分页查询性能
    start_time = time.time()
    cursor.execute('SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 10 OFFSET 0')
    rows = cursor.fetchall()
    end_time = time.time()
    print(f"分页查询耗时: {(end_time - start_time)*1000:.2f}ms")
    
    # 测试复杂查询性能
    start_time = time.time()
    cursor.execute('''
    SELECT t.* FROM transactions t 
    WHERE EXISTS (
        SELECT 1 FROM authorizations a 
        WHERE a.tx_hash = t.tx_hash 
        AND a.authorizer_address = ?
    ) LIMIT 10
    ''', ('0x1234567890123456789012345678901234567890',))
    rows = cursor.fetchall()
    end_time = time.time()
    print(f"复杂查询耗时: {(end_time - start_time)*1000:.2f}ms")
    
    conn.close()

def main():
    """主测试函数"""
    print("🚀 开始SQLite数据库迁移测试")
    
    # 测试各个网络的数据库
    networks = ["mainnet", "sepolia", "bsc", "op", "base"]
    
    for network in networks:
        db_path = f'/dev/shm/{network}_info.db'
        print(f"\n📊 测试网络: {network}")
        
        if test_database_structure(db_path):
            benchmark_performance(db_path)
        else:
            print(f"❌ {network} 数据库结构测试失败")
    
    # 测试搜索功能
    if test_search_functionality():
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 测试失败")

if __name__ == '__main__':
    main() 