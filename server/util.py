import sqlite3
import json
from hexbytes import HexBytes
from eth_utils import to_bytes
from eth_account import Account
import rlp
from eth_utils import keccak
from datetime import datetime
from pyevmasm import disassemble_hex
import requests
import time

NAME = ""

PER_EMPTY_ACCOUNT_COST = 25000

def ecrecover(chain_id_, address_, nonce_, r_, s_, y_parity_):
    try:            
        chain_id = to_bytes(hexstr=chain_id_)
        address_bytes = to_bytes(hexstr=address_)
        nonce = to_bytes(hexstr=nonce_)

        # RLP encode [chain_id, address, nonce]
        encoded_data = rlp.encode([chain_id, address_bytes, nonce])

        # Construct EIP-7702 message: 0x05 || rlp(...)
        message_bytes = b'\x05' + encoded_data
        # Calculate Keccak-256 hash
        message_hash = keccak(message_bytes)

        # Convert signature components to standard format
        r_bytes = HexBytes(r_)
        s_bytes = HexBytes(s_)
        # yParity (0 or 1) is used directly
        y_parity = int(y_parity_, 16)

        # Create vrs tuple
        vrs = (y_parity, r_bytes, s_bytes)
        recovered_address = Account()._recover_hash(message_hash, vrs=vrs)
    except Exception as e:
        print(f"ecrecover error: {e}")
        return "error"
    else:
        return recovered_address

def parse_authorization(authorization):
    if type(authorization['chainId']) == int:
        authorization['chainId'] = hex(authorization['chainId'])
    if type(authorization['nonce']) == int:
        authorization['nonce'] = hex(authorization['nonce'])
    if type(authorization['yParity']) == int:
        authorization['yParity'] = hex(authorization['yParity'])
        
    authorizer_address = ecrecover(
        authorization['chainId'],
        authorization['address'],
        authorization['nonce'],
        authorization['r'],
        authorization['s'],
        authorization['yParity']
    )

    ret = {
        'authorizer_address': authorizer_address.lower(),
        'code_address': authorization['address'].lower(),
        'chain_id': int(authorization['chainId'], 16),
        'nonce': int(authorization['nonce'], 16),
    }

    return ret


def parse_type4_tx_data(tx_data_str_):
    tx_data = json.loads(tx_data_str_)
    
    authorization_list = []
    for authorization in tx_data['authorizationList']:
        parsed_result = parse_authorization(authorization)
        if parsed_result is not None:
            authorization_list.append(parsed_result)
        
    authorization_fee = PER_EMPTY_ACCOUNT_COST * len(authorization_list) * tx_data['gasPrice'] / 10**18
    
    ret = {
        'block_number': tx_data['blockNumber'],
        'block_hash': tx_data['blockHash'],
        'tx_index': tx_data['transactionIndex'],
        'tx_hash': '0x' + tx_data['hash'],
        'relayer_address': tx_data['from'].lower(),
        'authorization_fee': authorization_fee,
        'authorization_list': authorization_list,
    }
    return ret

def get_all_type4_txs():
    conn = sqlite3.connect(f'../backend/{NAME}_block.db')
    cursor = conn.cursor()
    # Get all type4 transaction data
    cursor.execute("SELECT tx_hash, tx_data FROM type4_transactions")
    rows = cursor.fetchall()
    
    type4_txs = []
    
    # Iterate through all transaction data
    for (tx_hash, tx_data_str) in rows:
        type4_tx = parse_type4_tx_data(tx_data_str)
        type4_txs.append(type4_tx)
    conn.close()

    return type4_txs

def get_timestamp_of_block():
    timestamp_of_block = {}
    conn = sqlite3.connect(f'../backend/{NAME}_block.db')
    cursor = conn.cursor()
    cursor.execute("SELECT block_number, timestamp  FROM blocks")
    rows = cursor.fetchall()
    for (block_number, timestamp) in rows:
        timestamp_of_block[block_number] = timestamp
    conn.close()
    return timestamp_of_block


def get_all_type4_txs_with_timestamp():
    txs = get_all_type4_txs()
    timestamp_of_block = get_timestamp_of_block()
    for i in range(len(txs)):
        txs[i]['timestamp'] = timestamp_of_block[txs[i]['block_number']]
    return txs

