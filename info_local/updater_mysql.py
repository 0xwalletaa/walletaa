import util
import time
import logging
import os
import json
import sqlite3
import pymysql
import requests
import datetime

NAME = os.environ.get("NAME")
DB_PATH = os.environ.get("DB_PATH")
DATA_EXPIRY = 86400

def get_mysql_connection(mysql_db_name, with_database=True):
    """Helper function to create MySQL connection"""
    if with_database:
        return pymysql.connect(
            host='localhost',
            user=mysql_db_name,
            password=mysql_db_name,
            database=mysql_db_name,
            charset='utf8mb4'
        )
    else:
        return pymysql.connect(
            host='localhost',
            user=mysql_db_name,
            password=mysql_db_name,
            charset='utf8mb4'
        )

def create_used_col_and_index(mysql_db_name, block_db_path):
    """Create 'used' column in type4_transactions table if it doesn't exist"""
    # 连接到block db (SQLite)
    block_conn = sqlite3.connect(block_db_path)
    block_cursor = block_conn.cursor()
    
    # 检查type4_transactions表是否有used列
    block_cursor.execute("PRAGMA table_info(type4_transactions)")
    columns = [column[1] for column in block_cursor.fetchall()]
    
    has_used_column = 'used' in columns
    
    if not has_used_column:
        # 添加used列，默认值为0 (False)
        block_cursor.execute("ALTER TABLE type4_transactions ADD COLUMN used INTEGER DEFAULT 0")
        block_conn.commit()
        print("已添加 'used' 列到 type4_transactions 表")
    else:
        print("type4_transactions 表已有 'used' 列")
    
    # 创建used列的索引
    try:
        block_cursor.execute("CREATE INDEX IF NOT EXISTS idx_type4_transactions_used ON type4_transactions(used)")
        block_conn.commit()
        print("已创建 'used' 列的索引")
    except Exception as e:
        print(f"创建索引时出错: {e}")
        
    # 创建tx_hash的索引
    try:
        block_cursor.execute("CREATE INDEX IF NOT EXISTS idx_type4_transactions_tx_hash ON type4_transactions(tx_hash)")
        block_conn.commit()
        print("已创建 'tx_hash' 列的索引")
    except Exception as e:
        print(f"创建索引时出错: {e}")
    
    # 判断MySQL数据库是否有transactions表
    try:
        mysql_conn = get_mysql_connection(mysql_db_name, with_database=True)
        mysql_cursor = mysql_conn.cursor()
        
        # 检查transactions表是否存在
        mysql_cursor.execute("SHOW TABLES LIKE 'transactions'")
        transactions_table_exists = mysql_cursor.fetchone() is not None
        
        if not transactions_table_exists:
            # 如果MySQL中没有transactions表，将block db中的所有used列置为False (0)
            block_cursor.execute("UPDATE type4_transactions SET used = 0")
            block_conn.commit()
            print("MySQL中没有transactions表，已将所有 'used' 列置为False")
        else:
            print("MySQL中已有transactions表")
        
        mysql_conn.close()
    except Exception as e:
        print(f"检查MySQL数据库时出错: {e}")
    
    block_conn.close()


