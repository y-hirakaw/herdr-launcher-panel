# herdr-open-panel

A [Herdr](https://herdr.dev) plugin: a docked panel listing "Open in Finder"
and "Open in VS Code (new window)", each nested with every workspace. Click
one to launch it there — no command or keybinding to remember.

## Install

```bash
herdr plugin install y-hirakaw/herdr-open-panel
```

## Open the panel

Bind a key to the `open` action:

```toml
[[keys.command]]
key = "prefix+o"
type = "plugin_action"
command = "open-panel.open"
description = "open Finder/VS Code panel"
```

Avoid `ctrl+alt+<letter>` here if your terminal is Alacritty: it drops the
Alt modifier when combined with Ctrl, so Herdr never sees it as anything
but plain `ctrl+<letter>`. A plain `prefix+<key>` binding sidesteps this
entirely, since Herdr owns the very next keypress outright.

Calling the action again while the panel is already open opens a second
one rather than focusing the existing pane — known rough edge, not fixed
yet.

## Requirements

- macOS
- Python 3 with `textual` (installed automatically into a bundled `.venv`
  on `herdr plugin install`)
