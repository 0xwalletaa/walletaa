#!/bin/bash
export NAME="sepolia"
export PORT=8082
gunicorn -c gunicorn_config.py server:app