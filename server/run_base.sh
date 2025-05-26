#!/bin/bash
export NAME="base"
export PORT=9005
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app