def create_db_if_not_exists(mysql_db_name):
    """Create information database and table structure"""
    # First connect without database to create it if needed
    conn = get_mysql_connection(mysql_db_name, with_database=False)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.close()
    
    # Now connect to the specific database
    conn = get_mysql_connection(mysql_db_name)
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        tx_hash VARCHAR(66) PRIMARY KEY,
        block_number BIGINT,
        block_hash VARCHAR(66),
        tx_index INT,
        relayer_address VARCHAR(42),
        authorization_fee DOUBLE,
        timestamp BIGINT,
        authorization_list MEDIUMTEXT,
        INDEX idx_transactions_block_number(block_number),
        INDEX idx_transactions_timestamp(timestamp DESC),
        INDEX idx_transactions_relayer(relayer_address)
    )
    ''')
    
    
    # Create authorizations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorizations (
        tx_hash VARCHAR(66),
        authorizer_address VARCHAR(42),
        code_address VARCHAR(42),
        relayer_address VARCHAR(42),
        date VARCHAR(10),
        INDEX idx_authorizations_authorizer(authorizer_address),
        INDEX idx_authorizations_code(code_address),
        INDEX idx_authorizations_date(date),
        INDEX idx_authorizations_date_tx_hash(date, tx_hash),
        INDEX idx_authorizations_date_authorizer(date, authorizer_address),
        INDEX idx_authorizations_date_code(date, code_address),
        INDEX idx_authorizations_date_relayer(date, relayer_address)
    )
    ''')

    # Create authorizers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorizers (
        authorizer_address VARCHAR(42) PRIMARY KEY,
        tvl_balance DOUBLE,
        tvl_timestamp BIGINT,
        last_nonce BIGINT,
        last_chain_id BIGINT,
        code_address VARCHAR(42),
        set_code_tx_count INT,
        unset_code_tx_count INT,
        historical_code_address_count INT,
        INDEX idx_authorizers_tvl_balance(tvl_balance DESC),
        INDEX idx_authorizers_tvl_timestamp(tvl_timestamp ASC),
        INDEX idx_authorizers_code_address(code_address),
        INDEX idx_authorizers_historical_code_address_count(historical_code_address_count DESC)
    )
    ''')
    
    # Create codes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS codes (
        code_address VARCHAR(42) PRIMARY KEY,
        authorizer_count INT,
        tvl_balance DOUBLE,
        tags TEXT,
        provider VARCHAR(255),
        details TEXT,
        INDEX idx_codes_tvl_balance(tvl_balance DESC),
        INDEX idx_codes_authorizer_count(authorizer_count DESC)
    )
    ''')
    
    # Create relayers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relayers (
        relayer_address VARCHAR(42) PRIMARY KEY,
        tx_count INT,
        authorization_count INT,
        authorization_fee DOUBLE,
        INDEX idx_relayers_tx_count(tx_count DESC),
        INDEX idx_relayers_authorization_count(authorization_count DESC),
        INDEX idx_relayers_authorization_fee(authorization_fee DESC)
    )
    ''')
    
    # Crate calls table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS calls (
        tx_hash VARCHAR(66),
        block_number BIGINT,
        tx_index INT,
        call_type_trace_address VARCHAR(255),
        from_address VARCHAR(42),
        original_code_address VARCHAR(42),
        parsed_code_address VARCHAR(42),
        value VARCHAR(78),
        calling_function VARCHAR(10),
        timestamp BIGINT,
        INDEX idx_calls_block_number(block_number),
        INDEX idx_calls_timestamp(timestamp DESC),
        INDEX idx_calls_original_code_address(original_code_address),
        INDEX idx_calls_parsed_code_address(parsed_code_address),
        INDEX idx_calls_calling_function(calling_function)
    )
    ''')

    # # Create tvl table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tvl (
        total_tvl_balance DOUBLE,
        eth_tvl_balance DOUBLE,
        weth_tvl_balance DOUBLE,
        wbtc_tvl_balance DOUBLE,
        usdt_tvl_balance DOUBLE,
        usdc_tvl_balance DOUBLE,
        dai_tvl_balance DOUBLE
    )
    ''')
    cursor.execute("select count(*) from tvl")
    row = cursor.fetchone()
    if row[0] == 0:
        cursor.execute("INSERT INTO tvl (total_tvl_balance, eth_tvl_balance, weth_tvl_balance, wbtc_tvl_balance, usdt_tvl_balance, usdc_tvl_balance, dai_tvl_balance) VALUES (0, 0, 0, 0, 0, 0, 0)")

    # Create daily table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_stats (
        date VARCHAR(10) PRIMARY KEY,
        tx_count INT,
        authorization_count INT,
        code_count INT,
        relayer_count INT,
        cumulative_transaction_count INT,
        cumulative_authorization_count INT
    )
    ''')

    conn.commit()
    conn.close()


