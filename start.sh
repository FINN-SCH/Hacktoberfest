#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
exec /home/jonathan/assistant/.venv/bin/python server.py
