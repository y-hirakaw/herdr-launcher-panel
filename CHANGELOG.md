# Changelog

## 0.3.0

- Workspaces with tabs/panes open on different directories now expand into
  one row per directory (tagged with the tab it belongs to) instead of a
  single row with an ambiguous target.
- The panel's own pane no longer shows up as a bogus nested entry under the
  workspace it's docked in.
- The currently-focused workspace is highlighted instead of marked with a
  symbol, freeing up label width.
- The panel now always opens at the right edge of the current tab (it used
  to split whichever pane was focused, which could land it in the middle of
  an existing layout) and sizes itself to roughly a constant fraction of the
  tab's width regardless of how many panes are already open.

## 0.1.0

Initial release: click-to-launch Finder/Explorer/VS Code panel, nested by
workspace, with a configurable `menu.json` and first-run confirmation per
command.