def update_info_by_block(mysql_db_name, block_db_path):
    info_conn = get_mysql_connection(mysql_db_name)
    info_cursor = info_conn.cursor()
    
    block_conn = sqlite3.connect(block_db_path)
    block_tx_cursor = block_conn.cursor()
    block_timestamp_cursor = block_conn.cursor()
    block_update_cursor = block_conn.cursor()
    block_tx_cursor.execute("SELECT block_number, tx_hash, tx_data FROM type4_transactions WHERE used=0 ORDER BY block_number ASC")
    
    wrong_block_number = 0
    tx_processed = 0
    start_time = time.perf_counter()
    batch_start_time = start_time
    
    # Process row by row to avoid loading all data at once
    for row in block_tx_cursor:  # Iterate cursor directly
        block_number, tx_hash, tx_data_str = row
        
        tx_hash = "0x"+tx_hash
        info_cursor.execute("SELECT tx_hash FROM transactions WHERE tx_hash = %s", (tx_hash,))
        if info_cursor.fetchone() is not None:
            # 如果交易已存在于MySQL中，标记为已使用
            block_update_cursor.execute("UPDATE type4_transactions SET used = 1 WHERE tx_hash = ?", (tx_hash[2:],))
            block_conn.commit()
            continue
        if "authorizationList" not in tx_data_str:
            wrong_block_number = block_number
            break

        type4_tx = util.parse_type4_tx_data(tx_data_str)
        
        block_timestamp_cursor.execute("SELECT timestamp FROM blocks WHERE block_number = ?", (type4_tx['block_number'],))
        get_timestamp = block_timestamp_cursor.fetchone()
        if get_timestamp is None:
            wrong_block_number = block_number
            break
        timestamp = get_timestamp[0]
        date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        info_cursor.execute("INSERT INTO transactions (tx_hash, block_number, block_hash, tx_index, relayer_address, authorization_fee, timestamp, authorization_list) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (type4_tx['tx_hash'], type4_tx['block_number'], type4_tx['block_hash'], type4_tx['tx_index'], type4_tx['relayer_address'], type4_tx['authorization_fee'], timestamp, json.dumps(type4_tx['authorization_list'])))
        
        for authorization in type4_tx['authorization_list']:
            info_cursor.execute("INSERT INTO authorizations (tx_hash, authorizer_address, code_address, relayer_address, date) VALUES (%s, %s, %s, %s, %s)", (type4_tx['tx_hash'], authorization['authorizer_address'], authorization['code_address'], type4_tx['relayer_address'], date))
            
            info_cursor.execute("SELECT authorizer_address FROM authorizers WHERE authorizer_address = %s", (authorization['authorizer_address'],))
            if info_cursor.fetchone() is None:
                info_cursor.execute("INSERT INTO authorizers (authorizer_address, tvl_balance, tvl_timestamp, last_nonce, last_chain_id, code_address, set_code_tx_count, unset_code_tx_count, historical_code_address_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (authorization['authorizer_address'], 0, 0, 0, 0, "", 0, 0, 0))
            
            
            info_cursor.execute("SELECT code_address FROM authorizers WHERE authorizer_address = %s", (authorization['authorizer_address'],))
            result = info_cursor.fetchone()
            current_code_address = result[0]
            if authorization['code_address'] != current_code_address and current_code_address != "0x0000000000000000000000000000000000000000" and current_code_address != "":
                info_cursor.execute("UPDATE authorizers SET historical_code_address_count = historical_code_address_count + 1 WHERE authorizer_address = %s", (authorization['authorizer_address'],))
            
                
            if authorization['code_address'] == "0x0000000000000000000000000000000000000000":
                info_cursor.execute("UPDATE authorizers SET unset_code_tx_count = unset_code_tx_count + 1 WHERE authorizer_address = %s", (authorization['authorizer_address'],))
            else:
                info_cursor.execute("UPDATE authorizers SET set_code_tx_count = set_code_tx_count + 1 WHERE authorizer_address = %s", (authorization['authorizer_address'],))
                
            if authorization['nonce'] > 2147483647:
                authorization['nonce'] = None
            if authorization['chain_id'] > 2147483647:
                authorization['chain_id'] = None
                
            info_cursor.execute("UPDATE authorizers SET  last_nonce = %s, last_chain_id = %s, code_address = %s WHERE authorizer_address = %s", (authorization['nonce'], authorization['chain_id'], authorization['code_address'], authorization['authorizer_address']))


        info_cursor.execute("SELECT relayer_address FROM relayers WHERE relayer_address = %s", (type4_tx['relayer_address'] ,))
        if info_cursor.fetchone() is not None:
            info_cursor.execute("UPDATE relayers SET tx_count = tx_count + 1, authorization_count = authorization_count + %s, authorization_fee = authorization_fee + %s WHERE relayer_address = %s", (len(type4_tx['authorization_list']), type4_tx['authorization_fee'], type4_tx['relayer_address'] ,))
        else:
            info_cursor.execute("INSERT INTO relayers (relayer_address, tx_count, authorization_count, authorization_fee) VALUES (%s, %s, %s, %s)", (type4_tx['relayer_address'] , 1, len(type4_tx['authorization_list']),  type4_tx['authorization_fee']))
            
        info_conn.commit()
        
        # 标记交易为已使用
        block_update_cursor.execute("UPDATE type4_transactions SET used = 1 WHERE tx_hash = ?", (tx_hash[2:],))
        block_conn.commit()
        
        tx_processed += 1
        
        # 每处理100个交易输出一次TPS
        if tx_processed % 100 == 0:
            batch_end_time = time.perf_counter()
            batch_duration = batch_end_time - batch_start_time
            batch_tps = 100 / batch_duration
            total_duration = batch_end_time - start_time
            total_tps = tx_processed / total_duration
            print(f"已处理 {tx_processed} 个交易 | 本批TPS: {batch_tps:.2f} | 总体TPS: {total_tps:.2f} #{block_number}")
            batch_start_time = batch_end_time


    if wrong_block_number > 0:
        print(f"Wrong block number: {wrong_block_number}")
        block_tx_cursor.execute("DELETE FROM type4_transactions WHERE block_number = ?", (wrong_block_number,))
        block_timestamp_cursor.execute("DELETE FROM blocks WHERE block_number = ?", (wrong_block_number,))
        block_conn.commit()

    info_conn.close()
    block_conn.close()
    

def update_info_by_tvl(mysql_db_name, tvl_db_path):
    info_conn = get_mysql_connection(mysql_db_name)
    info_read_cursor = info_conn.cursor()
    info_write_cursor = info_conn.cursor()
    
    tvl_conn = sqlite3.connect(tvl_db_path)
    tvl_cursor = tvl_conn.cursor()
    
    start_time = time.time()
    while True:
        try:
            BTC_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()['price']
            ETH_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=ETHUSDT",timeout=10).json()['price']
            
            if NAME == "bsc":
                BNB_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=BNBUSDT",timeout=10).json()['price']
            if NAME == "bera":
                BERA_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=BERAUSDT",timeout=10).json()['price']
            break
        except:
            time.sleep(1)
    end_time = time.time()
    print(f"Price update: {end_time - start_time} seconds")
    
    start_time = time.time()
    info_read_cursor.execute("SELECT authorizer_address FROM authorizers")
    count = 0
    for row in info_read_cursor:
        authorizer_address = row[0]
        count += 1
        tvl_cursor.execute("SELECT eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp FROM author_balances WHERE author_address = ?", (authorizer_address,))
        result = tvl_cursor.fetchone()
        if result is not None:
            eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance, timestamp = result
            if NAME == "bsc":
                tvl_balance = float(eth_balance) * float(BNB_PRICE) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) / 10**12 + float(usdc_balance) / 10**12 + float(dai_balance)
            elif NAME == "bera":
                tvl_balance = float(eth_balance) * float(BERA_PRICE) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) + float(usdc_balance) + float(dai_balance)
            elif NAME == "gnosis":
                tvl_balance = float(eth_balance) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) + float(usdc_balance) + float(dai_balance)
            else:
                tvl_balance = float(eth_balance) * float(ETH_PRICE) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) + float(usdc_balance) + float(dai_balance)
            info_write_cursor.execute("UPDATE authorizers SET tvl_balance = %s, tvl_timestamp = %s WHERE authorizer_address = %s", (tvl_balance, timestamp, authorizer_address))

    end_time = time.time()
    print(f"TVL [update]: {end_time - start_time} seconds, data count: {count}")
    
    start_time = time.time()
    tvl_cursor.execute("SELECT sum(eth_balance), sum(weth_balance), sum(wbtc_balance), sum(usdt_balance), sum(usdc_balance), sum(dai_balance) FROM author_balances")
    result = tvl_cursor.fetchone()
    if result is not None:
        eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance = result
        
        eth_tvl_balance = float(eth_balance) * float(ETH_PRICE)
        weth_tvl_balance = float(weth_balance) * float(ETH_PRICE)
        wbtc_tvl_balance = float(wbtc_balance) * float(BTC_PRICE)
        usdt_tvl_balance = float(usdt_balance)
        usdc_tvl_balance = float(usdc_balance)
        dai_tvl_balance = float(dai_balance)
        
        if NAME == "bsc":
            eth_tvl_balance = float(eth_balance) * float(BNB_PRICE)
            usdt_tvl_balance = float(usdt_balance) / 10**12
            usdc_tvl_balance = float(usdc_balance) / 10**12
        if NAME == "bera":
            eth_tvl_balance = float(eth_balance) * float(BERA_PRICE)
        if NAME == "gnosis":
            eth_tvl_balance = float(eth_balance)    
            
        total_tvl_balance = eth_tvl_balance + weth_tvl_balance + wbtc_tvl_balance + usdt_tvl_balance + usdc_tvl_balance + dai_tvl_balance
        
        info_write_cursor.execute("UPDATE tvl SET total_tvl_balance = %s, eth_tvl_balance = %s, weth_tvl_balance = %s, wbtc_tvl_balance = %s, usdt_tvl_balance = %s, usdc_tvl_balance = %s, dai_tvl_balance = %s", (
            total_tvl_balance,
            eth_tvl_balance, 
            weth_tvl_balance, 
            wbtc_tvl_balance, 
            usdt_tvl_balance, 
            usdc_tvl_balance, 
            dai_tvl_balance
        ))
        
        # print(f"Total TVL balance: {total_tvl_balance}")
        # print(eth_tvl_balance, weth_tvl_balance, wbtc_tvl_balance, usdt_tvl_balance, usdc_tvl_balance, dai_tvl_balance)

    end_time = time.time()
    print(f"TVL [sum]: {end_time - start_time} seconds")
    
    
    info_conn.commit()
    info_conn.close()
    tvl_conn.close()
        
    
