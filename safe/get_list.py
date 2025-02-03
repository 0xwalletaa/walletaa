import requests
import os
import json
import time
import glob

try:
    os.mkdir("list")
except:
    pass


address = "0x4e1dcf7ad4e460cfd30791ccc4f9c8a4f820ec67"
topic0 = "0x4f51faf6c4561ff95f067657e43439f0f856d97c04d9ec9070a6199ad418e235"

# filename = f'src/{chainid}_{address}_{topic0}_{fromBlock}.json'
files = glob.glob(f'src/*_{address}_{topic0}_*.json')
files.sort()
chainids = []
for file in files:
    chainid = file.split('_')[0].split('/')[-1]
    if chainid not in chainids:
        chainids.append(chainid)
print(chainids)


for chainid in chainids:
    f = open(f'list/{chainid}.csv', "w")
    files = glob.glob(f'src/{chainid}_{address}_{topic0}_*.json')
    files.sort()
    for file in files:
        print(file)
        data = json.loads(open(file).read())
        for one in data["result"]:
            blocknum = int(one["blockNumber"], 16)
            timestamp = int(one["timeStamp"], 16)
            created_addr = "0x" + one["topics"][1][26:]
            f.write(f"{blocknum},{timestamp},{created_addr}\n")
    f.close()    
