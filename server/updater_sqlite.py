import util
import time
import logging
import os
import json
import sqlite3
import requests
import datetime

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
        code_address TEXT,
        relayer_address TEXT,
        date TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_authorizer ON authorizations(authorizer_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_code ON authorizations(code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_date ON authorizations(date)')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_date_tx_hash ON authorizations(date, tx_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_date_authorizer ON authorizations(date, authorizer_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_date_code ON authorizations(date, code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizations_date_relayer ON authorizations(date, relayer_address)')

    # 创建authorizers表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorizers (
        authorizer_address TEXT PRIMARY KEY,
        tvl_balance REAL,
        tvl_timestamp INTEGER,
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_tvl_timestamp ON authorizers(tvl_timestamp ASC)')
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
        date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        info_cursor.execute("INSERT INTO transactions (tx_hash, block_number, block_hash, tx_index, relayer_address, authorization_fee, timestamp, authorization_list) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (type4_tx['tx_hash'], type4_tx['block_number'], type4_tx['block_hash'], type4_tx['tx_index'], type4_tx['relayer_address'], type4_tx['authorization_fee'], timestamp, json.dumps(type4_tx['authorization_list'])))
        
        for authorization in type4_tx['authorization_list']:
            info_cursor.execute("INSERT INTO authorizations (tx_hash, authorizer_address, code_address, relayer_address, date) VALUES (?, ?, ?, ?, ?)", (type4_tx['tx_hash'], authorization['authorizer_address'], authorization['code_address'], type4_tx['relayer_address'], date))
            
            info_cursor.execute("SELECT authorizer_address FROM authorizers WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            if info_cursor.fetchone() is None:
                info_cursor.execute("INSERT INTO authorizers (authorizer_address, tvl_balance, tvl_timestamp, last_nonce, last_chain_id, code_address, set_code_tx_count, unset_code_tx_count, historical_code_address, provider) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (authorization['authorizer_address'], 0, 0, 0, 0, "", 0, 0, json.dumps([]), ""))
            
            
            row = info_cursor.execute("SELECT code_address, historical_code_address FROM authorizers WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            current_code_address, current_historical_code_address_json = row.fetchone()
            if authorization['code_address'] != current_code_address and current_code_address != "0x0000000000000000000000000000000000000000" and current_code_address != "":
                current_historical_code_address = json.loads(current_historical_code_address_json)
                current_historical_code_address.append(current_code_address)
                info_cursor.execute("UPDATE authorizers SET historical_code_address = ? WHERE authorizer_address = ?", (json.dumps(current_historical_code_address), authorization['authorizer_address']))
            
                
            if authorization['code_address'] == "0x0000000000000000000000000000000000000000":
                info_cursor.execute("UPDATE authorizers SET unset_code_tx_count = unset_code_tx_count + 1 WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            else:
                info_cursor.execute("UPDATE authorizers SET set_code_tx_count = set_code_tx_count + 1 WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            
            info_cursor.execute("UPDATE authorizers SET  last_nonce = ?, last_chain_id = ?, code_address = ? WHERE authorizer_address = ?", (authorization['nonce'], authorization['chain_id'], authorization['code_address'], authorization['authorizer_address']))


        info_cursor.execute("SELECT relayer_address FROM relayers WHERE relayer_address = ?", (type4_tx['relayer_address'] ,))
        if info_cursor.fetchone() is not None:
            info_cursor.execute("UPDATE relayers SET tx_count = tx_count + 1, authorization_count = authorization_count + ?, authorization_fee = authorization_fee + ? WHERE relayer_address = ?", (len(type4_tx['authorization_list']), type4_tx['authorization_fee'], type4_tx['relayer_address'] ,))
        else:
            info_cursor.execute("INSERT INTO relayers (relayer_address, tx_count, authorization_count, authorization_fee) VALUES (?, ?, ?, ?)", (type4_tx['relayer_address'] , 1, len(type4_tx['authorization_list']),  type4_tx['authorization_fee']))
            
        info_conn.commit()

    info_conn.close()
    block_conn.close()
    

def update_info_by_tvl(info_db_path, tvl_db_path):
    info_conn = sqlite3.connect(info_db_path)
    info_read_cursor = info_conn.cursor()
    info_write_cursor = info_conn.cursor()
    
    tvl_conn = sqlite3.connect(tvl_db_path)
    tvl_cursor = tvl_conn.cursor()
    
    start_time = time.time()
    while True:
        try:
            BTC_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=BTCUSDT").json()['price']
            ETH_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=ETHUSDT").json()['price']
            
            if NAME == "bsc":
                BNB_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=BNBUSDT").json()['price']
            break
        except:
            time.sleep(1)
    end_time = time.time()
    print(f"获取价格信息完成，耗时 {end_time - start_time} 秒")
    
    info_read_cursor.execute("SELECT authorizer_address FROM authorizers")
    for row in info_read_cursor:
        authorizer_address = row[0]
        tvl_cursor.execute("SELECT eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp FROM author_balances WHERE author_address = ?", (authorizer_address,))
        result = tvl_cursor.fetchone()
        if result is not None:
            eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp = result
            if NAME != "bsc":
                tvl_balance = float(eth_balance) * float(ETH_PRICE) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) + float(usdc_balance) + float(dai_balance)
            else:
                tvl_balance = float(eth_balance) * float(BNB_PRICE) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) / 10**12 + float(usdc_balance) / 10**12 + float(dai_balance)
            info_write_cursor.execute("UPDATE authorizers SET tvl_balance = ?, tvl_timestamp = ? WHERE authorizer_address = ?", (tvl_balance, timestamp, authorizer_address))
        
    info_conn.commit()
    info_conn.close()
    tvl_conn.close()
        
    
def update_info_by_code(info_db_path, code_db_path):
    info_conn = sqlite3.connect(info_db_path)
    info_read_cursor = info_conn.cursor()
    info_write_cursor = info_conn.cursor()
    
    code_conn = sqlite3.connect(code_db_path)
    code_cursor = code_conn.cursor()
        
    info_read_cursor.execute("SELECT code_address, count(authorizer_address), sum(tvl_balance) FROM authorizers GROUP BY code_address")
    for row in info_read_cursor:
        code_address, authorizer_count, tvl_balance = row
        info_write_cursor.execute("INSERT INTO codes (code_address, authorizer_count, tvl_balance) VALUES (?, ?, ?) ON CONFLICT(code_address) DO UPDATE SET authorizer_count = excluded.authorizer_count, tvl_balance = excluded.tvl_balance", (code_address, authorizer_count, tvl_balance))
        
        code_cursor.execute("SELECT code FROM codes WHERE LOWER(code_address) = ?", (code_address,))
        row = code_cursor.fetchone()
        if row is not None:
            code = row[0]
            functions = util.parse_functions(code)
            tags = []
            for function in functions:
                if function in util.FUNCTION_TO_TAGS:
                    for tag in util.FUNCTION_TO_TAGS[function]:
                        if tag not in tags:
                            tags.append(tag)
            info_write_cursor.execute("UPDATE codes SET tags = ? WHERE code_address = ?", (json.dumps(tags), code_address))
    
    code_info = json.load(open(f'code_info.json'))
    for item in code_info:
        code_address = item['address'].lower()
        info_write_cursor.execute("UPDATE codes SET provider = ?, details = ? WHERE code_address = ?", (item['provider'], json.dumps(item), code_address))
        info_write_cursor.execute("UPDATE authorizers SET provider = ? WHERE code_address = ?", (item['provider'], code_address))
    
    info_conn.commit()
    info_conn.close()


def update_info_daily(info_db_path):
    info_conn = sqlite3.connect(info_db_path)
    info_read_cursor = info_conn.cursor()
    info_write_cursor = info_conn.cursor()
    
    cumulative_tx_count = 0
    cumulative_authorization_count = 0
    
    info_read_cursor.execute("SELECT date, count(distinct tx_hash), count(distinct authorizer_address), count(distinct code_address), count(distinct relayer_address) FROM authorizations GROUP BY date")
    for row in info_read_cursor:
        date, tx_count, authorization_count, code_count, relayer_count = row
        cumulative_tx_count += tx_count
        cumulative_authorization_count += authorization_count
        
        info_write_cursor.execute("INSERT INTO daily_stats (date, tx_count, authorization_count, code_count, relayer_count, cumulative_transaction_count, cumulative_authorization_count) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(date) DO UPDATE SET tx_count = excluded.tx_count, authorization_count = excluded.authorization_count, code_count = excluded.code_count, relayer_count = excluded.relayer_count, cumulative_transaction_count = excluded.cumulative_transaction_count, cumulative_authorization_count = excluded.cumulative_authorization_count", (date, tx_count, authorization_count, code_count, relayer_count, cumulative_tx_count, cumulative_authorization_count))
    
    info_conn.commit()
    info_conn.close()

block_db_path = f'../backend/{NAME}_block.db'
tvl_db_path = f'../backend/{NAME}_tvl.db'
code_db_path = f'../backend/{NAME}_code.db'

info_db_path = f'./db/{NAME}.db'
print(f"开始处理 {NAME} 网络...")

create_db_if_not_exists(info_db_path)
start_time = time.time()
update_info_by_block(info_db_path, block_db_path)
end_time = time.time()
print(f"更新区块信息完成，耗时 {end_time - start_time} 秒")

start_time = time.time()
update_info_by_tvl(info_db_path, tvl_db_path)
end_time = time.time()
print(f"更新TVL信息完成，耗时 {end_time - start_time} 秒")

start_time = time.time()
update_info_by_code(info_db_path, code_db_path)
end_time = time.time()
print(f"更新代码信息完成，耗时 {end_time - start_time} 秒")

start_time = time.time()
update_info_daily(info_db_path)
end_time = time.time()
print(f"更新每日信息完成，耗时 {end_time - start_time} 秒")
