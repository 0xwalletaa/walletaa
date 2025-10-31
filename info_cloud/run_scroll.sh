#!/bin/bash
export NAME="scroll"
export PORT=9009
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app