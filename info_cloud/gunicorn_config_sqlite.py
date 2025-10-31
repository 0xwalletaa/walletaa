#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gunicorn configuration file
For production environment deployment
"""

import multiprocessing
import os
import sys
import threading
import argparse

PORT = os.environ.get("PORT")
NAME = os.environ.get("NAME")

# Bind IP and port
bind = f"0.0.0.0:{PORT}"

log_dir = f"logs_{NAME}"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Working mode
worker_class = "sync"

# Number of concurrent worker processes, usually set to (2 x $num_cores) + 1
# Can also be adjusted according to memory requirements
workers = 2 #  multiprocessing.cpu_count() * 2 + 1

# Number of threads per worker process
threads = 2

# Maximum client concurrency
worker_connections = 1000

# Timeout (seconds)
timeout = 60

# Maximum number of requests, worker process will restart after exceeding
max_requests = 2000
max_requests_jitter = 200

# Preload application to reduce startup time
preload_app = True

# Run in background
daemon = False

# Access log
accesslog = f"{log_dir}/gunicorn_access.log"
access_log_format = '%({X-Real-IP}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Error log
errorlog = f"{log_dir}/gunicorn_error.log"
loglevel = "info"

# Process ID file
pidfile = f"{log_dir}/gunicorn.pid"

# Hook functions before startup and after shutdown
def on_starting(server):
    server.log.info("Gunicorn server is starting...")

def on_exit(server):
    server.log.info("Gunicorn server is shutting down...")
