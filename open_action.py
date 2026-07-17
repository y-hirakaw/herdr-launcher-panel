#!/usr/bin/env python3
"""Herdr plugin action: open the panel pane, then shrink it down from the
default 50/50 split to roughly a 15% wide sidebar."""

import json
import os
import subprocess

HERDR_BIN = os.environ.get("HERDR_BIN_PATH", "herdr")


def main():
    try:
        result = subprocess.run(
            [
                HERDR_BIN,
                "plugin",
                "pane",
                "open",
                "--plugin",
                "launcher-panel",
                "--entrypoint",
                "launcher",
                "--placement",
                "split",
                "--direction",
                "right",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return

    try:
        pane_id = json.loads(result.stdout)["result"]["plugin_pane"]["pane"]["pane_id"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return

    subprocess.run(
        [
            HERDR_BIN,
            "pane",
            "resize",
            "--pane",
            pane_id,
            "--direction",
            "right",
            "--amount",
            "0.35",
        ],
        capture_output=True,
    )


if __name__ == "__main__":
    main()
