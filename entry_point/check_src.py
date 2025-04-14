import glob
import json
import os

files = glob.glob("src/*")
print(len(files))
cnt = 1
for filename in files:
    try:
        data = json.loads(open(filename).read())
        # filename = f'src/{chainid}_{address}_{fromBlock}.json'
        arr = filename.split("/")[1].split(".")[0].split("_")
        fromBlock = int(arr[2])
        if fromBlock > 1:
            if int(data["result"][0]["blockNumber"], 16) != fromBlock:
                print(filename, int(data["result"][0]["blockNumber"], 16), "???")            
    except:
        print(filename)
        # os.unlink(filename)
    cnt += 1
    if cnt % 10000 == 0:
        print(cnt)