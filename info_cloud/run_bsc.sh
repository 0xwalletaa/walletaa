#!/bin/bash
export NAME="bsc"
export PORT=9003
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app