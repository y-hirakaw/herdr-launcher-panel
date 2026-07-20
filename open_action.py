#!/usr/bin/env python3
"""Herdr plugin action: open the launcher pane at the right edge of the
current tab, sized to roughly a constant fraction of the tab's total width.

The launcher pane is split off from whichever pane is currently the tab's
rightmost one (by `pane layout` geometry), not the focused pane — so it
always lands at the right edge, even when a different pane was focused when
the action ran. `pane split` always starts at a 50/50 ratio of *that source
pane's* own width, not the whole tab, so how much resize is needed
afterward depends on how wide the source pane already was: the more panes
already open, the narrower it tends to be, and a fixed resize amount would
leave the launcher pane far smaller than intended. The amount is instead
computed from the source pane's pre-split width and the tab's total width,
so the launcher pane ends up close to TARGET_WIDTH_FRACTION of the tab
regardless of how many panes were already there.

The resize targets that same source pane (not the launcher pane itself).
herdr's `pane resize --direction right` adjusts whichever split sits
immediately to the target pane's right, falling back to its left split only
if there is no right neighbor; the source pane always has the launcher pane
as its right neighbor right after the split, so resizing it is stable
regardless of layout. Resizing the launcher pane instead only happened to
work when it was the rightmost pane overall — with more panes to its
right, `--direction right` would find and grow the launcher/next-pane split
instead, shrinking an unrelated neighbor."""

import json
import os
import subprocess

HERDR_BIN = os.environ.get("HERDR_BIN_PATH", "herdr")
TARGET_WIDTH_FRACTION = 0.15


def find_resize_target():
    """(pane_id, pane_width, tab_width) for the current tab's rightmost pane
    (by `pane layout` rects) — the pane the launcher will be split off from.
    All three are None if the lookup fails for any reason."""
    try:
        result = subprocess.run(
            [HERDR_BIN, "pane", "layout", "--current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, None, None
    if result.returncode != 0:
        return None, None, None
    try:
        layout = json.loads(result.stdout)["result"]["layout"]
        panes = layout["panes"]
        tab_width = layout["area"]["width"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None, None, None

    best_id, best_width, best_edge = None, None, None
    for pane in panes:
        rect = pane.get("rect") or {}
        x, width, pane_id = rect.get("x"), rect.get("width"), pane.get("pane_id")
        if x is None or width is None or not pane_id:
            continue
        edge = x + width
        if best_edge is None or edge > best_edge:
            best_id, best_width, best_edge = pane_id, width, edge
    return best_id, best_width, tab_width


def main():
    target_pane_id, source_width, tab_width = find_resize_target()
    if not target_pane_id:
        # Layout lookup failed; fall back to the focused pane with the old
        # fixed amount below (right, not necessarily the tab's right edge).
        target_pane_id = os.environ.get("HERDR_PANE_ID")

    open_args = [
        HERDR_BIN,
        "plugin",
        "pane",
        "open",
        "--plugin",
        "launcher-pane",
        "--entrypoint",
        "launcher",
        "--placement",
        "split",
        "--direction",
        "right",
    ]
    if target_pane_id:
        open_args += ["--target-pane", target_pane_id]

    try:
        subprocess.run(open_args, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return

    if not target_pane_id:
        return  # no reliable pane to anchor the resize on, leave the default split

    amount = 0.35
    if source_width and tab_width:
        # split_pane starts the new pane at ratio 0.5 of source_width, not
        # tab_width; solve for the additional ratio that brings the launcher
        # pane down to TARGET_WIDTH_FRACTION of tab_width. Clamped to keep the
        # underlying split ratio (0.5 + amount) inside herdr's 0.1-0.9 range.
        amount = 0.5 - (TARGET_WIDTH_FRACTION * tab_width / source_width)
        amount = max(-0.4, min(0.4, amount))

    subprocess.run(
        [
            HERDR_BIN,
            "pane",
            "resize",
            "--pane",
            target_pane_id,
            "--direction",
            "right",
            "--amount",
            f"{amount:.4f}",
        ],
        capture_output=True,
    )


if __name__ == "__main__":
    main()
