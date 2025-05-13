#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gunicorn配置文件
适用于生产环境部署
"""

import multiprocessing
import os
import sys
import threading
import argparse

PORT = os.environ.get("PORT")
NAME = os.environ.get("NAME")

# 绑定的IP和端口
bind = f"0.0.0.0:{PORT}"

log_dir = f"logs_{NAME}"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 工作模式
worker_class = "sync"

# 并发工作进程数，通常设置为 (2 x $num_cores) + 1
# 也可以根据内存需求适当调整
workers = 4 #  multiprocessing.cpu_count() * 2 + 1

# 每个工作进程的线程数
threads = 2

# 最大客户端并发数
worker_connections = 1000

# 超时时间（秒）
timeout = 60

# 最大请求数，超过后工作进程会重启
max_requests = 2000
max_requests_jitter = 200

# 预加载应用以减少启动时间
preload_app = True

# 后台运行
daemon = False

# 访问日志
accesslog = f"{log_dir}/gunicorn_access.log"
access_log_format = '%({X-Real-IP}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 错误日志
errorlog = f"{log_dir}/gunicorn_error.log"
loglevel = "info"

# 进程ID文件
pidfile = f"{log_dir}/gunicorn.pid"

# 启动前和关闭后的钩子函数
def on_starting(server):
    server.log.info("Gunicorn服务器正在启动...")

def on_exit(server):
    server.log.info("Gunicorn服务器正在关闭...")

# worker进程的钩子函数
def post_fork(server, worker):
    """
    每个worker进程启动后的钩子函数，确保每个worker都启动自己的更新线程
    """
    server.log.info(f"Worker {worker.pid} 正在启动更新线程...")
    from server import update_data
    
    # 在每个worker进程中启动独立的更新线程
    worker_update_thread = threading.Thread(target=update_data, daemon=True)
    worker_update_thread.start()
    server.log.info(f"Worker {worker.pid} 更新线程已启动") 