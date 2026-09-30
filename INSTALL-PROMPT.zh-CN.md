# 让 AI 帮你安装 mem

Windows 用户请使用 [Windows 原生安装说明](windows/README.zh-CN.md)。下面的提示词使用 macOS/Linux 命令。

把下面两条分隔线之间的整段文字复制下来，发给你常用的任意一个 AI 编码工具：Claude Code、Codex、ZCode、Grok 或其他都可以。

如果你已经下载了 mem-kit，把 `【可选：本地路径】` 换成文件夹的实际位置（把文件夹拖进终端窗口，路径会自动出现）。没下载也没关系，保持原样，AI 会自己从 GitHub 下载。

> English version: [INSTALL-PROMPT.md](INSTALL-PROMPT.md)

---

请帮我安装 mem。本地安装包：【可选：本地路径】。项目地址：https://github.com/wyiky/mem-kit

mem 是一个只读的命令行小工具，用来让我电脑上的几个 AI 编码工具互相检索对方的记忆。请先读一遍项目说明（本地的 `README.zh-CN.md`，或者 https://github.com/wyiky/mem-kit/blob/main/README.zh-CN.md），然后按下面的步骤做。**每到标着「停下」的地方，都先问我、等我回答，不要替我决定。**

**第 1 步：检查环境**
- 运行 `python3 --version`，要求 3.8 或以上。
- 运行 `rg --version`，检查 ripgrep 装没装。
- 两样都有，直接进第 2 步。缺哪样就告诉我缺什么，并给出适合我系统的安装命令。**停下**，等我同意后再装。

**第 2 步：问我要共享哪几个工具**
- **停下**，问我：「这台电脑上有哪几个 AI 工具需要共享记忆？」
- 可以顺带告诉我你在默认位置看到了哪些工具的目录（`~/.claude`、`~/.codex`、`~/.zcode`、`~/.grok`、`~/.config/opencode`），当作参考，但名单由我定。
- 内置认识的名字有 `claude`、`codex`、`zcode`、`grok`、`opencode`。我说的工具不在里面，就问我它的记忆目录在哪里。

**第 3 步：把 mem 放进 PATH**
- 有本地安装包：`mkdir -p ~/bin && install -m 755 【本地路径】/mem ~/bin/mem`
- 没有本地安装包：`mkdir -p ~/bin && curl -fsSL https://raw.githubusercontent.com/wyiky/mem-kit/main/mem -o ~/bin/mem && chmod +x ~/bin/mem`
- 运行 `command -v mem`，确认能找到。
- 如果找不到，说明 `~/bin` 不在 PATH 里，需要在 `~/.zshrc`（macOS）或 `~/.bashrc`（Linux）末尾加一行 `export PATH="$HOME/bin:$PATH"`。**停下**，告诉我要改哪个文件、加哪一行，等我同意后再改。

**第 4 步：登记名单**
- 按我在第 2 步给的名单运行 `mem init --agents 工具1,工具2,...`。名单外的工具用 `--path 名字=记忆目录` 补上。
- 把它列出来的清单原样给我看：每个工具找到了几个文件、多大、在哪个目录。显示「没有记忆目录」的工具不算出错，它只是只读别人的记忆，不贡献自己的。
- **停下**，问我清单对不对。

**第 5 步：预览要改的文件**
- 运行 `mem install`。这一步只是预演，什么都不会改。
- 把输出翻译成大白话告诉我：会动哪些文件，每个文件是新建、追加还是替换；会不会给 Claude Code 或 Grok 加一条命令白名单。
- **停下**，等我说「可以」。

**第 6 步：正式写入**
- 运行 `mem install --apply`。
- 如果输出提示某个文件需要手动处理（例如 Grok 的配置里已经有 `[permission]` 段），把要加的那一行和加的位置告诉我，**停下**，等我同意后再改。

**第 7 步：验收**
- 运行 `mem map`，把各记忆库的现状给我看。
- 从我的记忆里挑一个大概会出现的词，比如某个项目名，运行 `mem search 那个词`，给我看结果，证明确实能跨工具搜到。
- 提醒我：已经开着的 AI 会话要重开一次，才会读到新写入的规则。重开后不用敲任何命令，直接说一句「你还记得我们之前 X 是怎么弄的吗？」或者「你去 Codex 那边找一下 X」，就能验证它会不会自己去查。

**全程遵守：**
- 不要修改、移动或删除任何工具的记忆文件。mem 本身只读，你也一样。
- 不要创建 `~/.config/mem/aliases.tsv`，除非我主动要求。
- 不要运行需要 sudo 的命令，除非我同意。
- 装完用三五句话总结做了什么，并告诉我怎么卸载：删掉各指令文件里 `<!-- mem:begin -->` 到 `<!-- mem:end -->` 之间的内容，删掉加过的 `mem` 白名单，再运行 `rm ~/bin/mem` 和 `rm -r ~/.config/mem`。

---
