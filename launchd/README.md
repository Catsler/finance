# launchd templates (macOS)

These are **templates** for running the MVP system on macOS via `launchd`.

Copy the `.plist` files into `~/Library/LaunchAgents/`, then `launchctl load -w ...`.

Paths are pinned to this repo location:
- `/Users/elie/Downloads/Stock`
- Python interpreter: `/Users/elie/Downloads/Stock/venv/bin/python`

## Install

```bash
mkdir -p ~/Library/LaunchAgents
cp launchd/com.stock.paper.server.plist ~/Library/LaunchAgents/
cp launchd/com.stock.kdj.scan.plist ~/Library/LaunchAgents/
cp launchd/com.stock.kdj.execute.plist ~/Library/LaunchAgents/

launchctl load -w ~/Library/LaunchAgents/com.stock.paper.server.plist
launchctl load -w ~/Library/LaunchAgents/com.stock.kdj.scan.plist
# Week2+: uncomment "Disabled" in execute plist or load it when ready:
# launchctl load -w ~/Library/LaunchAgents/com.stock.kdj.execute.plist
```

## Check status

```bash
launchctl list | rg "com\\.stock\\."
tail -n 200 results/launchd_paper_server.err.log
tail -n 200 results/launchd_kdj_scan.err.log
tail -n 200 results/launchd_kdj_execute.err.log
```

