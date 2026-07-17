#!/usr/bin/env python3
"""Herdr plugin pane: click a workspace under a configurable menu (default:
"Open in Finder" / "Open in VS Code") to run a command against it there. No
external dependencies (stdlib curses)."""

import curses
import json
import os
import platform
import subprocess

HERDR_BIN = os.environ.get("HERDR_BIN_PATH", "herdr")
REFRESH_MS = 3000

# Seeded into menu.json the first time the panel runs, if that file doesn't
# exist yet — a starting point the user can edit or delete from then on.
SEED_MENU = [
    {"title": "💻 Open in VS Code (new window)", "command": ["code", "-n", "{cwd}"]},
]


def builtin_open_entry():
    """Open in the OS file browser. Fixed, not user-configurable: every
    platform has exactly one, so there's nothing to choose between."""
    system = platform.system()
    if system == "Darwin":
        return {"title": "📁 Open in Finder", "command": ["open", "{cwd}"]}
    if system == "Windows":
        return {"title": "📁 Open in Explorer", "command": ["explorer", "{cwd}"]}
    return {"title": "📁 Open in File Manager", "command": ["xdg-open", "{cwd}"]}


def seed_menu_file(path):
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(SEED_MENU, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except OSError:
        pass


def valid_entries(menu):
    return [
        entry
        for entry in menu
        if isinstance(entry, dict)
        and isinstance(entry.get("title"), str)
        and isinstance(entry.get("command"), list)
        and entry["command"]
        and all(isinstance(part, str) for part in entry["command"])
    ]


def load_menu():
    """User-configurable entries only; see `builtin_open_entry` for the
    fixed Finder/Explorer/File Manager entry prepended in build_rows.

    Returns (entries, error_message). error_message is None unless
    menu.json exists but couldn't be used, in which case entries falls
    back to SEED_MENU and error_message explains why.
    """
    config_dir = os.environ.get("HERDR_PLUGIN_CONFIG_DIR")
    if not config_dir:
        return SEED_MENU, None
    path = os.path.join(config_dir, "menu.json")
    if not os.path.isfile(path):
        seed_menu_file(path)
        return SEED_MENU, None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as err:
        return SEED_MENU, f"menu.json unreadable ({err.strerror or err}), using defaults"
    try:
        menu = json.loads(raw)
    except json.JSONDecodeError as err:
        return SEED_MENU, f"menu.json is invalid JSON (line {err.lineno}: {err.msg}), using defaults"
    if not isinstance(menu, list):
        return SEED_MENU, "menu.json must be a JSON array at the top level, using defaults"
    entries = valid_entries(menu)
    if not entries:
        return SEED_MENU, "menu.json has no valid entries (need title + command), using defaults"
    return entries, None


def herdr_json(*args):
    try:
        result = subprocess.run(
            [HERDR_BIN, *args], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def list_workspaces():
    response = herdr_json("workspace", "list")
    if not response:
        return []
    return response.get("result", {}).get("workspaces", [])


def list_panes():
    response = herdr_json("pane", "list")
    if not response:
        return []
    return response.get("result", {}).get("panes", [])


def workspace_cwd(workspace_id, panes):
    """Herdr's workspace list doesn't expose a cwd directly; use the first
    pane belonging to that workspace as a stand-in."""
    for pane in panes:
        if pane.get("workspace_id") == workspace_id and pane.get("cwd"):
            return pane["cwd"]
    return None


CARD_WIDTH = 32


def build_rows():
    """Flat list of (label, values, command_template). values/command_template
    are None for section headers, borders, and blank spacer rows, which
    aren't clickable. values is {"cwd": ..., "workspace_id": ...} otherwise —
    both are available as {cwd}/{workspace_id} placeholders in commands."""
    workspaces = sorted(list_workspaces(), key=lambda w: w.get("number", 0))
    panes = list_panes()
    rows = []
    menu, error = load_menu()
    if error:
        rows.append((f"⚠ {error}", None, None))
        rows.append(("", None, None))
    for entry in [builtin_open_entry(), *menu]:
        header = f"╭─ {entry['title']} "
        header += "─" * max(CARD_WIDTH - len(header), 0)
        rows.append((header, None, None))
        for workspace in workspaces:
            workspace_id = workspace["workspace_id"]
            cwd = workspace_cwd(workspace_id, panes)
            label = workspace.get("label", workspace_id)
            marker = "● " if workspace.get("focused") else "  "
            values = {"cwd": cwd, "workspace_id": workspace_id}
            rows.append((f"│  {marker}{label}", values, entry["command"]))
        rows.append(("╰" + "─" * (CARD_WIDTH - 1), None, None))
        rows.append(("", None, None))
    return rows


CONFIRMED_FILE = "confirmed_commands.json"


def command_key(command_template):
    """Stable identity for a menu entry's command, independent of which
    workspace was clicked (before {cwd}/{workspace_id} substitution)."""
    return json.dumps(command_template)


def load_confirmed(config_dir):
    if not config_dir:
        return set()
    try:
        with open(
            os.path.join(config_dir, CONFIRMED_FILE), "r", encoding="utf-8"
        ) as handle:
            return set(json.load(handle))
    except (OSError, json.JSONDecodeError, TypeError):
        return set()


def record_confirmed(config_dir, key):
    if not config_dir:
        return
    confirmed = load_confirmed(config_dir)
    confirmed.add(key)
    try:
        with open(
            os.path.join(config_dir, CONFIRMED_FILE), "w", encoding="utf-8"
        ) as handle:
            json.dump(sorted(confirmed), handle)
    except OSError:
        pass


def show_run_confirm_prompt(stdscr, command):
    """Shown the first time a specific menu command is about to run. Returns
    False if the user cancelled instead of confirming."""
    stdscr.erase()
    stdscr.keypad(True)
    stdscr.nodelay(False)
    stdscr.timeout(-1)
    try:
        for i, line in enumerate(
            [
                "First time running this command:",
                "",
                "  " + " ".join(command),
                "",
                "Enter to run it (won't ask again for this exact command),",
                "q to cancel.",
            ]
        ):
            stdscr.addnstr(i, 0, line, max(stdscr.getmaxyx()[1] - 1, 0))
        stdscr.refresh()
        while True:
            key = stdscr.getch()
            if key in (10, 13, curses.KEY_ENTER):
                return True
            if key in (ord("q"), 27):
                return False
    finally:
        stdscr.timeout(REFRESH_MS)


def run_action(stdscr, config_dir, rows, index):
    if not 0 <= index < len(rows):
        return
    _label, values, command_template = rows[index]
    if not values or not command_template:
        return
    cwd = values.get("cwd")
    workspace_id = values.get("workspace_id")
    if cwd is None and any("{cwd}" in part for part in command_template):
        return  # command needs a cwd we couldn't resolve
    command = [
        part.replace("{cwd}", cwd or "").replace("{workspace_id}", workspace_id or "")
        for part in command_template
    ]

    key = command_key(command_template)
    if key not in load_confirmed(config_dir):
        if not show_run_confirm_prompt(stdscr, command):
            return
        record_confirmed(config_dir, key)

    try:
        subprocess.run(command)
    except Exception:
        pass  # a launch failure should never take the panel down


def main(stdscr):
    curses.curs_set(0)
    config_dir = os.environ.get("HERDR_PLUGIN_CONFIG_DIR")

    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    print("\033[?1003h")  # ncurses' mousemask doesn't always push this itself
    stdscr.timeout(REFRESH_MS)
    stdscr.keypad(True)

    rows = build_rows()
    selected = next((i for i, r in enumerate(rows) if r[2]), 0)
    hovered = None

    try:
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            for i, (label, _values, action_fn) in enumerate(rows):
                if i >= height:
                    break
                if action_fn and i == hovered:
                    attr = curses.A_REVERSE
                elif action_fn and i == selected:
                    attr = curses.A_BOLD
                else:
                    attr = curses.A_NORMAL
                stdscr.addnstr(i, 0, label[: max(width - 1, 0)], max(width - 1, 0), attr)
            stdscr.refresh()

            key = stdscr.getch()

            if key == -1:  # timeout: nothing pressed, just refresh the data
                rows = build_rows()
                continue

            if key == curses.KEY_RESIZE:
                continue

            if key == curses.KEY_MOUSE:
                try:
                    _id, _x, y, _z, bstate = curses.getmouse()
                except curses.error:
                    continue
                clickable = 0 <= y < len(rows) and rows[y][2] is not None
                hovered = y if clickable else None
                if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                    run_action(stdscr, config_dir, rows, y)
                continue

            if key == curses.KEY_UP:
                selected = max(0, selected - 1)
            elif key == curses.KEY_DOWN:
                selected = min(len(rows) - 1, selected + 1)
            elif key in (10, 13, curses.KEY_ENTER):
                run_action(stdscr, config_dir, rows, selected)
    finally:
        print("\033[?1003l")  # stop reporting mouse motion on the way out


if __name__ == "__main__":
    curses.wrapper(main)
