import sqlite3
import json
from hexbytes import HexBytes
from eth_utils import to_bytes
from eth_account import Account
import rlp
from eth_utils import keccak


def ecrecover(chain_id_, address_, nonce_, r_, s_, y_parity_):
    try:
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
        'tx_hash': tx_data['hash'],
        'relayer_address': tx_data['from'].lower(),
        'tx_fee': tx_fee,
        'authorization_list': authorization_list,
    }
    return ret

def get_all_type4_txs():
    conn = sqlite3.connect('sepolia_blocks.db')
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
    conn = sqlite3.connect('sepolia_blocks.db')
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

    conn = sqlite3.connect('author_tvl.db')
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

"""
Type4交易示例
('ddf4aef622b21511447ee55f417ef76acaeaf8e4d8b4f587bbfa2bf9e24eee97', 8033831, '{"blockHash": "953c5893e1e7c4c9a350fe9778f6dd69965b93207d4b686017f1a1b94ce4c621", "blockNumber": 8033831, "from": "0x54c5E297819D1BF7bbF6a9d3B129b5BBfcA99171", "gas": 4918696, "gasPrice": 708846590, "maxPriorityFeePerGas": 100000000, "maxFeePerGas": 873235169, "hash": "ddf4aef622b21511447ee55f417ef76acaeaf8e4d8b4f587bbfa2bf9e24eee97", "input": "0x0000", "nonce": 68, "to": "0x0000000071727De22E5E9d8BAf0edAc6f37da032", "transactionIndex": 94, "value": 0, "type": 4, "accessList": [], "chainId": 11155111, "authorizationList": [{"chainId": "0xaa36a7", "address": "0x69007702764179f14f51cdce752f4f775d74e139", "nonce": "0x0", "yParity": "0x1", "r": "0xc6763bea75391f2e3ded5de88fc9f37dfb36b4166af73f3732ea31331ca292e0", "s": "0x58bc8fc791548d0f90eefaaa72623b54d1e5b7f0bbf94d23d95dad230e228cad"}], "v": 0, "yParity": 0, "r": "2e87f05f6b1d3352c1cff1b90a1528f002c5c9f99072fa49a7ed2d37153f19df", "s": "5a3f5f3045a41ed862e8814a7eb712c0a9c291bbb63b7527d705683bd0c0c4f1"}')
"""
