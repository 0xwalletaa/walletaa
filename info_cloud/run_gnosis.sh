#!/bin/bash
export NAME="gnosis"
export PORT=9008
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app