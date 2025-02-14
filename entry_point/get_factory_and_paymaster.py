import requests
import os
import json
import time
import glob

try:
    os.mkdir("statistics")
except:
    pass

files = glob.glob(f'account_deplyed/*.csv')
files.sort()
chainids = []
for file in files:
    chainid = file[:-4].split('/')[-1]
    if chainid not in chainids:
        chainids.append(chainid)
print(chainids)

chainids.sort()

factories = {}
paymasters = {}

for chainid in chainids:
    lines = open(f'account_deplyed/{chainid}.csv').readlines()
    for line in lines:
        arr = line.strip().split(',')
        factory = arr[3]
        paymaster = arr[4]
        
        if factory not in factories:
            factories[factory] = 0
        factories[factory] += 1
        
        if paymaster not in paymasters:
            paymasters[paymaster] = 0
        paymasters[paymaster] += 1

factories_keys = []
factories_values = []
for factory in factories:
    factories_keys.append(factory)
    factories_values.append(factories[factory])

paymasters_keys = []
paymasters_values = []
for paymaster in paymasters:
    paymasters_keys.append(paymaster)
    paymasters_values.append(paymasters[paymaster])

for i in range(len(factories_keys)):
    for j in range(i+1, len(factories_keys)):
        if factories_values[i] < factories_values[j]:
            factories_keys[i], factories_keys[j] = factories_keys[j], factories_keys[i]
            factories_values[i], factories_values[j] = factories_values[j], factories_values[i]

for i in range(len(paymasters_keys)):
    for j in range(i+1, len(paymasters_keys)):
        if paymasters_values[i] < paymasters_values[j]:
            paymasters_keys[i], paymasters_keys[j] = paymasters_keys[j], paymasters_keys[i]
            paymasters_values[i], paymasters_values[j] = paymasters_values[j], paymasters_values[i]

f = open(f'statistics/factories.csv', 'w')
for i in range(len(factories_keys)):
    f.write(f'{factories_keys[i]},{factories_values[i]}\n')
f.close()

f = open(f'statistics/paymasters.csv', 'w')
for i in range(len(paymasters_keys)):
    f.write(f'{paymasters_keys[i]},{paymasters_values[i]}\n')
f.close()
