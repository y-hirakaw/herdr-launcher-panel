# herdr-launcher-panel

A [Herdr](https://herdr.dev) plugin: a docked panel listing every workspace
under "Open in Finder / Explorer" and whatever else you configure — VS Code
ships as the default second entry, but any command works. Click a workspace
to launch it there, no command to remember. No dependencies beyond Python's
standard library.

![Launcher panel example](assets/panel.png)

## Install

```bash
herdr plugin install y-hirakaw/herdr-launcher-panel
```

## Open the panel

Bind a key to the `open` action:

```toml
[[keys.command]]
key = "prefix+o"
type = "plugin_action"
command = "launcher-panel.open"
description = "open Finder/VS Code panel"
```

Calling the action again while the panel is already open opens a second
one rather than focusing the existing pane — known rough edge, not fixed
yet.

## Customize the menu

"Open in Finder/Explorer/File Manager" is fixed (there's only ever one per
OS). Everything else comes from `menu.json` in the plugin's config directory
(`herdr plugin config-dir launcher-panel`), seeded with a VS Code entry the
first time the panel runs. Edit or replace it freely:

```json
[
  {"title": "💻 Open in VS Code (new window)", "command": ["code", "-n", "{cwd}"]},
  {"title": "🌐 Open in Browser", "command": ["open", "-a", "Google Chrome", "{cwd}"]}
]
```

Each `command` is an argv list, not a shell string — no quoting needed, and
each element is passed through exactly as one argument (so `"Google Chrome"`
stays one argument, spaces and all). `{cwd}` is replaced with the
workspace's directory at click time. Changes take effect within a few
seconds, no reload needed. An invalid file falls back to the VS Code default
and shows why at the top of the panel.

## Requirements

- Python 3 (preinstalled on macOS; on Windows, needs `python3` on `PATH` —
  true for the Microsoft Store distribution, not guaranteed for every
  python.org install)
- macOS, Linux, and Windows are all declared, but only macOS has been
  actually run and clicked through. Windows in particular is untested:
  mouse support through `windows-curses` may behave differently on
  Windows Terminal / conhost than it does on a Unix pty.
