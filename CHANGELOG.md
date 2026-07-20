# Changelog

## 0.4.0

Renamed from `herdr-launcher-panel` (plugin id `launcher-panel`) to
`herdr-launcher-pane` (plugin id `launcher-pane`), to match Herdr's own
terminology — the plugin has no "panel" concept, only workspaces, tabs, and
panes, and this launcher is itself just a pane. Repo, plugin id and name,
install command, and keybinding command string (`launcher-pane.open`) all
changed accordingly.

If you already have this installed: update your keybinding's `command` to
`launcher-pane.open`, reinstall/relink under the new id, and copy
`menu.json` (and `confirmed_commands.json`, if you want confirmations to
carry over) from the old config directory to the new one —
`herdr plugin config-dir launcher-pane` prints the new path.

## 0.3.0

- Workspaces with tabs/panes open on different directories now expand into
  one row per directory (tagged with the tab it belongs to) instead of a
  single row with an ambiguous target.
- The launcher's own pane no longer shows up as a bogus nested entry under
  the workspace it's docked in.
- The currently-focused workspace is highlighted instead of marked with a
  symbol, freeing up label width.
- The launcher now always opens at the right edge of the current tab (it
  used to split whichever pane was focused, which could land it in the
  middle of an existing layout) and sizes itself to roughly a constant
  fraction of the tab's width regardless of how many panes are already open.
- The hover path line now collapses the home directory to `~` and spans two
  lines, bottom-aligned, instead of always sitting one row up and cutting
  off the end of deep paths.

## 0.1.0

Initial release: click-to-launch Finder/Explorer/VS Code launcher, nested by
workspace, with a configurable `menu.json` and first-run confirmation per
command.
