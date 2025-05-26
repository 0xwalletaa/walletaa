from web3 import Web3
import json
import time

def format_balance(balance, decimals=18, symbol=""):
    """格式化余额显示"""
    if decimals == 18:
        formatted = Web3.from_wei(balance, 'ether')
    else:
        formatted = balance / (10 ** decimals)
    return f"{formatted:.{decimals//3}f} {symbol}".strip()

# 连接到以太坊网络
# 这里使用Infura提供的以太坊主网节点，您需要替换为您自己的API密钥
w3 = Web3(Web3.HTTPProvider('https://base-mainnet.public.blastapi.io'))

# 检查连接
if not w3.is_connected():
    print("未能连接到以太坊网络")
    exit()

# 已部署的合约地址（需要替换为实际部署地址）
contract_address = ''

# 合约ABI
contract_abi = [
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "targets",
                "type": "address[]"
            }
        ],
        "name": "get",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "uint256",
                        "name": "ethBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "wethBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "wbtcBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "usdtBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "usdcBalance",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "daiBalance",
                        "type": "uint256"
                    }
                ],
                "internalType": "struct BalanceQuery.TokenBalances[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# 创建合约实例
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# 要查询的钱包地址列表
wallet_addresses = [
    '','',''
]


# 调用合约的get函数查询余额
try:
    start_time = time.time()
    result = contract.functions.get(wallet_addresses).call()
    
    # 解析结果
    item_cnt = 0
    for i, address in enumerate(wallet_addresses):
        balances = result[i]
        item_cnt += 1
        print(f"\n地址 {address} 的余额:")
        print(f"ETH:  {format_balance(balances[0], 18, 'ETH')}")
        print(f"WETH: {format_balance(balances[1], 18, 'WETH')}")
        print(f"WBTC: {format_balance(balances[2], 8, 'WBTC')}")
        print(f"USDT: {format_balance(balances[3], 6, 'USDT')}")
        print(f"USDC: {format_balance(balances[4], 6, 'USDC')}")
        print(f"DAI:  {format_balance(balances[5], 18, 'DAI')}")
    
    end_time = time.time()
    print(f"item_cnt: {item_cnt}")
    print(f"time: {end_time - start_time}")
    
except Exception as e:
    print(f"调用合约时出错: {e}") 