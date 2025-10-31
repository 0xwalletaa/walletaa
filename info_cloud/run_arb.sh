#!/bin/bash
export NAME="arb"
export PORT=9011
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app