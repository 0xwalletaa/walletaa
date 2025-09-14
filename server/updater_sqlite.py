import util
import time
import logging
import os
import json
import sqlite3
import requests
import datetime

NAME = os.environ.get("NAME")
BLOCK_DB_PATH = os.environ.get("BLOCK_DB_PATH")
DATA_EXPIRY = 86400

def create_db_if_not_exists(db_path):
    """Create information database and table structure"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create transactions table
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
    
    
    # Create authorizations table
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

    # Create authorizers table
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
        historical_code_address_count INTEGER
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_tvl_balance ON authorizers(tvl_balance DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_tvl_timestamp ON authorizers(tvl_timestamp ASC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_code_address ON authorizers(code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_authorizers_historical_code_address_count ON authorizers(historical_code_address_count DESC)')
    
    # Create codes table
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
    
    # Create relayers table
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
    
    # Crate calls table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS calls (
        tx_hash TEXT,
        block_number INTEGER,
        tx_index INTEGER,
        call_type_trace_address TEXT,
        from_address TEXT,
        original_code_address TEXT,
        parsed_code_address TEXT,
        value TEXT,
        calling_function TEXT,
        timestamp INTEGER
    )
    ''')    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_block_number ON calls(block_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_timestamp ON calls(timestamp DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_original_code_address ON calls(original_code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_parsed_code_address ON calls(parsed_code_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_calling_function ON calls(calling_function)')

    # # Create tvl table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tvl (
        total_tvl_balance REAL,
        eth_tvl_balance REAL,
        weth_tvl_balance REAL,
        wbtc_tvl_balance REAL,
        usdt_tvl_balance REAL,
        usdc_tvl_balance REAL,
        dai_tvl_balance REAL
    )
    ''')
    cursor.execute("select count(*) from tvl")
    row = cursor.fetchone()
    if row[0] == 0:
        cursor.execute("INSERT INTO tvl (total_tvl_balance, eth_tvl_balance, weth_tvl_balance, wbtc_tvl_balance, usdt_tvl_balance, usdc_tvl_balance, dai_tvl_balance) VALUES (0, 0, 0, 0, 0, 0, 0)")

    # Create daily table
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
    block_tx_cursor.execute("SELECT block_number, tx_hash, tx_data FROM type4_transactions ORDER BY block_number ASC")
    
    wrong_block_number = 0
    # Process row by row to avoid loading all data at once
    for row in block_tx_cursor:  # Iterate cursor directly
        block_number, tx_hash, tx_data_str = row
        
        tx_hash = "0x"+tx_hash
        info_cursor.execute("SELECT tx_hash FROM transactions WHERE tx_hash = ?", (tx_hash,))
        if info_cursor.fetchone() is not None:
            continue
        if "authorizationList" not in tx_data_str:
            wrong_block_number = block_number
            break

        type4_tx = util.parse_type4_tx_data(tx_data_str)
        
        block_timestamp_cursor.execute("SELECT timestamp FROM blocks WHERE block_number = ?", (type4_tx['block_number'],))
        timestamp = block_timestamp_cursor.fetchone()[0]
        date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        info_cursor.execute("INSERT INTO transactions (tx_hash, block_number, block_hash, tx_index, relayer_address, authorization_fee, timestamp, authorization_list) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (type4_tx['tx_hash'], type4_tx['block_number'], type4_tx['block_hash'], type4_tx['tx_index'], type4_tx['relayer_address'], type4_tx['authorization_fee'], timestamp, json.dumps(type4_tx['authorization_list'])))
        
        for authorization in type4_tx['authorization_list']:
            info_cursor.execute("INSERT INTO authorizations (tx_hash, authorizer_address, code_address, relayer_address, date) VALUES (?, ?, ?, ?, ?)", (type4_tx['tx_hash'], authorization['authorizer_address'], authorization['code_address'], type4_tx['relayer_address'], date))
            
            info_cursor.execute("SELECT authorizer_address FROM authorizers WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            if info_cursor.fetchone() is None:
                info_cursor.execute("INSERT INTO authorizers (authorizer_address, tvl_balance, tvl_timestamp, last_nonce, last_chain_id, code_address, set_code_tx_count, unset_code_tx_count, historical_code_address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (authorization['authorizer_address'], 0, 0, 0, 0, "", 0, 0, json.dumps([])))
            
            
            row = info_cursor.execute("SELECT code_address, historical_code_address FROM authorizers WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            current_code_address, current_historical_code_address_json = row.fetchone()
            if authorization['code_address'] != current_code_address and current_code_address != "0x0000000000000000000000000000000000000000" and current_code_address != "":
                current_historical_code_address = json.loads(current_historical_code_address_json)
                current_historical_code_address.append(current_code_address)
                info_cursor.execute("UPDATE authorizers SET historical_code_address = ?, historical_code_address_count = ? WHERE authorizer_address = ?", (json.dumps(current_historical_code_address), len(current_historical_code_address), authorization['authorizer_address']))
            
                
            if authorization['code_address'] == "0x0000000000000000000000000000000000000000":
                info_cursor.execute("UPDATE authorizers SET unset_code_tx_count = unset_code_tx_count + 1 WHERE authorizer_address = ?", (authorization['authorizer_address'],))
            else:
                info_cursor.execute("UPDATE authorizers SET set_code_tx_count = set_code_tx_count + 1 WHERE authorizer_address = ?", (authorization['authorizer_address'],))
                
            if authorization['nonce'] > 2147483647:
                authorization['nonce'] = None
            if authorization['chain_id'] > 2147483647:
                authorization['chain_id'] = None
                
            info_cursor.execute("UPDATE authorizers SET  last_nonce = ?, last_chain_id = ?, code_address = ? WHERE authorizer_address = ?", (authorization['nonce'], authorization['chain_id'], authorization['code_address'], authorization['authorizer_address']))


        info_cursor.execute("SELECT relayer_address FROM relayers WHERE relayer_address = ?", (type4_tx['relayer_address'] ,))
        if info_cursor.fetchone() is not None:
            info_cursor.execute("UPDATE relayers SET tx_count = tx_count + 1, authorization_count = authorization_count + ?, authorization_fee = authorization_fee + ? WHERE relayer_address = ?", (len(type4_tx['authorization_list']), type4_tx['authorization_fee'], type4_tx['relayer_address'] ,))
        else:
            info_cursor.execute("INSERT INTO relayers (relayer_address, tx_count, authorization_count, authorization_fee) VALUES (?, ?, ?, ?)", (type4_tx['relayer_address'] , 1, len(type4_tx['authorization_list']),  type4_tx['authorization_fee']))
            
        info_conn.commit()


    if wrong_block_number > 0:
        print(f"Wrong block number: {wrong_block_number}")
        block_tx_cursor.execute("DELETE FROM type4_transactions WHERE block_number = ?", (wrong_block_number,))
        block_timestamp_cursor.execute("DELETE FROM blocks WHERE block_number = ?", (wrong_block_number,))
        block_conn.commit()

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
    info_read_cursor.execute("SELECT authorizer_address FROM authorizers WHERE tvl_timestamp < ?", (int(time.time()) - DATA_EXPIRY,))
    expired_count = 0
    for row in info_read_cursor:
        authorizer_address = row[0]
        expired_count += 1
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
            info_write_cursor.execute("UPDATE authorizers SET tvl_balance = ?, tvl_timestamp = ? WHERE authorizer_address = ?", (tvl_balance, timestamp, authorizer_address))

    end_time = time.time()
    print(f"TVL [expired]: {end_time - start_time} seconds, data count: {expired_count}")
    
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
        
        info_write_cursor.execute("UPDATE tvl SET total_tvl_balance = ?, eth_tvl_balance = ?, weth_tvl_balance = ?, wbtc_tvl_balance = ?, usdt_tvl_balance = ?, usdc_tvl_balance = ?, dai_tvl_balance = ?", (
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
        
    
def update_info_by_code(info_db_path, code_db_path):
    info_conn = sqlite3.connect(info_db_path)
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
                
            info_write_cursor.execute("UPDATE codes SET tags = ? WHERE code_address = ?", (json.dumps(tags), code_address))
    
    code_info = json.load(open(f'code_info.json'))
    for item in code_info:
        code_address = item['address'].lower()
        info_write_cursor.execute("UPDATE codes SET provider = ?, details = ? WHERE code_address = ?", (item['provider'], json.dumps(item), code_address))
    
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


def update_info_daily(info_db_path, from_latest=True):
    info_conn = sqlite3.connect(info_db_path)
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
            info_read_cursor.execute("SELECT date, count(distinct tx_hash), count(distinct authorizer_address), count(distinct code_address), count(distinct relayer_address) FROM authorizations WHERE date > ? GROUP BY date", (from_last_date,))            
            for row in info_read_cursor:
                date, tx_count, authorization_count, code_count, relayer_count = row
                cumulative_tx_count += tx_count
                cumulative_authorization_count += authorization_count
                info_write_cursor.execute("INSERT INTO daily_stats (date, tx_count, authorization_count, code_count, relayer_count, cumulative_transaction_count, cumulative_authorization_count) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(date) DO UPDATE SET tx_count = excluded.tx_count, authorization_count = excluded.authorization_count, code_count = excluded.code_count, relayer_count = excluded.relayer_count, cumulative_transaction_count = excluded.cumulative_transaction_count, cumulative_authorization_count = excluded.cumulative_authorization_count", (date, tx_count, authorization_count, code_count, relayer_count, cumulative_tx_count, cumulative_authorization_count))
            
        else:
            from_latest = False
            
            
    if not from_latest:    
        info_read_cursor.execute("SELECT date, count(distinct tx_hash), count(distinct authorizer_address), count(distinct code_address), count(distinct relayer_address) FROM authorizations GROUP BY date")
        for row in info_read_cursor:
            date, tx_count, authorization_count, code_count, relayer_count = row
            cumulative_tx_count += tx_count
            cumulative_authorization_count += authorization_count
            info_write_cursor.execute("INSERT INTO daily_stats (date, tx_count, authorization_count, code_count, relayer_count, cumulative_transaction_count, cumulative_authorization_count) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(date) DO UPDATE SET tx_count = excluded.tx_count, authorization_count = excluded.authorization_count, code_count = excluded.code_count, relayer_count = excluded.relayer_count, cumulative_transaction_count = excluded.cumulative_transaction_count, cumulative_authorization_count = excluded.cumulative_authorization_count", (date, tx_count, authorization_count, code_count, relayer_count, cumulative_tx_count, cumulative_authorization_count))
    
    info_conn.commit()
    info_conn.close()


def update_info_by_trace(info_db_path, trace_db_path, block_db_path):
    info_conn = sqlite3.connect(info_db_path)
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
        
        info_cursor.execute("SELECT tx_hash FROM calls WHERE block_number = ?", (block_number,))
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
            info_cursor.execute("INSERT INTO calls (tx_hash, block_number, tx_index, call_type_trace_address, from_address, original_code_address, parsed_code_address, value, calling_function, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (trace['transactionHash'], block_number, trace['transactionPosition'], call_type_trace_address, from_address, original_code_address, parsed_code_address, value, calling_function, timestamp))

        info_conn.commit()

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
        top10_parsed_code_addresses.append({
            'parsed_code_address': parsed_code_address,
            'count': count,
            'type': code_address_to_type[parsed_code_address],
            'provider': code_address_to_provider[parsed_code_address]
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
if BLOCK_DB_PATH != '':
    block_db_path = f'{BLOCK_DB_PATH}/{NAME}_block.db'
tvl_db_path = f'../backend/{NAME}_tvl.db'
code_db_path = f'../backend/{NAME}_code.db'
trace_db_path = f'../backend/{NAME}_trace.db'

try:
    os.mkdir('db')
except:
    pass

info_db_path = f'./db/{NAME}.db'
print(f"\nStarting to process {NAME} network...")

create_db_if_not_exists(info_db_path)
start_time = time.time()
update_info_by_block(info_db_path, block_db_path)
end_time = time.time()
print(f"Block update: {end_time - start_time} seconds")

start_time = time.time()
update_info_by_tvl(info_db_path, tvl_db_path)
end_time = time.time()
print(f"TVL update: {end_time - start_time} seconds")

start_time = time.time()
update_info_by_code(info_db_path, code_db_path)
end_time = time.time()
print(f"Code update: {end_time - start_time} seconds")

start_time = time.time()
update_info_daily(info_db_path, from_latest=True)
end_time = time.time()
print(f"Daily update: {end_time - start_time} seconds")


if NAME == "mainnet":
    start_time = time.time()
    update_info_by_trace(info_db_path, trace_db_path, block_db_path)
    end_time = time.time()
    print(f"Trace update: {end_time - start_time} seconds")