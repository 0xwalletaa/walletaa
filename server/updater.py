import util
from flask import Flask, request, jsonify
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_cors import CORS
import random
import json
import pickle

for NAME in ["mainnet", "sepolia", "bsc", "op", "base"]:
    util.NAME = NAME

    start_time = time.time()
    code_infos = util.get_code_infos()
    txs = util.get_all_type4_txs_with_timestamp()
    authorizers = util.get_authorizer_info(txs, code_infos)
    authorizers_with_zero = util.get_authorizer_info(txs, code_infos, include_zero=True)
    code_function_info = util.get_code_function_info()
    codes_by_eth_balance = util.get_code_info(authorizers, code_infos, code_function_info, sort_by="eth_balance")
    codes_by_authorizer_count = util.get_code_info(authorizers, code_infos, code_function_info, sort_by="authorizer_count")
    relayers_by_tx_count = util.get_relayer_info(txs, sort_by="tx_count")
    relayers_by_authorization_count = util.get_relayer_info(txs, sort_by="authorization_count")
    relayers_by_authorization_fee = util.get_relayer_info(txs, sort_by="authorization_fee")
    overview = util.get_overview(txs, authorizers, codes_by_authorizer_count, relayers_by_tx_count, code_infos)
    last_update_time = time.time()
    end_time = time.time()
    print(f"{NAME} txs: {len(txs)}, 计算时间: {end_time - start_time} 秒")
    
    start_time = time.time()
    pickle.dump({
        'txs': txs,
        'authorizers': authorizers,
        'authorizers_with_zero': authorizers_with_zero,
        'codes_by_eth_balance': codes_by_eth_balance,
        'codes_by_authorizer_count': codes_by_authorizer_count,
        'relayers_by_tx_count': relayers_by_tx_count,
        'relayers_by_authorization_count': relayers_by_authorization_count,
        'relayers_by_authorization_fee': relayers_by_authorization_fee,
        'overview': overview,
        'last_update_time': last_update_time
    }, open(f'/dev/shm/{NAME}_data_temp.pkl', 'wb'))
    
    os.rename(f'/dev/shm/{NAME}_data_temp.pkl', f'/dev/shm/{NAME}_data.pkl')
    end_time = time.time()
    print(f"{NAME} txs: {len(txs)}, 存储时间: {end_time - start_time} 秒")
    print("--------------------------------")
    

for NAME in ["mainnet", "sepolia", "bsc", "op", "base"]:
    start_time = time.time()
    loaded_data = pickle.load(open(f'/dev/shm/{NAME}_data.pkl', 'rb'))
    end_time = time.time()
    print(f"{NAME} 加载时间: {end_time - start_time} 秒")
    print("--------------------------------")
