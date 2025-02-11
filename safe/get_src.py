import requests
import os
import json
import time

apikey = open('../etherscan.key').read()

try:
    os.mkdir("src")
except:
    pass

proxy = None
try:
    proxy = json.loads(open('../proxy.json').read())
except:
    pass

# ETH 1 # OP 10 # Scroll 534352 # Polygon zkEVM 1101 # Arbitrum One 42161 # Base 8453 # BSC 56 # Polygon Mainnet 137 # Fantom Opera 250 # Avalanche C-Chain 43114 # Celo 42220 # Gnosis 100
chainids = [1, 10, 534352, 1101, 42161, 8453, 56, 137, 250, 43114, 42220, 100] 
address = "0x4e1dcf7ad4e460cfd30791ccc4f9c8a4f820ec67"
# ProxyCreation (index_topic_1 address proxy, address singleton)
topic0 = "0x4f51faf6c4561ff95f067657e43439f0f856d97c04d9ec9070a6199ad418e235"

# Factory contracts 
# SafeProxyFactory at 0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67 (EVM), 0xc329D02fd8CB2fc13aa919005aF46320794a8629 (zkSync)

for chainid in chainids:
    fromBlock = 1
    lastlen = 1000
    while lastlen == 1000:
        filename = f'src/{chainid}_{address}_{topic0}_{fromBlock}.json'
        
        data = None
        needed = True
        if os.path.exists(filename):
            data = json.loads(open(filename).read())
            if len(data["result"]) == 1000:
                needed = False

        if needed:
            url = f'https://api.etherscan.io/v2/api?chainid={chainid}&module=logs&action=getLogs&fromBlock={fromBlock}&address={address}&topic0={topic0}&apikey={apikey}'
            try:
                resp = requests.get(url, proxies=proxy)
                if resp.status_code != 200:
                    print(resp.status_code, "wrong")
                    time.sleep(1)
                    continue
                data = resp.json()
                open(filename, 'w').write(resp.text)
                
            except Exception as e:
                print("error", e)
                print("resp", resp.text)
                time.sleep(1)
                continue
            
        lastlen = len(data["result"])
        print(filename, lastlen)
        
        fromBlock = int(data["result"][-1]["blockNumber"], 16)
