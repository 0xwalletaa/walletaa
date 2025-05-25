import util
import time
import logging
import os
import json
import sqlite3

NAME = os.environ.get("NAME")

def create_db_if_not_exists(db_path):
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_block_number ON transactions(block_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_relayer ON transactions(relayer_address)')
    
    
    # 创建authorizations表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorizations (
        tx_hash TEXT,
        authorizer_address TEXT,
        code_address TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_authorizer ON authorizations(authorizer_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_code ON authorizations(code_address)')

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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_tvl_balance ON authorizers(tvl_balance DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_code_address ON authorizers(code_address)')
    
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_codes_tvl_balance ON codes(tvl_balance DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_codes_authorizer_count ON codes(authorizer_count DESC)')
    
    # 创建relayers表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relayers (
        relayer_address TEXT PRIMARY KEY,
        tx_count INTEGER,
        authorization_count INTEGER,
        authorization_fee REAL
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relayers_tx_count ON relayers(tx_count DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relayers_authorization_count ON relayers(authorization_count DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relayers_authorization_fee ON relayers(authorization_fee DESC)')
    

    # 创建daily表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_stats (
        date TEXT PRIMARY KEY,
        tx_count INTEGER,
        authorization_count INTEGER,
        code_count INTEGER,
        relayer_count INTEGER,
        cumulative_transaction_count INTEGER,
        cumulative_authorization_count INTEGER
    )
    ''')

    conn.commit()
    conn.close()


def update_info_by_block(info_db_path, block_db_path):
    info_conn = sqlite3.connect(info_db_path)
    info_cursor = info_conn.cursor()
    
    block_conn = sqlite3.connect(block_db_path)
    block_tx_cursor = block_conn.cursor()
    block_timestamp_cursor = block_conn.cursor()
    block_tx_cursor.execute("SELECT tx_hash, tx_data FROM type4_transactions ORDER BY block_number ASC")
    
    # 逐行处理，避免一次性加载所有数据
    for row in block_tx_cursor:  # 直接迭代cursor
        tx_hash, tx_data_str = row
        
        tx_hash = "0x"+tx_hash
        info_cursor.execute("SELECT tx_hash FROM transactions WHERE tx_hash = ?", (tx_hash,))
        if info_cursor.fetchone() is not None:
            continue
                     
        type4_tx = util.parse_type4_tx_data(tx_data_str)
        
        block_timestamp_cursor.execute("SELECT timestamp FROM blocks WHERE block_number = ?", (type4_tx['block_number'],))
        timestamp = block_timestamp_cursor.fetchone()[0]
        
        info_cursor.execute("INSERT INTO transactions (tx_hash, block_number, block_hash, tx_index, relayer_address, authorization_fee, timestamp, authorization_list) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (type4_tx['tx_hash'], type4_tx['block_number'], type4_tx['block_hash'], type4_tx['tx_index'], type4_tx['relayer_address'], type4_tx['authorization_fee'], timestamp, json.dumps(type4_tx['authorization_list'])))
        
        for authorization in type4_tx['authorization_list']:
            info_cursor.execute("INSERT INTO authorizations (tx_hash, authorizer_address, code_address) VALUES (?, ?, ?)", (type4_tx['tx_hash'], authorization['authorizer_address'], authorization['code_address']))
            
         
            info_cursor.execute("SELECT authorizer_address FROM authorizers WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            if info_cursor.fetchone() is not None:
                continue
            else:
                info_cursor.execute("INSERT INTO authorizers (authorizer_address, tvl_balance, last_nonce, last_chain_id, code_address, set_code_tx_count, unset_code_tx_count, historical_code_address, provider) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (authorization['authorizer_address'], 0, 0, 0, authorization['code_address'], 0, 0, "", ""))
                
            if authorization['code_address'] == "0x0000000000000000000000000000000000000000":
                info_cursor.execute("UPDATE authorizers SET unset_code_tx_count = unset_code_tx_count + 1 WHERE authorizer_address = ?", (authorization['authorizer_address'],))
                row = info_cursor.execute("SELECT code_address, historical_code_address FROM authorizers WHERE authorizer_address = ?", (authorization['authorizer_address'],))
                current_code_address, current_historical_code_address_json = row.fetchone()
                if current_code_address != "0x0000000000000000000000000000000000000000":
                    current_historical_code_address = json.loads(current_historical_code_address_json)
                    current_historical_code_address.append(current_code_address)
                    info_cursor.execute("UPDATE authorizers SET historical_code_address = ? WHERE authorizer_address = ?", (json.dumps(current_historical_code_address), authorization['authorizer_address']))
            else:
                info_cursor.execute("UPDATE authorizers SET set_code_tx_count = set_code_tx_count + 1 WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            
            info_cursor.execute("UPDATE authorizers SET  last_nonce = ?, last_chain_id = ?, code_address = ? WHERE authorizer_address = ?", (authorization['nonce'], authorization['chain_id'], authorization['code_address'], authorization['authorizer_address']))


        relayer_address = type4_tx['relayer_address']        
        authorization_fee = util.PER_EMPTY_ACCOUNT_COST * len(type4_tx['authorization_list']) * type4_tx['gasPrice'] / 10**18
        info_cursor.execute("SELECT relayer_address FROM relayers WHERE relayer_address = ?", (relayer_address,))
        if info_cursor.fetchone() is not None:
            info_cursor.execute("UPDATE relayers SET tx_count = tx_count + 1, authorization_count = authorization_count + 1, authorization_fee = authorization_fee + ? WHERE relayer_address = ?", (authorization_fee, relayer_address,))
        else:
            info_cursor.execute("INSERT INTO relayers (relayer_address, tx_count, authorization_count, authorization_fee) VALUES (?, ?, ?, ?)", (relayer_address, 1, 1, authorization_fee))
            
        info_conn.commit()

    info_conn.close()
    block_conn.close()
    
    

block_db_path = f'../backend/{NAME}_block.db'
tvl_db_path = f'../backend/{NAME}_tvl.db'

info_db_path = f'./db/{NAME}.db'
print(f"开始处理 {NAME} 网络...")
start_time = time.time()

create_db_if_not_exists(info_db_path)
update_info_by_block(info_db_path, block_db_path)
