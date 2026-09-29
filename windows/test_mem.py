"""Isolated tests for the Windows bridge; no real agent data is read."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("mem.py")


class MemoryBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mem windows test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.claude = self.root / "claude"
        self.codex = self.root / "codex"
        self.projects = self.claude / "projects"
        self.memories = self.codex / "memories"
        self.sessions = self.codex / "sessions"
        for path in (self.projects, self.memories, self.sessions):
            path.mkdir(parents=True)
        self.environment = dict(os.environ)
        self.environment.update({
            "CLAUDE_CONFIG_DIR": str(self.claude),
            "CODEX_HOME": str(self.codex),
            "MEM_CLAUDE_PROJECTS": str(self.projects),
            "MEM_CODEX_MEMORY": str(self.memories),
            "MEM_CODEX_SESSIONS": str(self.sessions),
            "MEM_CONFIG_PATH": str(self.root / "config.json"),
        })
        self.run_mem("init", "--agents", "claude,codex")

    def run_mem(self, *arguments: str, success: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, str(SCRIPT), *arguments],
                                env=self.environment, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_memory_and_arbitrary_project_are_read_in_place(self) -> None:
        claude_memory = self.projects / "demo" / "memory"
        claude_memory.mkdir(parents=True)
        (claude_memory / "MEMORY.md").write_text("CLAUDE_MARKER\n", encoding="utf-8")
        (self.memories / "MEMORY.md").write_text("CODEX_MARKER\n", encoding="utf-8")
        project = self.root / "future project"
        project.mkdir()
        (project / "CLAUDE.local.md").write_text("TEST_PASSWORD_DO_NOT_USE\n", encoding="utf-8")

        self.assertIn("CLAUDE_MARKER", self.run_mem("search", "CLAUDE_MARKER", "--agent", "claude").stdout)
        self.assertIn("CODEX_MARKER", self.run_mem("search", "CODEX_MARKER", "--agent", "codex").stdout)
        self.assertNotIn("CLAUDE_MARKER", self.run_mem("search", "CLAUDE_MARKER", "--agent", "codex").stdout)

        self.run_mem("add-project", str(project))
        self.assertIn("TEST_PASSWORD_DO_NOT_USE",
                      self.run_mem("search", "TEST_PASSWORD_DO_NOT_USE", "--agent", "project").stdout)
        note_dir = project / "memory"
        note_dir.mkdir()
        (note_dir / "decision.md").write_text("# Decision\nNEW_NOTE_MARKER\n# Other\nOUTSIDE_SECTION\n",
                                              encoding="utf-8")
        self.assertIn("decision.md", self.run_mem("search", "NEW_NOTE_MARKER", "--files-only").stdout)
        section = self.run_mem("show", str(note_dir / "decision.md"), "--section", "Decision").stdout
        self.assertIn("NEW_NOTE_MARKER", section)
        self.assertNotIn("OUTSIDE_SECTION", section)
        self.run_mem("remove-project", str(project))
        self.assertIn("project=0", self.run_mem("search", "NEW_NOTE_MARKER").stdout)

    def test_sessions_only_searches_raw_transcripts_and_centers_snippet(self) -> None:
        claude_session = self.projects / "demo" / "session.jsonl"
        claude_session.parent.mkdir(parents=True)
        claude_session.write_text("x" * 300 + "CLAUDE_SESSION_MARKER\n", encoding="utf-8")
        (self.sessions / "session.jsonl").write_text("y" * 300 + "CODEX_SESSION_MARKER\n", encoding="utf-8")
        (self.memories / "MEMORY.md").write_text("CODEX_SESSION_MARKER\n", encoding="utf-8")

        result = self.run_mem("search", "CLAUDE_SESSION_MARKER", "--sessions-only", "--agent", "claude")
        self.assertIn("[claude/session]", result.stdout)
        self.assertIn("CLAUDE_SESSION_MARKER", result.stdout)
        result = self.run_mem("search", "CODEX_SESSION_MARKER", "--sessions-only", "--agent", "codex")
        self.assertIn("[codex/session]", result.stdout)
        self.assertNotIn("[codex/memory]", result.stdout)

    def test_install_dry_run_apply_and_repeat_preserve_settings(self) -> None:
        codex_rules = self.codex / "AGENTS.md"
        codex_rules.write_text("existing codex rules\n", encoding="utf-8")
        claude_rules = self.claude / "CLAUDE.md"
        claude_rules.write_text("existing claude rules\n", encoding="utf-8")
        settings = self.claude / "settings.json"
        settings.write_text(json.dumps({"theme": "dark", "testSecret": "TEST_SECRET_DO_NOT_USE",
                                        "permissions": {"allow": ["Bash(git status:*)"]}}),
                            encoding="utf-8")
        original = (codex_rules.read_bytes(), claude_rules.read_bytes(), settings.read_bytes())

        preview = self.run_mem("install").stdout
        self.assertNotIn("TEST_SECRET_DO_NOT_USE", preview)
        self.assertEqual(original, (codex_rules.read_bytes(), claude_rules.read_bytes(), settings.read_bytes()))
        self.run_mem("install", "--apply")
        self.run_mem("install", "--apply")
        self.assertEqual(codex_rules.read_text(encoding="utf-8").count("<!-- mem-windows:begin -->"), 1)
        self.assertEqual(claude_rules.read_text(encoding="utf-8").count("<!-- mem-windows:begin -->"), 1)
        data = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "dark")
        self.assertEqual(data["testSecret"], "TEST_SECRET_DO_NOT_USE")
        self.assertIn("Bash(git status:*)", data["permissions"]["allow"])
        self.assertEqual(data["permissions"]["allow"].count("Bash(mem:*)"), 1)

    def test_show_rejects_file_outside_enrolled_sources(self) -> None:
        unrelated = self.root / "unrelated.md"
        unrelated.write_text("NOT_ENROLLED\n", encoding="utf-8")
        result = self.run_mem("show", str(unrelated), success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("NOT_ENROLLED", result.stdout)

    def test_agent_selection_controls_search_and_install(self) -> None:
        self.run_mem("init", "--agents", "claude")
        self.assertNotEqual(self.run_mem("map", "--agent", "codex", success=False).returncode, 0)
        self.run_mem("install", "--apply")
        self.assertTrue((self.claude / "CLAUDE.md").exists())
        self.assertFalse((self.codex / "AGENTS.md").exists())

    def test_invalid_existing_settings_leave_instruction_files_untouched(self) -> None:
        codex_rules = self.codex / "AGENTS.md"
        codex_rules.write_text("original rules\n", encoding="utf-8")
        (self.claude / "settings.json").write_text("{broken json", encoding="utf-8")
        result = self.run_mem("install", "--apply", success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(codex_rules.read_text(encoding="utf-8"), "original rules\n")


if __name__ == "__main__":
    unittest.main()
