import json
from hexbytes import HexBytes
from eth_utils import to_bytes
from eth_account import Account
import rlp
from eth_utils import keccak
from pyevmasm import disassemble_hex

PER_EMPTY_ACCOUNT_COST = 25000

def ecrecover(chain_id_, address_, nonce_, r_, s_, y_parity_):
    try:            
        # 将16进制字符串转为整数，让RLP库正确处理（0会被编码为空字节串）
        chain_id = int(chain_id_, 16)
        address_bytes = to_bytes(hexstr=address_)
        nonce = int(nonce_, 16)

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

