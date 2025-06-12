#!/bin/bash
export NAME="bera"
export PORT=9006
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app