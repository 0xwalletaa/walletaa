import util
import time
import logging
import os
import json
import sqlite3

def create_info_database(db_path):
    """创建信息数据库和表结构"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建transactions表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        tx_hash TEXT PRIMARY KEY,
        block_number INTEGER,
        block_hash TEXT,
        tx_index INTEGER,
        relayer_address TEXT,
        authorization_fee REAL,
        timestamp INTEGER,
        authorization_list TEXT
    )
    ''')
    
    # 创建authorizations表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_hash TEXT,
        authorizer_address TEXT,
        code_address TEXT,
        chain_id INTEGER,
        nonce INTEGER,
        FOREIGN KEY (tx_hash) REFERENCES transactions(tx_hash)
    )
    ''')
    
    # 创建authorizers表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorizers (
        authorizer_address TEXT PRIMARY KEY,
        tvl_balance REAL,
        last_nonce INTEGER,
        last_chain_id INTEGER,
        code_address TEXT,
        set_code_tx_count INTEGER,
        unset_code_tx_count INTEGER,
        historical_code_address TEXT,
        provider TEXT
    )
    ''')
    
    # 创建authorizers_with_zero表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorizers_with_zero (
        authorizer_address TEXT PRIMARY KEY,
        tvl_balance REAL,
        last_nonce INTEGER,
        last_chain_id INTEGER,
        code_address TEXT,
        set_code_tx_count INTEGER,
        unset_code_tx_count INTEGER,
        historical_code_address TEXT,
        provider TEXT
    )
    ''')
    
    # 创建codes表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS codes (
        code_address TEXT PRIMARY KEY,
        authorizer_count INTEGER,
        tvl_balance REAL,
        tags TEXT,
        provider TEXT,
        details TEXT
    )
    ''')
    
    # 创建relayers表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relayers (
        relayer_address TEXT PRIMARY KEY,
        tx_count INTEGER,
        authorization_count INTEGER,
        authorization_fee REAL
    )
    ''')
    
    # 创建overview表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS overview (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # 创建last_update_time表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS last_update_time (
        id INTEGER PRIMARY KEY,
        timestamp REAL
    )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_relayer ON transactions(relayer_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_authorizer ON authorizations(authorizer_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_code ON authorizations(code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_tx_hash ON authorizations(tx_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_tvl_balance ON authorizers(tvl_balance DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_provider ON authorizers(provider)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_code_address ON authorizers(code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_with_zero_tvl_balance ON authorizers_with_zero(tvl_balance DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_with_zero_provider ON authorizers_with_zero(provider)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_with_zero_code_address ON authorizers_with_zero(code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_codes_tvl_balance ON codes(tvl_balance DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_codes_authorizer_count ON codes(authorizer_count DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_codes_provider ON codes(provider)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relayers_tx_count ON relayers(tx_count DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relayers_authorization_count ON relayers(authorization_count DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relayers_authorization_fee ON relayers(authorization_fee DESC)')
    
    conn.commit()
    conn.close()

def store_data_to_database(db_path, txs, authorizers, authorizers_with_zero, codes_by_tvl_balance, 
                          codes_by_authorizer_count, relayers_by_tx_count, relayers_by_authorization_count,
                          relayers_by_authorization_fee, overview, last_update_time):
    """将数据存储到SQLite数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 清空所有表
    cursor.execute('DELETE FROM transactions')
    cursor.execute('DELETE FROM authorizations')
    cursor.execute('DELETE FROM authorizers')
    cursor.execute('DELETE FROM authorizers_with_zero')
    cursor.execute('DELETE FROM codes')
    cursor.execute('DELETE FROM relayers')
    cursor.execute('DELETE FROM overview')
    cursor.execute('DELETE FROM last_update_time')
    
    # 插入transactions数据
    for tx in txs:
        cursor.execute('''
        INSERT INTO transactions 
        (tx_hash, block_number, block_hash, tx_index, relayer_address, authorization_fee, timestamp, authorization_list)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tx['tx_hash'],
            tx['block_number'],
            tx['block_hash'],
            tx['tx_index'],
            tx['relayer_address'],
            tx['authorization_fee'],
            tx['timestamp'],
            json.dumps(tx['authorization_list'])
        ))
        
        # 插入authorizations数据
        for auth in tx['authorization_list']:
            cursor.execute('''
            INSERT INTO authorizations 
            (tx_hash, authorizer_address, code_address, chain_id, nonce)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                tx['tx_hash'],
                auth['authorizer_address'],
                auth['code_address'],
                auth['chain_id'],
                auth['nonce']
            ))
    
    # 插入authorizers数据
    for auth in authorizers:
        cursor.execute('''
        INSERT INTO authorizers 
        (authorizer_address, tvl_balance, last_nonce, last_chain_id, code_address, 
         set_code_tx_count, unset_code_tx_count, historical_code_address, provider)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            auth['authorizer_address'],
            auth['tvl_balance'],
            auth['last_nonce'],
            auth['last_chain_id'],
            auth['code_address'],
            auth['set_code_tx_count'],
            auth['unset_code_tx_count'],
            json.dumps(auth['historical_code_address']),
            auth.get('provider', '')
        ))
    
    # 插入authorizers_with_zero数据
    for auth in authorizers_with_zero:
        cursor.execute('''
        INSERT INTO authorizers_with_zero 
        (authorizer_address, tvl_balance, last_nonce, last_chain_id, code_address, 
         set_code_tx_count, unset_code_tx_count, historical_code_address, provider)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            auth['authorizer_address'],
            auth['tvl_balance'],
            auth['last_nonce'],
            auth['last_chain_id'],
            auth['code_address'],
            auth['set_code_tx_count'],
            auth['unset_code_tx_count'],
            json.dumps(auth['historical_code_address']),
            auth.get('provider', '')
        ))
    
    # 插入codes数据（按TVL余额排序）
    for code in codes_by_tvl_balance:
        cursor.execute('''
        INSERT OR REPLACE INTO codes 
        (code_address, authorizer_count, tvl_balance, tags, provider, details)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            code['code_address'],
            code['authorizer_count'],
            code['tvl_balance'],
            json.dumps(code['tags']),
            code['provider'],
            json.dumps(code['details']) if code['details'] else None
        ))
    
    # 插入relayers数据
    for relayer in relayers_by_tx_count:
        cursor.execute('''
        INSERT OR REPLACE INTO relayers 
        (relayer_address, tx_count, authorization_count, authorization_fee)
        VALUES (?, ?, ?, ?)
        ''', (
            relayer['relayer_address'],
            relayer['tx_count'],
            relayer['authorization_count'],
            relayer['authorization_fee']
        ))
    
    # 插入overview数据
    for key, value in overview.items():
        cursor.execute('''
        INSERT INTO overview (key, value) VALUES (?, ?)
        ''', (key, json.dumps(value)))
    
    # 插入last_update_time
    cursor.execute('''
    INSERT INTO last_update_time (timestamp) VALUES (?)
    ''', (last_update_time,))
    
    conn.commit()
    conn.close()

def main():
    for NAME in ["mainnet", "sepolia", "bsc", "op", "base"]:
        util.NAME = NAME
        
        print(f"开始处理 {NAME} 网络...")
        start_time = time.time()
        
        # 获取数据
        code_infos = util.get_code_infos()
        txs = util.get_all_type4_txs_with_timestamp()
        authorizers = util.get_authorizer_info(txs, code_infos)
        authorizers_with_zero = util.get_authorizer_info(txs, code_infos, include_zero=True)
        code_function_info = util.get_code_function_info()
        codes_by_tvl_balance = util.get_code_info(authorizers, code_infos, code_function_info, sort_by="tvl_balance")
        codes_by_authorizer_count = util.get_code_info(authorizers, code_infos, code_function_info, sort_by="authorizer_count")
        relayers_by_tx_count = util.get_relayer_info(txs, sort_by="tx_count")
        relayers_by_authorization_count = util.get_relayer_info(txs, sort_by="authorization_count")
        relayers_by_authorization_fee = util.get_relayer_info(txs, sort_by="authorization_fee")
        overview = util.get_overview(txs, authorizers, codes_by_authorizer_count, relayers_by_tx_count, code_infos)
        last_update_time = time.time()
        
        end_time = time.time()
        print(f"{NAME} txs: {len(txs)}, 计算时间: {end_time - start_time:.2f} 秒")
        
        # 存储到数据库
        start_time = time.time()
        db_path = f'/dev/shm/{NAME}_info.db'
        temp_db_path = f'/dev/shm/{NAME}_info_temp.db'
        
        # 创建临时数据库
        create_info_database(temp_db_path)
        
        # 存储数据到临时数据库
        store_data_to_database(
            temp_db_path, txs, authorizers, authorizers_with_zero, 
            codes_by_tvl_balance, codes_by_authorizer_count,
            relayers_by_tx_count, relayers_by_authorization_count,
            relayers_by_authorization_fee, overview, last_update_time
        )
        
        # 原子性替换
        os.rename(temp_db_path, db_path)
        
        end_time = time.time()
        print(f"{NAME} txs: {len(txs)}, 存储时间: {end_time - start_time:.2f} 秒")
        print("--------------------------------")
    
    # 测试加载时间
    for NAME in ["mainnet", "sepolia", "bsc", "op", "base"]:
        start_time = time.time()
        db_path = f'/dev/shm/{NAME}_info.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM transactions')
        tx_count = cursor.fetchone()[0]
        conn.close()
        end_time = time.time()
        print(f"{NAME} 数据库连接和查询时间: {end_time - start_time:.2f} 秒, 交易数: {tx_count}")
        print("--------------------------------")

if __name__ == '__main__':
    main() 