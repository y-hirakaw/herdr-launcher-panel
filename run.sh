#!/bin/sh
# Herdr's own pane launcher won't resolve a relative venv path as the
# command to spawn directly; a shell in between resolves it fine.
exec .venv/bin/python3 app.py
