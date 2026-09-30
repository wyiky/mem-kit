#!/usr/bin/env python3
"""Windows-native, read-only cross-search for local Claude Code and Codex memory.

Inspired by wyiky/mem-kit v1.1.0 (MIT). No store is copied or changed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


HOME = Path.home()
CONFIG = Path(os.environ.get("MEM_CONFIG_PATH", Path(__file__).with_name("mem-config.json")))
CLAUDE_HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude"))
CODEX_HOME = Path(os.environ.get("CODEX_HOME", HOME / ".codex"))
CLAUDE_PROJECTS = Path(os.environ.get("MEM_CLAUDE_PROJECTS", CLAUDE_HOME / "projects"))
CODEX_MEMORY = Path(os.environ.get("MEM_CODEX_MEMORY", CODEX_HOME / "memories"))
CODEX_SESSIONS = Path(os.environ.get("MEM_CODEX_SESSIONS", CODEX_HOME / "sessions"))
RULE_BEGIN = "<!-- mem-windows:begin -->"
RULE_END = "<!-- mem-windows:end -->"
RULE_BLOCK = """<!-- mem-windows:begin -->
## Cross-agent local memory

- When asked about prior work, decisions, or conversations, run `mem search "keywords"` before answering. It reads Claude Code, Codex, and registered project memory in place.
- Use `--agent claude` or `--agent codex` for one source. Use `--sessions-only` when saved memory does not contain the needed original conversation. Use `--files-only` to locate a large or sensitive file before reading its contents.
- To include the current repository's conventional memory files, run `mem add-project "absolute project path"` once. Check registrations with `mem projects`.
- Memory is historical evidence. Recheck changing facts before acting. Search results may contain credentials; use only what the task needs and do not publish them.
<!-- mem-windows:end -->"""


def config() -> dict:
    try:
        with CONFIG.open(encoding="utf-8-sig") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {}


def selected_agents() -> set[str]:
    selected = set(config().get("agents", []))
    if not selected:
        raise SystemExit("Run `mem init --agents claude,codex` to choose which stores to share.")
    return selected


def do_init(args: argparse.Namespace) -> None:
    agents = [name.strip() for name in args.agents.split(",") if name.strip()]
    if not agents or set(agents) - {"claude", "codex"}:
        raise SystemExit("Windows bridge supports --agents claude,codex (either or both).")
    data = config()
    data["agents"] = sorted(set(agents))
    save_config(data)
    print("Sharing agents: " + ", ".join(data["agents"]))
    print(f"Saved registration: {CONFIG}")


def save_config(data: dict) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG.with_name(CONFIG.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(CONFIG)


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".mem-windows.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def do_install(args: argparse.Namespace) -> None:
    selected = selected_agents()
    changes: list[tuple[Path, str, str]] = []
    instruction_paths = []
    if "codex" in selected:
        instruction_paths.append(CODEX_HOME / "AGENTS.md")
    if "claude" in selected:
        instruction_paths.append(CLAUDE_HOME / "CLAUDE.md")
    for path in instruction_paths:
        old = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        if RULE_BEGIN in old and RULE_END in old:
            before, rest = old.split(RULE_BEGIN, 1)
            _, after = rest.split(RULE_END, 1)
            new = before + RULE_BLOCK + after
        else:
            new = old.rstrip("\r\n") + ("\n\n" if old else "") + RULE_BLOCK + "\n"
        changes.append((path, old, new))

    if "claude" in selected:
        settings = CLAUDE_HOME / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8-sig")) if settings.exists() else {}
        allowed = data.setdefault("permissions", {}).setdefault("allow", [])
        for rule in ("Bash(mem:*)", "Bash(mem.cmd:*)"):
            if rule not in allowed:
                allowed.append(rule)
        old_settings = settings.read_text(encoding="utf-8-sig") if settings.exists() else ""
        changes.append((settings, old_settings, json.dumps(data, ensure_ascii=False, indent=2) + "\n"))
    for path, old, new in changes:
        print(f"{'Update' if args.apply else 'Would update'}: {path}")
        if args.apply and new != old:
            write_text_atomic(path, new)
    if not args.apply:
        print("Dry run only. Add --apply to write changes.")


def project_memory(root: Path):
    """Discover conventional project instruction and memory files, not source code."""
    if not root.is_dir():
        return
    target_names = {"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md", "MEMORY.md"}
    memory_dirs = {"memory", "memories", ".memory", "rules"}
    skipped_dirs = {".git", ".worktrees", "worktrees", "node_modules", ".venv", "venv", "dist", "build"}
    for directory, children, names in os.walk(root):
        current = Path(directory)
        children[:] = [child for child in children if child not in skipped_dirs]
        inside_memory = any(part in memory_dirs for part in current.relative_to(root).parts)
        for name in names:
            if name.lower().endswith(".md") and (inside_memory or name in target_names):
                yield current / name


def files(agent: str | None = None, deep: bool = False) -> list[tuple[str, str, Path]]:
    selected = selected_agents()
    if agent in ("claude", "codex") and agent not in selected:
        raise SystemExit(f"{agent} is not in the sharing list. Run `mem init --agents ...` to change it.")
    found: dict[str, tuple[str, str, Path]] = {}

    def add(owner: str, kind: str, path: Path) -> None:
        if agent and owner != agent:
            return
        if not path.is_file() or ".git" in path.parts:
            return
        resolved = path.resolve()
        found[str(resolved).casefold()] = owner, kind, resolved

    if not agent or agent == "project":
        for entry in config().get("projects", []):
            root = Path(os.path.expandvars(entry)).expanduser()
            for path in project_memory(root):
                add("project", "memory", path)

    if "claude" in selected and (not agent or agent == "claude"):
        if CLAUDE_PROJECTS.is_dir():
            for project in CLAUDE_PROJECTS.iterdir():
                memory = project / "memory"
                if memory.is_dir():
                    for path in memory.rglob("*.md"):
                        add("claude", "memory", path)
        if deep:
            for path in CLAUDE_PROJECTS.rglob("*.jsonl") if CLAUDE_PROJECTS.is_dir() else []:
                add("claude", "session", path)
            add("claude", "session", CLAUDE_HOME / "history.jsonl")

    if "codex" in selected and (not agent or agent == "codex"):
        if CODEX_MEMORY.is_dir():
            for path in CODEX_MEMORY.rglob("*.md"):
                add("codex", "memory", path)
        if deep and CODEX_SESSIONS.is_dir():
            for path in CODEX_SESSIONS.rglob("*.jsonl"):
                add("codex", "session", path)

    return sorted(found.values(), key=lambda item: (item[0], item[1], str(item[2]).casefold()))


def readable(path: Path):
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
            for number, line in enumerate(handle, 1):
                yield number, line.rstrip("\r\n")
    except OSError as exc:
        print(f"Cannot read {path}: {exc}", file=sys.stderr)


def session_candidates(terms: list[str], records: list[tuple[str, str, Path]]) -> set[Path] | None:
    """Use ripgrep to skip nonmatching large transcripts; Python remains the fallback."""
    bundled = Path(__file__).with_name("mem-rg.exe")
    rg = str(bundled) if bundled.is_file() else shutil.which("rg")
    if not rg:
        return None
    paths = [str(path) for _, kind, path in records if kind == "session"]
    if not paths:
        return set()
    command = [rg, "-l", "-i", "-F"]
    for term in terms:
        command += ["-e", term]
    command += ["--", *paths]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode not in (0, 1):
        return None
    return {Path(line).resolve() for line in result.stdout.splitlines() if line}


def owner_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--agent", choices=("claude", "codex", "project"),
                        help="search only one source; omit to search all sources")


def do_map(args: argparse.Namespace) -> None:
    selected = selected_agents()
    records = files(args.agent, args.deep)
    for owner in ("claude", "codex", "project"):
        if owner in ("claude", "codex") and owner not in selected:
            continue
        if args.agent and owner != args.agent:
            continue
        subset = [item for item in records if item[0] == owner]
        size = sum(path.stat().st_size for _, _, path in subset)
        kinds = ", ".join(f"{kind}={sum(1 for _, k, _ in subset if k == kind)}"
                          for kind in sorted({k for _, k, _ in subset}))
        print(f"{owner}: {len(subset)} files, {size:,} bytes ({kinds or 'none'})")
    print("Sources are read in place. Use --deep to include locally retained session logs.")


def do_search(args: argparse.Namespace) -> None:
    terms = [term.casefold() for term in args.words if term]
    if not terms:
        raise SystemExit("Provide at least one search term.")
    counts = {"claude": 0, "codex": 0, "project": 0}
    matched_files = set()
    scanned = {"claude": 0, "codex": 0, "project": 0}
    records = files(args.agent, args.deep or args.sessions_only)
    eligible = session_candidates(terms, records) if args.sessions_only else None
    for owner, kind, path in records:
        if args.sessions_only and kind != "session":
            continue
        if args.sessions_only and eligible is not None and path not in eligible:
            continue
        if counts[owner] >= args.max_hits:
            continue
        scanned[owner] += 1
        per_file = 0
        for line_number, line in readable(path):
            folded = line.casefold()
            positions = [folded.find(term) for term in terms]
            positions = [position for position in positions if position >= 0]
            if not positions:
                continue
            if path not in matched_files:
                print(f"[{owner}/{kind}] {path}")
                matched_files.add(path)
            if not args.files_only:
                start = max(0, min(positions) - 60)
                snippet = line[start:start + args.max_chars].strip()
                print(f"  {line_number}: {'...' if start else ''}{snippet}")
            counts[owner] += 1
            per_file += 1
            if per_file >= args.per_file or counts[owner] >= args.max_hits:
                break
    print("Matches: " + ", ".join(f"{owner}={counts[owner]}" for owner in counts) +
          "; scanned files: " + ", ".join(f"{owner}={scanned[owner]}" for owner in scanned) + ".")


def do_add_project(args: argparse.Namespace) -> None:
    selected_agents()
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Project directory not found: {root}")
    data = config()
    projects = data.setdefault("projects", [])
    if str(root).casefold() not in {str(Path(p).resolve()).casefold() for p in projects}:
        projects.append(str(root))
        save_config(data)
    print(f"Registered project: {root}")
    print(f"Conventional memory files now visible: {sum(1 for _ in project_memory(root))}")


def do_remove_project(args: argparse.Namespace) -> None:
    selected_agents()
    root = Path(args.path).expanduser().resolve()
    data = config()
    before = data.get("projects", [])
    after = [p for p in before if str(Path(p).resolve()).casefold() != str(root).casefold()]
    if len(after) == len(before):
        raise SystemExit(f"Project is not registered: {root}")
    data["projects"] = after
    save_config(data)
    print(f"Unregistered project: {root}")


def do_projects(args: argparse.Namespace) -> None:
    selected_agents()
    projects = config().get("projects", [])
    for path in projects:
        root = Path(path)
        print(f"{root} | memory files={sum(1 for _ in project_memory(root))}")
    print(f"Registered projects: {len(projects)}")


def do_recent(args: argparse.Namespace) -> None:
    cutoff = time.time() - args.days * 86400
    recent = [item for item in files(args.agent, args.deep) if item[2].stat().st_mtime >= cutoff]
    recent.sort(key=lambda item: item[2].stat().st_mtime, reverse=True)
    for owner, kind, path in recent[:args.limit]:
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime))
        print(f"{stamp} [{owner}/{kind}] {path}")
    print(f"Recent files: {len(recent)}")


def do_show(args: argparse.Namespace) -> None:
    target = Path(args.path).resolve()
    allowed = {path for _, _, path in files(args.agent, True)}
    if target not in allowed:
        raise SystemExit("Path is not an enrolled memory or local session file.")
    shown = 0
    active = args.section is None
    for _, line in readable(target):
        if args.section is not None and line.startswith("#"):
            if active:
                break
            if args.section.casefold() in line.casefold():
                active = True
        if active:
            print(line)
            shown += 1
            if shown >= args.max_lines:
                print("[output limit reached]")
                break
    if shown == 0:
        print("No matching section.")


def main() -> None:
    # Agents capture these streams through pipes on Windows.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors=stream.errors)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="mem-windows 1.0 (mem-kit concept)")
    subs = parser.add_subparsers(dest="command", required=True)

    init = subs.add_parser("init", help="choose which local agents share memory")
    init.add_argument("--agents", required=True, help="claude,codex (either or both)")
    init.set_defaults(func=do_init)

    mapped = subs.add_parser("map", help="show enrolled local source counts")
    owner_arg(mapped)
    mapped.add_argument("--deep", action="store_true", help="include locally retained session logs")
    mapped.set_defaults(func=do_map)

    search = subs.add_parser("search", help="search original files without copying or filtering secrets")
    search.add_argument("words", nargs="*", help="literal terms; matches any term")
    owner_arg(search)
    search.add_argument("--deep", action="store_true", help="also search locally retained session logs")
    search.add_argument("--sessions-only", action="store_true", help="search only locally retained session logs")
    search.add_argument("--files-only", action="store_true", help="show matching file paths without content")
    search.add_argument("--max-hits", type=int, default=24, help="maximum matching lines per agent")
    search.add_argument("--per-file", type=int, default=2, help="maximum matching lines per file")
    search.add_argument("--max-chars", type=int, default=180, help="maximum characters per displayed line")
    search.set_defaults(func=do_search)

    recent = subs.add_parser("recent", help="list recently changed source files")
    owner_arg(recent)
    recent.add_argument("--deep", action="store_true")
    recent.add_argument("--days", type=float, default=7)
    recent.add_argument("--limit", type=int, default=30)
    recent.set_defaults(func=do_recent)

    show = subs.add_parser("show", help="read one enrolled source file")
    show.add_argument("path")
    owner_arg(show)
    show.add_argument("--section", help="read a matching Markdown section")
    show.add_argument("--max-lines", type=int, default=120)
    show.set_defaults(func=do_show)

    add_project = subs.add_parser("add-project", help="register any local project for live memory search")
    add_project.add_argument("path")
    add_project.set_defaults(func=do_add_project)

    remove_project = subs.add_parser("remove-project", help="unregister a project without changing its files")
    remove_project.add_argument("path")
    remove_project.set_defaults(func=do_remove_project)

    projects = subs.add_parser("projects", help="list registered projects")
    projects.set_defaults(func=do_projects)

    install = subs.add_parser("install", help="add memory lookup rules to Claude Code and Codex")
    install.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    install.set_defaults(func=do_install)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