def is_target_tx(tx, search_by):
    if len(search_by) == 42:
        if search_by == tx['relayer_address']:
            return True
        for authorization in tx['authorization_list']:
            if search_by == authorization['code_address']:
                return True
            if search_by == authorization['authorizer_address']:
                return True
    if len(search_by) == 66:
        if search_by == tx['tx_hash']:
            return True
    return False

def get_authorizer_info(txs, code_infos, include_zero=False):
    balance_of= {}

    conn = sqlite3.connect(f'../backend/{NAME}_tvl.db')
    cursor = conn.cursor()
    # Query all addresses and balances
    
    while True:
        try:
            BTC_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=BTCUSDT").json()['price']
            ETH_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=ETHUSDT").json()['price']
            
            if NAME == "bsc":
                BNB_PRICE = requests.get("https://walletaa.com/api-binance/api/v3/ticker/price?symbol=BNBUSDT").json()['price']
            break
        except:
            time.sleep(1)
    
    cursor.execute("SELECT author_address, eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance FROM author_balances")
    data = cursor.fetchall()
    for address, eth_balance, weth_balance, wbtc_balance, usdt_balance, usdc_balance, dai_balance in data:
        if NAME != "bsc":
            balance_of[address] = float(eth_balance) * float(ETH_PRICE) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) + float(usdc_balance) + float(dai_balance)
        else:
            balance_of[address] = float(eth_balance) * float(BNB_PRICE) + float(weth_balance) * float(ETH_PRICE) + float(wbtc_balance) * float(BTC_PRICE) + float(usdt_balance) / 10**12 + float(usdc_balance) / 10**12 + float(dai_balance)

    conn.close()
            
    authorizer_info_dict = {}
    for tx in txs:
        for authorization in tx['authorization_list']:
            authorizer_address = authorization['authorizer_address']
            if authorizer_address not in authorizer_info_dict:
                authorizer_info_dict[authorizer_address] = {
                    'authorizer_address': authorizer_address,
                    'tvl_balance': 0,
                    'last_nonce': authorization['nonce'],
                    'last_chain_id': authorization['chain_id'],
                    'code_address': "0x0000000000000000000000000000000000000000",
                    'set_code_tx_count': 0,
                    'unset_code_tx_count': 0,
                    'historical_code_address': [],
                }
                if authorization['code_address'] == "0x0000000000000000000000000000000000000000":
                    authorizer_info_dict[authorizer_address]['unset_code_tx_count'] += 1
                    if authorizer_info_dict[authorizer_address]['code_address'] != "0x0000000000000000000000000000000000000000":
                        authorizer_info_dict[authorizer_address]['historical_code_address'].append(authorizer_info_dict[authorizer_address]['code_address'])
                else:
                    authorizer_info_dict[authorizer_address]['set_code_tx_count'] += 1
                authorizer_info_dict[authorizer_address]['code_address'] = authorization['code_address']
    
    code_to_provider = {}
    for code_info in code_infos:
        code_to_provider[code_info['address'].lower()] = code_info['provider']
    
    for authorizer_address in authorizer_info_dict:
        if authorizer_address in balance_of:
            authorizer_info_dict[authorizer_address]['tvl_balance'] = balance_of[authorizer_address]
        if authorizer_info_dict[authorizer_address]['code_address'] in code_to_provider:
            authorizer_info_dict[authorizer_address]['provider'] = code_to_provider[authorizer_info_dict[authorizer_address]['code_address']]

    authorizer_info = []
    for authorizer_address in authorizer_info_dict:
        if authorizer_address != "error":
            if not include_zero and authorizer_info_dict[authorizer_address]['code_address'] == "0x0000000000000000000000000000000000000000":
                continue
            authorizer_info.append(authorizer_info_dict[authorizer_address]) 
    authorizer_info.sort(key=lambda x: x['tvl_balance'], reverse=True)

    return authorizer_info

def is_target_authorizer_info_item(authorizer_info_item, search_by):
    if len(search_by) == 42:
        if authorizer_info_item['authorizer_address'] == search_by or authorizer_info_item['code_address'] == search_by:
            return True
    else:
        if 'provider' in authorizer_info_item and search_by in authorizer_info_item['provider'].lower():
            return True
    return False

