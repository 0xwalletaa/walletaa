import util
import time
import logging
import os
import json
import sqlite3
import requests
import datetime

NAME = os.environ.get("NAME")
start_time = time.time()

# Database path
DB_PATH = f'./db/{NAME}.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row  # Make returned results accessible like a dictionary

cursor = conn.cursor()

# Get basic statistical information
cursor.execute('SELECT COUNT(*) as tx_count FROM transactions')
tx_count = cursor.fetchone()['tx_count']

cursor.execute('SELECT COUNT(*) as authorizer_count FROM authorizers WHERE code_address != "0x0000000000000000000000000000000000000000"')
authorizer_count = cursor.fetchone()['authorizer_count']

cursor.execute('SELECT COUNT(*) as code_count FROM codes')
code_count = cursor.fetchone()['code_count']

cursor.execute('SELECT COUNT(*) as relayer_count FROM relayers')
relayer_count = cursor.fetchone()['relayer_count']

# Get daily statistical data
cursor.execute('SELECT * FROM daily_stats ORDER BY date')
daily_stats = cursor.fetchall()

daily_tx_count = {}
daily_cumulative_tx_count = {}
daily_authorization_count = {}
daily_cumulative_authorization_count = {}
daily_code_count = {}
daily_relayer_count = {}

for row in daily_stats:
    date = row['date']
    daily_tx_count[date] = row['tx_count']
    daily_cumulative_tx_count[date] = row['cumulative_transaction_count']
    daily_authorization_count[date] = row['authorization_count']
    daily_cumulative_authorization_count[date] = row['cumulative_authorization_count']
    daily_code_count[date] = row['code_count']
    daily_relayer_count[date] = row['relayer_count']

# Get top10 data
cursor.execute('SELECT * FROM codes ORDER BY authorizer_count DESC LIMIT 10')
top10_codes_rows = cursor.fetchall()
top10_codes = []
for row in top10_codes_rows:
    code = dict(row)
    code['tags'] = json.loads(code['tags']) if code['tags'] else []
    code['details'] = json.loads(code['details']) if code['details'] else None
    code['type'] = code['details']['type'] if code['details'] and 'type' in code['details'] else ""
    top10_codes.append(code)

cursor.execute('SELECT * FROM relayers ORDER BY tx_count DESC LIMIT 10')
top10_relayers = [dict(row) for row in cursor.fetchall()]

cursor.execute('''
    SELECT a.*, c.provider 
    FROM (
        SELECT * FROM authorizers 
        WHERE code_address != "0x0000000000000000000000000000000000000000" 
        ORDER BY tvl_balance DESC 
        LIMIT 10
    ) a 
    LEFT JOIN codes c ON a.code_address = c.code_address
''')
top10_authorizers_rows = cursor.fetchall()
top10_authorizers = []
for row in top10_authorizers_rows:
    auth = dict(row)
    auth['historical_code_address'] = json.loads(auth['historical_code_address']) if auth['historical_code_address'] else []
    top10_authorizers.append(auth)

cursor.execute('SELECT * FROM tvl')
tvl_balance = cursor.fetchone()
conn.close()

tvls = {
    'total_tvl_balance': tvl_balance['total_tvl_balance'],
    'eth_tvl_balance': tvl_balance['eth_tvl_balance'], 
    'weth_tvl_balance': tvl_balance['weth_tvl_balance'], 
    'wbtc_tvl_balance': tvl_balance['wbtc_tvl_balance'], 
    'usdt_tvl_balance': tvl_balance['usdt_tvl_balance'], 
    'usdc_tvl_balance': tvl_balance['usdc_tvl_balance'], 
    'dai_tvl_balance': tvl_balance['dai_tvl_balance']
}

overview = {
    'tx_count': tx_count,
    'authorizer_count': authorizer_count,
    'code_count': code_count,
    'relayer_count': relayer_count,
    'daily_tx_count': daily_tx_count,
    'daily_cumulative_tx_count': daily_cumulative_tx_count,
    'daily_authorizaion_count': daily_authorization_count,
    'daily_cumulative_authorizaion_count': daily_cumulative_authorization_count,
    'daily_code_count': daily_code_count,
    'daily_relayer_count': daily_relayer_count,
    'top10_codes': top10_codes,
    'top10_relayers': top10_relayers,
    'top10_authorizers': top10_authorizers,
    'tvls': tvls
}

cache_path = f'/dev/shm/{NAME}_overview.json'
with open(cache_path, 'w') as f:
    json.dump(overview, f)

end_time = time.time()
print(f"Cached {cache_path} in {end_time - start_time} seconds")