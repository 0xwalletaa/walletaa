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
chainids = [1, 10, 534352, 1101, 42161, 8453, 56, 137, 43114, 42220, 100] 
chainids.sort()

addresses = ["0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789", "0x0000000071727de22e5e9d8baf0edac6f37da032"]

for address in addresses:
    for chainid in chainids:
        fromBlock = 1
        lastlen = 1000
        while lastlen == 1000:
            filename = f'src/{chainid}_{address}_{fromBlock}.json'
            
            data = None
            needed = True
            if os.path.exists(filename):
                data = json.loads(open(filename).read())
                if data["result"] != None and len(data["result"]) == 1000:
                    needed = False

            if needed:
                url = f'https://api.etherscan.io/v2/api?chainid={chainid}&module=logs&action=getLogs&fromBlock={fromBlock}&address={address}&apikey={apikey}'
                try:
                    print(url)
                    resp = requests.get(url, timeout=30, proxies=proxy)
                    if resp.status_code != 200:
                        print(resp.status_code, "wrong")
                        time.sleep(1)
                        continue
                    data = resp.json()
                    if fromBlock > 1:
                        if int(data["result"][0]["blockNumber"], 16) != fromBlock:
                            raise("wrong fromBlock")
                    fromBlock = int(data["result"][-1]["blockNumber"], 16)
                    open(filename, 'w').write(resp.text)
                    
                except Exception as e:
                    print("error", e)
                    time.sleep(1)
                    continue
                
            lastlen = len(data["result"])
            print(filename, lastlen)
            
            fromBlock = int(data["result"][-1]["blockNumber"], 16)
            if chainid == 42220 and fromBlock == 30703153 and address=="0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789":
                fromBlock = 30730009
            if chainid == 42220 and fromBlock == 30798371 and address=="0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789":
                fromBlock = 30830002
        time.sleep(1)