def get_code_info(authorizer_info, code_infos, code_function_info, sort_by="tvl_balance"):
    code_info_dict = {}
    for authorizer in authorizer_info:
        code_address = authorizer['code_address']
        if code_address not in code_info_dict:
            code_info_dict[code_address] = {
                'code_address': code_address,
                'authorizer_count': 0,
                'tvl_balance': 0,
                'tags': [],
                'details': None,
                'provider': "",
            }
            if code_address in code_function_info:
                code_info_dict[code_address]['tags'] = code_function_info[code_address]
        code_info_dict[code_address]['authorizer_count'] += 1
        code_info_dict[code_address]['tvl_balance'] += authorizer['tvl_balance']
    
    for code_info in code_infos:
        code_address_lower = code_info['address'].lower()
        if code_address_lower in code_info_dict:
            code_info_dict[code_address_lower]['details'] = code_info
            code_info_dict[code_address_lower]['provider'] = code_info['provider']
    
    code_info = []
    for code_address in code_info_dict:
        code_info.append(code_info_dict[code_address])
    
    if sort_by == "tvl_balance":
        code_info.sort(key=lambda x: x['tvl_balance'], reverse=True)
    elif sort_by == "authorizer_count":
        code_info.sort(key=lambda x: x['authorizer_count'], reverse=True)
    
    return code_info

def is_target_code_info_item(code_info_item, search_by):
    if len(search_by) == 42:
        if code_info_item['code_address'].lower() == search_by:
            return True
    else:
        if search_by in code_info_item['provider'].lower():
            return True
        for tag in code_info_item['tags']:
            if search_by in tag.lower():
                return True
    return False

def get_relayer_info(txs, sort_by="tx_count"):
    relayer_info_dict = {}
    for tx in txs:
        relayer_address = tx['relayer_address']
        if relayer_address not in relayer_info_dict:
            relayer_info_dict[relayer_address] = {
                'relayer_address': relayer_address,
                'tx_count': 0,
                'authorization_count': 0,
                'authorization_fee': 0,
            }
        relayer_info_dict[relayer_address]['tx_count'] += 1
        relayer_info_dict[relayer_address]['authorization_fee'] += tx['authorization_fee']
        relayer_info_dict[relayer_address]['authorization_count'] += len(tx['authorization_list'])
    
    relayer_info = []
    for relayer_address in relayer_info_dict:
        relayer_info.append(relayer_info_dict[relayer_address])
        
    if sort_by == "tx_count":
        relayer_info.sort(key=lambda x: x['tx_count'], reverse=True)
    elif sort_by == "authorization_count":
        relayer_info.sort(key=lambda x: x['authorization_count'], reverse=True)
    elif sort_by == "authorization_fee":
        relayer_info.sort(key=lambda x: x['authorization_fee'], reverse=True)
        
    return relayer_info

def get_code_infos():
    with open('code_info.json', 'r', encoding='utf-8') as f:
        code_infos = json.load(f)
    return code_infos

