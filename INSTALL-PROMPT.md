# Install mem by asking your AI

Copy everything between the two lines below and paste it into any AI coding agent you use: Claude Code, Codex, ZCode, Grok, or any other.

If you already downloaded mem-kit, replace `[optional: local path]` with the folder's path (drag the folder into a terminal window to get it). Otherwise leave it as is, and the agent will download mem from GitHub.

> 中文版：[INSTALL-PROMPT.zh-CN.md](INSTALL-PROMPT.zh-CN.md)

---

Please install mem for me. Local copy: [optional: local path]. Project: https://github.com/wyiky/mem-kit

mem is a small read-only command-line tool that lets the AI coding agents on my machine search each other's memory. Read the project README first (the local `README.md`, or https://github.com/wyiky/mem-kit), then follow the steps below. **Wherever a step says STOP, ask me and wait for my answer. Do not decide for me.**

**Step 1: Check the environment**
- Run `python3 --version`. Needs 3.8 or later.
- Run `rg --version` to check for ripgrep.
- If both are present, go to step 2. If something is missing, tell me what and give me the install command for my system. **STOP** and wait for my OK before installing.

**Step 2: Ask which agents to share**
- **STOP** and ask me: "Which AI agents on this machine should share memory?"
- You may mention which agent folders you can see (`~/.claude`, `~/.codex`, `~/.zcode`, `~/.grok`, `~/.config/opencode`) as a hint, but I make the list.
- Built-in names: `claude`, `codex`, `zcode`, `grok`, `opencode`. If I name an agent that isn't built in, ask me where its memory folder is.

**Step 3: Put mem on PATH**
- With a local copy: `mkdir -p ~/bin && install -m 755 [local path]/mem ~/bin/mem`
- Without one: `mkdir -p ~/bin && curl -fsSL https://raw.githubusercontent.com/wyiky/mem-kit/main/mem -o ~/bin/mem && chmod +x ~/bin/mem`
- Run `command -v mem` to confirm it's found.
- If it isn't, `~/bin` is not on PATH. The fix is one line, `export PATH="$HOME/bin:$PATH"`, at the end of `~/.zshrc` (macOS) or `~/.bashrc` (Linux). **STOP**, tell me which file and which line, and wait for my OK.

**Step 4: Register the list**
- Run `mem init --agents agent1,agent2,...` with the list from step 2. Add `--path name=memory_dir` for agents that aren't built in.
- Show me the result as-is: how many files each agent has, how big, and where. An agent with "no memory store" is not an error. It just reads the others.
- **STOP** and ask me whether the list is right.

**Step 5: Preview the changes**
- Run `mem install`. This is a dry run and changes nothing.
- Explain the output in plain words: which files it will touch, whether each one is created, appended to or replaced, and whether it adds an allowlist entry for Claude Code or Grok.
- **STOP** and wait for me to say go.

**Step 6: Write**
- Run `mem install --apply`.
- If the output says a file needs manual editing (for example, Grok's config already has a `[permission]` section), tell me the exact line to add and where. **STOP** and wait for my OK.

**Step 7: Verify**
- Run `mem map` and show me the stores.
- Pick a word that's probably in my memory, such as a project name, run `mem search <that word>`, and show me the result as proof it works across agents.
- Remind me to restart any open agent sessions so they pick up the new rules. After restarting, I can test it without any command, e.g. "Do you remember what we did about X?" or "Go check Codex for X."

**Throughout:**
- Never modify, move or delete any agent's memory files. mem is read-only, and so are you.
- Don't create `~/.config/mem/aliases.tsv` unless I ask.
- Don't run anything with sudo unless I agree.
- When done, summarize what you did in three to five sentences, and tell me how to uninstall: delete the content between `<!-- mem:begin -->` and `<!-- mem:end -->` in each instructions file, remove any `mem` allowlist entries, then `rm ~/bin/mem` and `rm -r ~/.config/mem`.

---
