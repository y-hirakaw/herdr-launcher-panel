#!/bin/sh
exec "${HERDR_BIN_PATH:-herdr}" plugin pane open \
  --plugin open-panel --entrypoint open-panel \
  --placement split --direction right