def update_info_by_code(mysql_db_name, code_db_path):
    info_conn = get_mysql_connection(mysql_db_name)
    info_read_cursor = info_conn.cursor()
    info_write_cursor = info_conn.cursor()
    
    code_conn = sqlite3.connect(code_db_path)
    code_cursor = code_conn.cursor()
    
    code_address_to_type = {}
    code_info = json.load(open(f'code_info.json'))
    for item in code_info:
        code_address = item['address'].lower()
        code_address_to_type[code_address] = item['type']
    
    code_count_by_type = {}
    code_authorizer_by_type = {}
    code_tvl_by_type = {}
    
    code_count_by_tag = {}
    code_authorizer_by_tag = {}
    code_tvl_by_tag = {}
    
    info_read_cursor.execute("SELECT code_address, count(authorizer_address), sum(tvl_balance) FROM authorizers GROUP BY code_address")
    for row in info_read_cursor:
        code_address, authorizer_count, tvl_balance = row
        info_write_cursor.execute("INSERT INTO codes (code_address, authorizer_count, tvl_balance) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE authorizer_count = VALUES(authorizer_count), tvl_balance = VALUES(tvl_balance)", (code_address, authorizer_count, tvl_balance))
        
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
            
            for tag in tags:
                if tag not in code_count_by_tag:
                    code_count_by_tag[tag] = 0
                    code_authorizer_by_tag[tag] = 0
                    code_tvl_by_tag[tag] = 0
                code_count_by_tag[tag] += 1
                code_authorizer_by_tag[tag] += authorizer_count
                code_tvl_by_tag[tag] += tvl_balance
                
            if code_address in code_address_to_type:
                the_type = code_address_to_type[code_address]
            else:
                the_type = "Other"
                
            if the_type not in code_count_by_type:
                code_count_by_type[the_type] = 0
                code_authorizer_by_type[the_type] = 0
                code_tvl_by_type[the_type] = 0
            code_count_by_type[the_type] += 1
            code_authorizer_by_type[the_type] += authorizer_count
            code_tvl_by_type[the_type] += tvl_balance
                
            info_write_cursor.execute("UPDATE codes SET tags = %s WHERE code_address = %s", (json.dumps(tags), code_address))
    
    code_info = json.load(open(f'code_info.json'))
    for item in code_info:
        code_address = item['address'].lower()
        info_write_cursor.execute("UPDATE codes SET provider = %s, details = %s WHERE code_address = %s", (item['provider'], json.dumps(item), code_address))
    
    info_conn.commit()
    info_conn.close()
    
    code_statistics = {
        'code_count_by_type': code_count_by_type,
        'code_authorizer_by_type': code_authorizer_by_type,
        'code_tvl_by_type': code_tvl_by_type,
        'code_count_by_tag': code_count_by_tag,
        'code_authorizer_by_tag': code_authorizer_by_tag,
        'code_tvl_by_tag': code_tvl_by_tag
    }
    
    cache_path = f'/dev/shm/{NAME}_code_statistics.json'
    with open(cache_path, 'w') as f:
        json.dump(code_statistics, f)


