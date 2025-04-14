import requests
import os
import json
import time
import glob

try:
    os.mkdir("account_deplyed")
except:
    pass


address = "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789"

files = glob.glob(f'src/*_{address}_*.json')
files.sort()
chainids = []
for file in files:
    chainid = file.split('_')[0].split('/')[-1]
    if chainid not in chainids:
        chainids.append(chainid)
print(chainids)

chainids.sort()

last_blocknum = 0
last_logindex = 0

for chainid in chainids:
    f = open(f'account_deplyed/{chainid}.csv', "w")
    files = glob.glob(f'src/{chainid}_{address}_*.json')
    files.sort()
    for file in files:
        print(file)
        data = json.loads(open(file).read())
        for one in data["result"]:
            
            # avoid duplicate in source log data
            blocknum = int(one["blockNumber"], 16)
            logindex = 0
            if one["logIndex"] != "0x":
                int(one["logIndex"], 16) 
            if blocknum == last_blocknum and logindex <= last_logindex:
                continue
            else:
                last_blocknum = blocknum
                last_logindex = logindex

            if one["topics"][0] == "0xd51a9c61267aa6196961883ecf5ff2da6619c37dac0fa92122513fb32c032d2d":
                timestamp = int(one["timeStamp"], 16)
                sender = "0x" + one["topics"][2][26:]
                factory = "0x" + one["data"][26:66]
                paymaster = "0x" + one["data"][90:130]
                f.write(f"{blocknum},{timestamp},{sender},{factory},{paymaster}\n")
    f.close()    
