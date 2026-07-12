#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向 syncer_server 上报请求统计的公用模块。

get_block_batch.py 内置了同样的上报逻辑 (kind='block'); get_tvl.py /
get_code.py 用本模块, 以 kind='tvl' / 'code' 上报, 面板按 kind 分列展示。

纯内存累计, 后台线程每 30 秒增量上报一次; 上报失败把数字加回去下轮重试。
进程结束前调用 flush() 把尾巴报出去。
"""

import os
import time
import threading
import requests


class StatsReporter:
    def __init__(self, name, kind, stats_url='http://127.0.0.1:5000', interval=30):
        self.name = name
        self.kind = kind
        self.url = stats_url.rstrip('/') if stats_url else ''
        self.interval = interval
        self.lock = threading.Lock()
        # updated: 成功写库的记录数 (对应 block 上报里的 blocks_added)
        self.stats = {'updated': 0, 'success_requests': 0, 'failed_requests': 0}
        self.headers = self._load_token()
        if self.url:
            threading.Thread(target=self._loop, daemon=True).start()

    def _load_token(self):
        try:
            token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'syncer_token.txt')
            with open(token_file) as f:
                token = f.read().strip()
            return {'Authorization': f'Bearer {token}'} if token else {}
        except Exception:
            return {}

    def add(self, updated=0, ok=0, fail=0):
        with self.lock:
            self.stats['updated'] += updated
            self.stats['success_requests'] += ok
            self.stats['failed_requests'] += fail

    def flush(self):
        if not self.url:
            return
        with self.lock:
            snapshot = dict(self.stats)
            for key in self.stats:
                self.stats[key] = 0
        if not any(snapshot.values()):
            return
        # 字段名沿用 report_stats 现有 schema, blocks_added 在 tvl/code 语义下是更新的记录数
        payload = {'kind': self.kind,
                   'blocks_added': snapshot['updated'],
                   'success_requests': snapshot['success_requests'],
                   'failed_requests': snapshot['failed_requests']}
        try:
            requests.post(f'{self.url}/{self.name}/report_stats', json=payload,
                          headers={**self.headers, 'Content-Type': 'application/json'},
                          timeout=5)
        except Exception:
            with self.lock:
                for key in self.stats:
                    self.stats[key] += snapshot[key]

    def _loop(self):
        while True:
            time.sleep(self.interval)
            self.flush()
