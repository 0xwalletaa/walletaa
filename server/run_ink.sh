#!/bin/bash
export NAME="ink"
export PORT=9010
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app