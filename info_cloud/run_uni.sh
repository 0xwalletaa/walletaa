#!/bin/bash
export NAME="uni"
export PORT=9007
gunicorn -c gunicorn_config_sqlite.py server_sqlite:app