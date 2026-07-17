#!/usr/bin/env python3
"""Herdr plugin pane: click a workspace under "Open in Finder" or "Open in
VS Code" to launch it there. No keybinding or command to remember."""

import json
import os
import subprocess

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Tree

HERDR_BIN = os.environ.get("HERDR_BIN_PATH", "herdr")
REFRESH_SECONDS = 3.0

def open_in_finder(cwd):
    subprocess.run(["open", cwd])


def open_in_vscode(cwd):
    """Prefer the `code` CLI shim (supports -n for a new window); fall back
    to launching the app bundle directly if that shim isn't on PATH."""
    try:
        subprocess.run(["code", "-n", cwd], check=True)
    except (OSError, subprocess.CalledProcessError):
        subprocess.run(["open", "-na", "Visual Studio Code", "--args", cwd])


ACTIONS = {
    "finder": ("📁 Open in Finder", open_in_finder),
    "vscode": ("💻 Open in VS Code (new window)", open_in_vscode),
}


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


class OpenPanelApp(App):
    CSS = """
    Tree {
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Tree("Open", id="tree")

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        tree.show_root = False
        tree.guide_depth = 2
        self.refresh_tree()
        self.set_interval(REFRESH_SECONDS, self.refresh_tree)

    def refresh_tree(self) -> None:
        try:
            self._refresh_tree()
        except Exception:
            # Runs on a timer; a bad refresh should never take the panel down.
            pass

    def _refresh_tree(self) -> None:
        tree = self.query_one(Tree)
        workspaces = sorted(list_workspaces(), key=lambda w: w.get("number", 0))
        panes = list_panes()

        expanded_categories = {
            node.data["action"]
            for node in tree.root.children
            if node.data and node.is_expanded
        } or set(ACTIONS)  # first run: expand everything

        tree.root.remove_children()
        for action, (label, _fn) in ACTIONS.items():
            category = tree.root.add(label, data={"kind": "category", "action": action})
            if action in expanded_categories:
                category.expand()
            for workspace in workspaces:
                workspace_id = workspace["workspace_id"]
                cwd = workspace_cwd(workspace_id, panes)
                display = workspace.get("label", workspace_id)
                text = Text(display)
                if workspace.get("focused"):
                    text = Text(f"● {display}", style="bold")
                category.add_leaf(
                    text, data={"kind": "workspace", "action": action, "cwd": cwd}
                )

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data
        if not data or data.get("kind") != "workspace":
            return
        cwd = data.get("cwd")
        if not cwd:
            return
        _label, action_fn = ACTIONS[data["action"]]
        try:
            action_fn(cwd)
        except Exception:
            # A launch failure should never take the whole panel down.
            pass


if __name__ == "__main__":
    OpenPanelApp().run()
