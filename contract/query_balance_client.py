from web3 import Web3
import json

# 连接到以太坊网络
# 这里使用Infura提供的以太坊主网节点，您需要替换为您自己的API密钥
w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.public.blastapi.io'))

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
                "internalType": "address",
                "name": "target",
                "type": "address"
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
                "internalType": "struct BalanceQuery.TokenBalances",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# 创建合约实例
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# 要查询的钱包地址
wallet_address = ''

# 调用合约的get函数查询余额
try:
    result = contract.functions.get(wallet_address).call()
    
    # 解析结果
    eth_balance = w3.from_wei(result[0], 'ether')
    weth_balance = w3.from_wei(result[1], 'ether')
    wbtc_balance = w3.from_wei(result[2], 'ether')  # 注意WBTC的精度可能是8
    usdt_balance = w3.from_wei(result[3], 'mwei')   # USDT通常是6位精度
    usdc_balance = w3.from_wei(result[4], 'mwei')   # USDC通常是6位精度
    dai_balance = w3.from_wei(result[5], 'ether')
    
    # 打印结果
    print(f"地址 {wallet_address} 的余额:")
    print(f"ETH: {eth_balance}")
    print(f"WETH: {weth_balance}")
    print(f"WBTC: {wbtc_balance}")
    print(f"USDT: {usdt_balance}")
    print(f"USDC: {usdc_balance}")
    print(f"DAI: {dai_balance}")
    
except Exception as e:
    print(f"调用合约时出错: {e}") 