def get_overview(txs, authorizers, codes, relayers, code_infos):
    daily_tx_count = {}
    for tx in txs:
        tx_date = datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d')
        if tx_date not in daily_tx_count:
            daily_tx_count[tx_date] = 0
        daily_tx_count[tx_date] += 1    
    
    daily_cumulative_tx_count = {}
    last_day_cumulative_tx_count = 0
    for tx_date in sorted(daily_tx_count.keys()):
        last_day_cumulative_tx_count += daily_tx_count[tx_date]
        daily_cumulative_tx_count[tx_date] = last_day_cumulative_tx_count
        
    daily_authorizaion_count = {}
    for tx in txs:
        tx_date = datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d')
        if tx_date not in daily_authorizaion_count:
            daily_authorizaion_count[tx_date] = 0
        daily_authorizaion_count[tx_date] += len(tx['authorization_list'])
    
    daily_code_set = {}
    for tx in txs:
        tx_date = datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d')
        if tx_date not in daily_code_set:
            daily_code_set[tx_date] = set()
        for authorization in tx['authorization_list']:
            daily_code_set[tx_date].add(authorization['code_address'])
    daily_code_count = {}
    for tx_date in daily_code_set:
        daily_code_count[tx_date] = len(daily_code_set[tx_date])
    
    
    daily_relayer_set = {}
    for tx in txs:
        tx_date = datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d')
        if tx_date not in daily_relayer_set:
            daily_relayer_set[tx_date] = set()
        daily_relayer_set[tx_date].add(tx['relayer_address'])
    daily_relayer_count = {}
    for tx_date in daily_relayer_set:
        daily_relayer_count[tx_date] = len(daily_relayer_set[tx_date])
    
    daily_cumulative_authorizaion_count = {}
    last_day_cumulative_authorizaion_count = 0
    for tx_date in sorted(daily_authorizaion_count.keys()):
        last_day_cumulative_authorizaion_count += daily_authorizaion_count[tx_date]
        daily_cumulative_authorizaion_count[tx_date] = last_day_cumulative_authorizaion_count
    
    top10_codes = codes[:10]
    top10_relayers = relayers[:10]
    
    top10_authorizers = authorizers[:10]
    code_to_provider = {}
    for code_info in code_infos:
        code_to_provider[code_info['address'].lower()] = code_info['provider']
    
    for i in range(len(top10_authorizers)):
        if top10_authorizers[i]['code_address'] in code_to_provider:
            top10_authorizers[i]['provider'] = code_to_provider[top10_authorizers[i]['code_address']]
    
    return {
        'tx_count': len(txs),
        'authorizer_count': len(authorizers),
        'code_count': len(codes),
        'relayer_count': len(relayers),
        'daily_tx_count': daily_tx_count,
        'daily_cumulative_tx_count': daily_cumulative_tx_count,
        'daily_authorizaion_count': daily_authorizaion_count,
        'daily_cumulative_authorizaion_count': daily_cumulative_authorizaion_count,
        'daily_code_count': daily_code_count,
        'daily_relayer_count': daily_relayer_count,
        'top10_codes': top10_codes,
        'top10_relayers': top10_relayers,
        'top10_authorizers': top10_authorizers,
    }


def parse_functions(code):
    disassembled = disassemble_hex(code)
    arr = disassembled.split("\n")
    # print(arr)
    functions = []
    for i in range(len(arr)):
        if arr[i].startswith("PUSH4"):
            if i+1 < len(arr) and arr[i+1] in ["EQ", "SUB"]:
                if i+2 < len(arr) and arr[i+2].startswith("PUSH2"):
                    if i+3 < len(arr) and arr[i+3] == "JUMPI":
                        functions.append(arr[i][6:])
    return functions


TAG_INFO = json.load(open('tag_info.json'))
FUNCTION_TO_TAGS = {}
for tag in TAG_INFO:
    for function in tag['functions']:
        function = "0x"+keccak(function.encode()).hex()[:8]
        if function not in FUNCTION_TO_TAGS:
            FUNCTION_TO_TAGS[function] = []
        FUNCTION_TO_TAGS[function].append(tag['tag'])


def get_code_function_info():
    conn = sqlite3.connect(f'../backend/{NAME}_code.db')
    cursor = conn.cursor()
    cursor.execute("SELECT code_address, code FROM codes") # WHERE code_address = '0x0c338ca25585035142a9a0a1eeeba267256f281f'")
    rows = cursor.fetchall()
    
    ret = {}
    # Iterate through all data
    for (code_address, code) in rows:
        functions = parse_functions(code)
        tags = []
        for function in functions:
            if function in FUNCTION_TO_TAGS:
                for tag in FUNCTION_TO_TAGS[function]:
                    if tag not in tags:
                        tags.append(tag)
        if len(tags) > 0:
            ret[code_address.lower()] = tags
        
    conn.close()
    return ret

# NAME = "mainnet"
# authorizer_info = get_authorizer_info(get_all_type4_txs(), get_code_infos())
# for i in authorizer_info[0:10]:
#     print(i["authorizer_address"], i["tvl_balance"])

# print("")
# code_info = get_code_info(authorizer_info, get_code_infos(), get_code_function_info())
# for i in code_info[0:10]:
#     print(i["code_address"], i["tvl_balance"])

# import time
# start_time = time.time()
# print(get_code_function_info())
# end_time = time.time()
# print(f"Time taken: {end_time - start_time} seconds")