def update_info_daily(mysql_db_name, from_latest=True):
    info_conn = get_mysql_connection(mysql_db_name)
    info_read_cursor = info_conn.cursor()
    info_write_cursor = info_conn.cursor()
    
    cumulative_tx_count = 0
    cumulative_authorization_count = 0
    
    if from_latest:
        info_read_cursor.execute("SELECT date, cumulative_transaction_count, cumulative_authorization_count FROM daily_stats ORDER BY date DESC LIMIT 3")
        rows = info_read_cursor.fetchall()
        if len(rows) >= 3:
            from_last_date = rows[2][0]
            cumulative_tx_count = rows[2][1]
            cumulative_authorization_count = rows[2][2]            
            info_read_cursor.execute("SELECT date, count(distinct tx_hash), count(distinct authorizer_address), count(distinct code_address), count(distinct relayer_address) FROM authorizations WHERE date > %s GROUP BY date", (from_last_date,))            
            for row in info_read_cursor:
                date, tx_count, authorization_count, code_count, relayer_count = row
                cumulative_tx_count += tx_count
                cumulative_authorization_count += authorization_count
                info_write_cursor.execute("INSERT INTO daily_stats (date, tx_count, authorization_count, code_count, relayer_count, cumulative_transaction_count, cumulative_authorization_count) VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE tx_count = VALUES(tx_count), authorization_count = VALUES(authorization_count), code_count = VALUES(code_count), relayer_count = VALUES(relayer_count), cumulative_transaction_count = VALUES(cumulative_transaction_count), cumulative_authorization_count = VALUES(cumulative_authorization_count)", (date, tx_count, authorization_count, code_count, relayer_count, cumulative_tx_count, cumulative_authorization_count))
            
        else:
            from_latest = False
            
            
    if not from_latest:    
        info_read_cursor.execute("SELECT date, count(distinct tx_hash), count(distinct authorizer_address), count(distinct code_address), count(distinct relayer_address) FROM authorizations GROUP BY date")
        for row in info_read_cursor:
            date, tx_count, authorization_count, code_count, relayer_count = row
            cumulative_tx_count += tx_count
            cumulative_authorization_count += authorization_count
            info_write_cursor.execute("INSERT INTO daily_stats (date, tx_count, authorization_count, code_count, relayer_count, cumulative_transaction_count, cumulative_authorization_count) VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE tx_count = VALUES(tx_count), authorization_count = VALUES(authorization_count), code_count = VALUES(code_count), relayer_count = VALUES(relayer_count), cumulative_transaction_count = VALUES(cumulative_transaction_count), cumulative_authorization_count = VALUES(cumulative_authorization_count)", (date, tx_count, authorization_count, code_count, relayer_count, cumulative_tx_count, cumulative_authorization_count))
    
    info_conn.commit()
    info_conn.close()


