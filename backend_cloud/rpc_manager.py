#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RPC endpoint manager.

从 https://chainlist.org/rpcs.json 获取各链公共 RPC 列表, 缓存到本目录
rpc_<YYYYmmdd_HHMMSS>.json (一周内的缓存直接复用, 多进程安全),
并对候选端点做并发存活探测, 输出可用端点列表。

用法 (作为库):
    import rpc_manager
    endpoints = rpc_manager.get_alive_endpoints('arb', require_batch=True)

用法 (命令行, stdout 每行一个可用端点, 诊断信息走 stderr):
    python3 rpc_manager.py --name arb --require_batch
"""

import os
import re
import sys
import json
import glob
import time
import random
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor

CHAINLIST_URL = 'https://chainlist.org/rpcs.json'
CACHE_MAX_AGE = 7 * 86400  # 一周
CACHE_PREFIX = 'rpc_'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 各链配置: chain_id, 批量获取区块数默认值, 允许落后最优节点的块数
CHAIN_CONFIG = {
    'mainnet': {'chain_id': 1,        'batch_size': 5,  'lag_tolerance': 30},
    'sepolia': {'chain_id': 11155111, 'batch_size': 10, 'lag_tolerance': 30},
    'bsc':     {'chain_id': 56,       'batch_size': 5,  'lag_tolerance': 300},
    'op':      {'chain_id': 10,       'batch_size': 20, 'lag_tolerance': 100},
    'arb':     {'chain_id': 42161,    'batch_size': 30, 'lag_tolerance': 1000},
    'base':    {'chain_id': 8453,     'batch_size': 15, 'lag_tolerance': 100},
    'bera':    {'chain_id': 80094,    'batch_size': 20, 'lag_tolerance': 100},
    'gnosis':  {'chain_id': 100,      'batch_size': 10, 'lag_tolerance': 60},
    'ink':     {'chain_id': 57073,    'batch_size': 20, 'lag_tolerance': 200},
    'uni':     {'chain_id': 130,      'batch_size': 20, 'lag_tolerance': 200},
    'scroll':  {'chain_id': 534352,   'batch_size': 10, 'lag_tolerance': 80},
}

# 已证实有问题的端点, 按 URL 子串匹配直接从候选里剔除
BLOCKLIST = [
    'arbitrum-one.rpc.sentio.xyz',  # type4 交易缺 authorizationList (脏数据)
    'arb-mainnet.g.alchemy.com',    # 公共 demo key, 配额极小, 429 大户
    'arb-one.api.pocket.network',   # 批量请求 500 / 整批返回 null
    'arb1.arbitrum.io',             # 零压力下也对本 IP 批量 429, 与并发无关
]


def log(msg):
    print(f"[rpc_manager] {msg}", file=sys.stderr, flush=True)


def _cache_files():
    """返回 (path, timestamp) 列表, 新的在前"""
    files = []
    pattern = os.path.join(SCRIPT_DIR, f'{CACHE_PREFIX}*.json')
    for path in glob.glob(pattern):
        m = re.match(rf'{CACHE_PREFIX}(\d{{8}}_\d{{6}})\.json$', os.path.basename(path))
        if not m:
            continue
        try:
            ts = time.mktime(time.strptime(m.group(1), '%Y%m%d_%H%M%S'))
        except ValueError:
            continue
        files.append((path, ts))
    files.sort(key=lambda x: x[1], reverse=True)
    return files


def load_chainlist():
    """加载 chainlist 数据: 优先用一周内的本地缓存, 否则重新下载。

    多进程并发时: 写入用临时文件 + os.replace 原子替换, 即使两个进程同时
    下载也只是各自生成一个带自己时间戳的文件, 内容等价, 无损坏风险。
    """
    files = _cache_files()
    now = time.time()

    if files and now - files[0][1] < CACHE_MAX_AGE:
        log(f"Using cached {os.path.basename(files[0][0])} "
            f"(age {(now - files[0][1]) / 86400:.1f} days)")
        with open(files[0][0]) as f:
            return json.load(f)

    log(f"Cache missing or older than 7 days, fetching {CHAINLIST_URL} ...")
    try:
        resp = requests.get(CHAINLIST_URL, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) < 100:
            raise ValueError(f"Unexpected chainlist payload: type={type(data)}")
    except Exception as e:
        log(f"WARNING: failed to fetch chainlist: {e}")
        if files:
            log(f"Falling back to stale cache {os.path.basename(files[0][0])}")
            with open(files[0][0]) as f:
                return json.load(f)
        raise

    fname = f"{CACHE_PREFIX}{time.strftime('%Y%m%d_%H%M%S')}.json"
    final_path = os.path.join(SCRIPT_DIR, fname)
    tmp_path = final_path + f'.tmp{os.getpid()}'
    try:
        with open(tmp_path, 'w') as f:
            json.dump(data, f)
        os.replace(tmp_path, final_path)
        log(f"Saved cache {fname}")
        # 清理旧缓存文件
        for path, _ in _cache_files():
            if path != final_path:
                try:
                    os.remove(path)
                except OSError:
                    pass
    except Exception as e:
        log(f"WARNING: failed to save cache: {e}")

    return data


def get_candidate_urls(name):
    """从 chainlist 数据里取指定链的 https 候选端点"""
    if name not in CHAIN_CONFIG:
        raise ValueError(f"Unknown chain name: {name}, known: {list(CHAIN_CONFIG)}")
    chain_id = CHAIN_CONFIG[name]['chain_id']

    data = load_chainlist()
    entry = next((c for c in data if c.get('chainId') == chain_id), None)
    if entry is None:
        raise ValueError(f"chainId {chain_id} not found in chainlist data")

    urls = []
    for rpc in entry.get('rpc', []):
        url = rpc['url'] if isinstance(rpc, dict) else rpc
        if not isinstance(url, str) or not url.startswith('https://'):
            continue
        if '${' in url or ' ' in url:  # 带占位符的跳过
            continue
        if any(bad in url for bad in BLOCKLIST):
            continue
        if url not in urls:
            urls.append(url)
    log(f"{name}: {len(urls)} https candidates from chainlist")
    return urls


def probe_endpoint(url, chain_id, require_batch=False, timeout=8, batch_test_size=2):
    """探测单个端点。

    返回 (ok, height)。require_batch=True 时按 batch_test_size 发一次真实
    大小的 JSON-RPC 批量请求试压: 部分公共节点小批量能过、大批量直接 500,
    这里用该链实际会用的批大小提前把它们过滤掉。
    """
    headers = {'Content-Type': 'application/json'}
    try:
        if require_batch:
            payload = [
                {'jsonrpc': '2.0', 'method': 'eth_chainId', 'params': [], 'id': 1},
                {'jsonrpc': '2.0', 'method': 'eth_blockNumber', 'params': [], 'id': 2},
            ]
            # 用轻量的 getBlockByNumber 把批量撑到实际大小
            for i in range(max(0, batch_test_size - 2)):
                payload.append({'jsonrpc': '2.0', 'method': 'eth_getBlockByNumber',
                                'params': ['latest', False], 'id': 3 + i})
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or len(data) != len(payload):
                return False, 0  # 不支持批量
            results = {item.get('id'): item.get('result') for item in data
                       if isinstance(item, dict)}
            if any(results.get(item['id']) is None for item in payload):
                return False, 0
            if int(results[1], 16) != chain_id:
                return False, 0
            return True, int(results[2], 16)
        else:
            resp = requests.post(url, json={'jsonrpc': '2.0', 'method': 'eth_chainId',
                                            'params': [], 'id': 1},
                                 headers=headers, timeout=timeout)
            resp.raise_for_status()
            result = resp.json().get('result')
            if result is None or int(result, 16) != chain_id:
                return False, 0
            resp = requests.post(url, json={'jsonrpc': '2.0', 'method': 'eth_blockNumber',
                                            'params': [], 'id': 1},
                                 headers=headers, timeout=timeout)
            resp.raise_for_status()
            result = resp.json().get('result')
            if result is None:
                return False, 0
            return True, int(result, 16)
    except Exception:
        return False, 0


def get_alive_endpoints(name, require_batch=False, max_endpoints=None,
                        num_threads=32, timeout=8):
    """返回指定链当前存活 (且不严重落后) 的端点列表"""
    config = CHAIN_CONFIG[name]
    chain_id = config['chain_id']
    lag_tolerance = config['lag_tolerance']

    candidates = get_candidate_urls(name)
    if not candidates:
        return []

    batch_test_size = config['batch_size'] if require_batch else 2
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(
            lambda u: probe_endpoint(u, chain_id, require_batch, timeout,
                                     batch_test_size), candidates))

    alive = [(url, height) for url, (ok, height) in zip(candidates, results) if ok]
    if not alive:
        log(f"{name}: WARNING no alive endpoints out of {len(candidates)} candidates")
        return []

    best_height = max(h for _, h in alive)
    fresh = [url for url, h in alive if best_height - h <= lag_tolerance]
    lagging = len(alive) - len(fresh)
    log(f"{name}: {len(alive)} alive / {len(candidates)} candidates, "
        f"{lagging} lagging dropped, best height {best_height}"
        f"{' (batch verified)' if require_batch else ''}")

    random.shuffle(fresh)  # 打散顺序, 避免多脚本都压在同一批节点上
    if max_endpoints:
        fresh = fresh[:max_endpoints]
    return fresh


def get_batch_size(name):
    """该链批量获取区块的默认批大小"""
    return CHAIN_CONFIG[name]['batch_size']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Probe alive RPC endpoints for a chain')
    parser.add_argument('--name', required=True, choices=sorted(CHAIN_CONFIG.keys()))
    parser.add_argument('--require_batch', action='store_true',
                        help='Only keep endpoints that support JSON-RPC batch requests')
    parser.add_argument('--max', type=int, default=None, help='Max endpoints to output')
    parser.add_argument('--timeout', type=int, default=8, help='Probe timeout seconds')
    args = parser.parse_args()

    endpoints = get_alive_endpoints(args.name, require_batch=args.require_batch,
                                    max_endpoints=args.max, timeout=args.timeout)
    for url in endpoints:
        print(url)
    if not endpoints:
        sys.exit(1)
