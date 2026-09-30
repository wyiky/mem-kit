# Native Windows memory bridge

This directory contains a Windows-native Claude Code ↔ Codex bridge based on mem-kit. The original `mem` remains the macOS/Linux CLI. The Windows bridge reads existing local files in place; it does not copy, redact, or modify either agent's memory.

## Install

Requirements: Windows, Python 3.8+ on `PATH`. `ripgrep` is optional and speeds up searches through large session logs.

From a clone of this repository, run in PowerShell:

```powershell
$memBin = Join-Path $HOME 'bin'
New-Item -ItemType Directory -Force -Path $memBin | Out-Null
Copy-Item .\windows\mem.py (Join-Path $memBin 'mem.py')
Copy-Item .\windows\mem.cmd (Join-Path $memBin 'mem.cmd')
Copy-Item .\windows\mem (Join-Path $memBin 'mem')
```

Add `$memBin` to your **user PATH** if it is not already present, then open a new terminal. The `mem.cmd` shim works in PowerShell and the extensionless `mem` shim works in Git Bash. Run `mem --version` to verify it resolves.

Choose which agents share memory, preview the instruction and permission changes, then apply them:

```powershell
mem init --agents claude,codex
mem map
mem install
mem install --apply
```

You can select just `claude` or just `codex` and rerun `mem init` later to change the list. The bridge will not search an agent that you did not select.

`install` creates or updates `%USERPROFILE%\.codex\AGENTS.md`, `%USERPROFILE%\.claude\CLAUDE.md`, and Claude's global `settings.json` command allowance. It preserves existing instructions and settings. The block is marked `mem-windows:begin/end`, so rerunning it replaces rather than duplicates the block. Restart open agent sessions afterward. If your Claude launch intentionally omits user-level settings or instructions, add the same block to that project's local instructions and allow the `mem` command in its local settings.

## Use

```powershell
mem map
mem search "rollback plan"
mem search "rollback plan" --agent codex
mem search "rollback plan" --files-only
mem search "rollback plan" --sessions-only
mem recent --days 7
mem show "C:\path\from\search\MEMORY.md" --section "Heading"
```

Search is case-insensitive literal matching. Multiple terms mean **any** term. Default limits are 24 matching lines per source and 2 per file; increase them with `--max-hits` and `--per-file`. `--sessions-only` searches locally retained Claude and Codex JSONL transcripts; `--deep` includes them alongside saved memory.

Claude Code project auto-memory under `~/.claude/projects/*/memory` and Markdown in `~/.codex/memories` are discovered on every run. For any additional project, run:

```powershell
mem add-project "D:\path\to\project"
mem projects
mem search "project keyword" --agent project --files-only
```

Registered projects contribute `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, `MEMORY.md`, and Markdown under `memory`, `memories`, `.memory`, or `rules` directories. New matching files become visible on the next search. `mem remove-project "D:\path\to\project"` unregisters a project without deleting its files. The agent selection and project registrations live in `mem-config.json` beside the installed script.

## Boundaries

The bridge never contacts a server, but search results read by an AI agent enter that agent's model context. It does not filter passwords in enrolled memory or project files. It cannot retrieve conversations that were never saved locally or files removed by an agent's retention policy. Automatic lookup rules improve the chance an agent checks memory; you can explicitly ask it to run `mem search` if needed.

To uninstall, remove the installed `mem.py`, `mem.cmd`, `mem` shim, and `mem-config.json`; remove the `mem-windows:begin/end` blocks from the two global instruction files and the `Bash(mem:*)` / `Bash(mem.cmd:*)` entries from Claude settings. Original memory files are untouched.
