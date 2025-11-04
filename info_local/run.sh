#!/bin/bash
# 定义允许访问的链名称列表（用逗号分隔）
export ALLOWED_NAMES="mainnet,bsc,op,arb,base,bera,gnosis,ink,uni,scroll"
export PORT=3000
gunicorn -c gunicorn_config_mysql.py server_mysql:app