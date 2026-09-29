# Changelog

## 1.1.0 · 2026-09-29

- Implicit use: the rule block now lists everyday phrasings ("do you remember…", "go check Codex for…") so agents search memory without being told to, and forbids answering "I can't see previous conversations".
- `--agent name[,name]` for `mem search` and `mem recent`, to search only the agents the owner names.
- Bilingual output: English or Chinese, following the system language. Override with `MEM_LANG=en|zh`.
- The rule block written by `mem install` matches the output language.
- `mem --version`.
- `mem search` gives a clear message when ripgrep is missing.
- `mem map` no longer fails when the Codex index file is absent.
- English and Chinese READMEs, install prompts, and illustrations.
- MIT license.

## 1.0.0 · 2026-09-28

- First release: `init`, `install`, `map`, `search`, `show`, `recent`, `snapshot`.
