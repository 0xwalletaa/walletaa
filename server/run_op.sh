#!/bin/bash
export NAME="op"
export PORT=9004
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app