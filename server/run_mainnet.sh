#!/bin/bash
export NAME="mainnet"
export PORT=9001
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app