def update_info_by_trace(mysql_db_name, trace_db_path, block_db_path):
    info_conn = get_mysql_connection(mysql_db_name)
    info_cursor = info_conn.cursor()
    
    trace_conn = sqlite3.connect(trace_db_path)
    trace_cursor = trace_conn.cursor()
    
    block_conn = sqlite3.connect(block_db_path)
    block_timestamp_cursor = block_conn.cursor()
    
    
    trace_cursor.execute("SELECT block_number, traces FROM traces ORDER BY block_number ASC")
    
    wrong_block_number = 0
    # Process row by row to avoid loading all data at once
    for row in trace_cursor:  # Iterate cursor directly
        block_number, traces = row
        if traces == "[]":
            continue
        
        info_cursor.execute("SELECT tx_hash FROM calls WHERE block_number = %s", (block_number,))
        if info_cursor.fetchone() is not None:
            continue
        
        try:
            block_timestamp_cursor.execute("SELECT timestamp FROM blocks WHERE block_number = ?", (block_number,))
            timestamp = block_timestamp_cursor.fetchone()[0]
        except:
            print(f"Block {block_number} not found in blocks table")
            continue
        
        traces = json.loads(traces)

        for trace in traces:
            call_type_trace_address = trace['action']['callType'] + "_" + "_".join(str(x) for x in trace['traceAddress'])
            from_address = trace['action']['from']
            original_code_address = trace['action']['originalCodeAddress']
            parsed_code_address = trace['action']['parsedCodeAddress']
            value = trace['action']['value']
            calling_function = trace['action']['input'][:10]
            info_cursor.execute("INSERT INTO calls (tx_hash, block_number, tx_index, call_type_trace_address, from_address, original_code_address, parsed_code_address, value, calling_function, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (trace['transactionHash'], block_number, trace['transactionPosition'], call_type_trace_address, from_address, original_code_address, parsed_code_address, value, calling_function, timestamp))

        info_conn.commit()

    code_info = json.load(open(f'code_info.json'))
    code_address_to_type = {}
    code_address_to_provider = {}
    for item in code_info:
        code_address = item['address'].lower()
        code_address_to_type[code_address] = item['type']
        code_address_to_provider[code_address] = item['provider']
        
    top10_calling_functions = []
    info_cursor.execute("SELECT calling_function, count(*) FROM calls GROUP BY calling_function ORDER BY count(*) DESC LIMIT 10")
    for row in info_cursor:
        calling_function, count = row
        top10_calling_functions.append({'calling_function': calling_function, 'count': count})
    
    top10_parsed_code_addresses = []
    info_cursor.execute("SELECT parsed_code_address, count(*) FROM calls GROUP BY parsed_code_address ORDER BY count(*) DESC LIMIT 10")
    for row in info_cursor:
        parsed_code_address, count = row
        the_type = "Other"
        the_provider = ""
        if parsed_code_address in code_address_to_type:
            the_type = code_address_to_type[parsed_code_address]
            the_provider = code_address_to_provider[parsed_code_address]

        top10_parsed_code_addresses.append({
            'parsed_code_address': parsed_code_address,
            'count': count,
            'type': the_type,
            'provider': the_provider
        })

    info_conn.close()
    block_conn.close()

    trace_statistics = {
        'top10_calling_functions': top10_calling_functions,
        'top10_parsed_code_addresses': top10_parsed_code_addresses
    }
    
    cache_path = f'/dev/shm/{NAME}_trace_statistics.json'
    with open(cache_path, 'w') as f:
        json.dump(trace_statistics, f)
    
    
block_db_path = f'../backend/{NAME}_block.db'
if DB_PATH != None:
    if DB_PATH != '':
        block_db_path = f'{DB_PATH}/{NAME}_block.db'
tvl_db_path = f'../backend/{NAME}_tvl.db'
if DB_PATH != None:
    if DB_PATH != '':
        tvl_db_path = f'{DB_PATH}/{NAME}_tvl.db'
code_db_path = f'../backend/{NAME}_code.db'
if DB_PATH != None:
    if DB_PATH != '':
        code_db_path = f'{DB_PATH}/{NAME}_code.db'
trace_db_path = f'../backend/{NAME}_trace.db'

print(f"\nStarting to process {NAME} network...")

mysql_db_name = f'walletaa_{NAME}'

create_db_if_not_exists(mysql_db_name)
create_used_col_and_index(mysql_db_name, block_db_path)
start_time = time.time()
update_info_by_block(mysql_db_name, block_db_path)
end_time = time.time()
print(f"Block update: {end_time - start_time} seconds")

start_time = time.time()
update_info_by_tvl(mysql_db_name, tvl_db_path)
end_time = time.time()
print(f"TVL update: {end_time - start_time} seconds")

start_time = time.time()
update_info_by_code(mysql_db_name, code_db_path)
end_time = time.time()
print(f"Code update: {end_time - start_time} seconds")

start_time = time.time()
update_info_daily(mysql_db_name, from_latest=True)
end_time = time.time()
print(f"Daily update: {end_time - start_time} seconds")


# if NAME == "mainnet":
#     start_time = time.time()
#     update_info_by_trace(mysql_db_name, trace_db_path, block_db_path)
#     end_time = time.time()
#     print(f"Trace update: {end_time - start_time} seconds")