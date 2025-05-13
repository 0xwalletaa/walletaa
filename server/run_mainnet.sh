#!/bin/bash
export NAME="mainnet"
export PORT=3001
gunicorn -c gunicorn_config.py server:app