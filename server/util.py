import sqlite3
import json
from hexbytes import HexBytes
from eth_utils import to_bytes
from eth_account import Account
import rlp
from eth_utils import keccak
from datetime import datetime

NAME = ""

def ecrecover(chain_id_, address_, nonce_, r_, s_, y_parity_):
    try:
        if type(chain_id_) == int:
            chain_id_ = hex(chain_id_)
        if type(nonce_) == int:
            nonce_ = hex(nonce_)
        if type(y_parity_) == int:
            y_parity_ = hex(y_parity_)
            
        chain_id = to_bytes(hexstr=chain_id_)
        address_bytes = to_bytes(hexstr=address_)
        nonce = to_bytes(hexstr=nonce_)

        # RLP 编码 [chain_id, address, nonce]
        encoded_data = rlp.encode([chain_id, address_bytes, nonce])

        # 构造 EIP-7702 消息：0x05 || rlp(...)
        message_bytes = b'\x05' + encoded_data
        # 计算 Keccak-256 哈希
        message_hash = keccak(message_bytes)

        # 将签名组件转换为标准格式
        r_bytes = HexBytes(r_)
        s_bytes = HexBytes(s_)
        # yParity (0 or 1) is used directly
        y_parity = int(y_parity_, 16)

        # 创建vrs元组
        vrs = (y_parity, r_bytes, s_bytes)
        recovered_address = Account()._recover_hash(message_hash, vrs=vrs)
    except Exception as e:
        print(f"ecrecover error: {e}")
        return "error"
    else:
        return recovered_address

def parse_authorization(authorization):
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
        
    tx_fee = tx_data['gas'] * tx_data['gasPrice'] / 10**18
    
    ret = {
        'block_number': tx_data['blockNumber'],
        'block_hash': tx_data['blockHash'],
        'tx_index': tx_data['transactionIndex'],
        'tx_hash': '0x' + tx_data['hash'],
        'relayer_address': tx_data['from'].lower(),
        'tx_fee': tx_fee,
        'authorization_list': authorization_list,
    }
    return ret

def get_all_type4_txs():
    conn = sqlite3.connect(f'../backend/{NAME}_block.db')
    cursor = conn.cursor()
    # 获取所有type4交易数据
    cursor.execute("SELECT tx_hash, tx_data FROM type4_transactions")
    rows = cursor.fetchall()
    
    type4_txs = []
    
    # 遍历所有交易数据
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

def get_authorizer_info(txs, include_zero=False):
    balance_of= {}

    conn = sqlite3.connect(f'../backend/{NAME}_address.db')
    cursor = conn.cursor()
    # 查询所有地址和余额
    cursor.execute("SELECT author_address, eth_balance FROM author_balances")
    data = cursor.fetchall()
    for address, balance in data:
        balance_of[address] = float(balance)
    conn.close()
            
    authorizer_info_dict = {}
    for tx in txs:
        for authorization in tx['authorization_list']:
            authorizer_address = authorization['authorizer_address']
            if authorizer_address not in authorizer_info_dict:
                authorizer_info_dict[authorizer_address] = {
                    'authorizer_address': authorizer_address,
                    'eth_balance': 0,
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
    
    for authorizer_address in authorizer_info_dict:
        if authorizer_address in balance_of:
            authorizer_info_dict[authorizer_address]['eth_balance'] = balance_of[authorizer_address]

    authorizer_info = []
    for authorizer_address in authorizer_info_dict:
        if authorizer_address != "error":
            if not include_zero and authorizer_info_dict[authorizer_address]['code_address'] == "0x0000000000000000000000000000000000000000":
                continue
            authorizer_info.append(authorizer_info_dict[authorizer_address]) 
    authorizer_info.sort(key=lambda x: x['eth_balance'], reverse=True)

    return authorizer_info


def get_code_info(authorizer_info, sort_by="eth_balance"):
    code_info_dict = {}
    for authorizer in authorizer_info:
        code_address = authorizer['code_address']
        if code_address not in code_info_dict:
            code_info_dict[code_address] = {
                'code_address': code_address,
                'authorizer_count': 0,
                'eth_balance': 0,
            }
        code_info_dict[code_address]['authorizer_count'] += 1
        code_info_dict[code_address]['eth_balance'] += authorizer['eth_balance']
    
    code_info = []
    for code_address in code_info_dict:
        code_info.append(code_info_dict[code_address])
    
    if sort_by == "eth_balance":
        code_info.sort(key=lambda x: x['eth_balance'], reverse=True)
    elif sort_by == "authorizer_count":
        code_info.sort(key=lambda x: x['authorizer_count'], reverse=True)
    
    return code_info

def get_relayer_info(txs, sort_by="tx_count"):
    relayer_info_dict = {}
    for tx in txs:
        relayer_address = tx['relayer_address']
        if relayer_address not in relayer_info_dict:
            relayer_info_dict[relayer_address] = {
                'relayer_address': relayer_address,
                'tx_count': 0,
                'authorization_count': 0,
                'tx_fee': 0,
            }
        relayer_info_dict[relayer_address]['tx_count'] += 1
        relayer_info_dict[relayer_address]['tx_fee'] += tx['tx_fee']
        relayer_info_dict[relayer_address]['authorization_count'] += len(tx['authorization_list'])
    
    relayer_info = []
    for relayer_address in relayer_info_dict:
        relayer_info.append(relayer_info_dict[relayer_address])
        
    if sort_by == "tx_count":
        relayer_info.sort(key=lambda x: x['tx_count'], reverse=True)
    elif sort_by == "authorization_count":
        relayer_info.sort(key=lambda x: x['authorization_count'], reverse=True)
    elif sort_by == "tx_fee":
        relayer_info.sort(key=lambda x: x['tx_fee'], reverse=True)
        
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
        'code_infos': code_infos,
    }
