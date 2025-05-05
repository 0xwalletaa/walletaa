#!/bin/bash
pkill gunicorn
# 创建日志目录
mkdir -p logs
# 启动服务器
echo "启动Gunicorn服务器..."
gunicorn -c gunicorn_config.py server:app 