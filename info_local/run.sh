#!/bin/bash
export NAME="mainnet"
export PORT=9001
gunicorn -c gunicorn_config_mysql.py server_mysql:app