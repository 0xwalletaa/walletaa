#!/bin/bash
export NAME="sepolia"
export PORT=9002
gunicorn -c gunicorn_config.py server:app