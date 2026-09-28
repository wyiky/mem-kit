# mem

**一条命令，搜遍你所有 AI 编码工具的记忆。**

Claude Code、Codex、ZCode、Grok 用久了，各自都会记下你的习惯、踩过的坑、做过的决定。问题是它们互相看不见：在 Codex 里定下的事，换到 Claude 就得重讲一遍。

`mem` 让任何一个工具都能一次搜遍所有工具的记忆。

```
你：上次那个部署回滚是怎么处理的？
AI：（自动运行 mem search 部署 回滚）
    在 Codex 的记忆里找到了：……
```

| 不复制 | 不合并 | 不联网 | 不装服务 |
|:---:|:---:|:---:|:---:|
| 记忆留在原地 | 各工具各管各的 | 全部本地运行 | 只有一个脚本 |

---

## 安装

### 方式一：让 AI 帮你装（推荐）

打开 [`INSTALL-PROMPT.md`](INSTALL-PROMPT.md)，把里面那段话复制给你常用的 AI 编码工具，大约五分钟装好。

AI 会先检查环境，再问你要共享哪几个工具，预览要改的文件，都征得你同意之后才写入。

### 方式二：自己动手

**准备**：macOS 或 Linux，并装有以下两样。

| 依赖 | 检查命令 | 没有的话 |
|---|---|---|
| Python 3.8+ | `python3 --version` | 系统一般自带 |
| ripgrep | `rg --version` | macOS：`brew install ripgrep`<br>Ubuntu/Debian：`sudo apt install ripgrep` |

**① 放进 PATH**

在解压出来的目录里运行：

```bash
mkdir -p ~/bin && install -m 755 mem ~/bin/mem
```

```bash
mem --help
```

如果提示 `command not found`，把下面这行加进 `~/.zshrc`（macOS）或 `~/.bashrc`（Linux），然后重开终端：

```bash
export PATH="$HOME/bin:$PATH"
```

**② 登记要共享的工具**

名单由你来定，mem 不会自己猜。比如你用的是 Claude Code、Codex 和 ZCode：

```bash
mem init --agents claude,codex,zcode
```

它会去这些工具的默认位置找记忆目录，并列出找到了什么。

- 内置认识的名字：`claude` `codex` `zcode` `grok` `opencode`
- 其他工具用 `--path 名字=记忆目录` 指定
- 没有记忆目录的工具也可以加入，它能读别人的记忆，只是自己不贡献

**③ 把使用规则写进各工具**

```bash
mem install
```

```bash
mem install --apply
```

第一条只预览会改哪些文件，第二条才真正写入。写入的内容是：

- 每个工具的全局指令文件里，加一段用 `<!-- mem:begin -->` 和 `<!-- mem:end -->` 包起来的规则。原有内容不动，重复运行只替换这一段，不会叠加。
- Claude Code 和 Grok 各加一条 `mem` 命令白名单，否则每次调用都会弹窗审批。

装完以后，把已经开着的 AI 会话重开一次，新规则才会生效。

---

## 使用

平时不需要你手动跑。规则写进去以后，你问 AI「我以前怎么处理 X 的」，它会自己去搜。

想自己查的时候：

| 命令 | 作用 |
|---|---|
| `mem map` | 看各记忆库现状，数字每次现算 |
| `mem search 部署 回滚` | 一次搜遍所有库，结果按层分组 |
| `mem search 部署 --raw` | 再往下挖一层，看当时的原话（Codex） |
| `mem search 部署 --deep` | 连活动流证据一起搜（Codex） |
| `mem show <路径> --section '标题'` | 只读某一节；大文件默认只给大纲 |
| `mem recent --days 7 [词]` | 最近改过的记忆 |
| `mem snapshot` | 给带 git 的记忆库打快照 |

### 搜索结果怎么看

`mem search` 按从粗到细的顺序，一层一层往下搜：

| 层 | 搜什么 | 什么时候用 |
|---|---|---|
| L0 索引 | 各库的总目录（`MEMORY.md` 等） | 默认 |
| L1 条目 | 每一条具体记忆 | 默认 |
| L2 会话 | Codex 的会话摘要 | 默认，装了 Codex 才有 |
| L3 原始 | Codex 的原始记忆 | 加 `--raw` |
| L4 证据 | Codex 的活动流 | 加 `--deep` |

---

## 中英别名（可选）

有些工具的记忆主要是英文，你用中文搜会漏掉。可以建一个 `~/.config/mem/aliases.tsv`，每行一条，用 Tab 分隔：

```
部署	deploy|发布|上线
数据库	database|db|postgres
```

之后搜「部署」，会自动连 deploy、发布、上线一起搜。

没有这个文件也能正常用。**这个文件是你的私有配置，把 mem 分享给别人时不要带上。**

---

## 常见问题

**会不会改动我的记忆？**
不会。mem 只读。`install` 只改各工具的全局指令文件，而且只动 `mem:begin` 到 `mem:end` 之间那一段。

**AI 还是没去查记忆？**
规则只能提高 AI 主动查的概率，没法保证每次都查。遇到这种情况，直接跟它说「先用 mem 搜一下」。

**搜不到？**
先换个近义词或者英文再搜。如果中文经常漏，就加上面说的别名。两轮都是 0 命中，说明记忆里确实没有。

**配置存在哪？**
`~/.config/mem/config.json`，里面只有名单和目录路径。脚本本身不含任何个人信息。

**能直接改 Codex 的记忆文件吗？**
不要。Codex 会整体重新生成自己的索引文件，你改的内容会丢。

---

## 卸载

1. 删掉各工具指令文件里 `<!-- mem:begin -->` 到 `<!-- mem:end -->` 之间的内容
2. 删掉 Claude Code 或 Grok 配置里的 `mem` 白名单（如果加过）
3. `rm ~/bin/mem`
4. `rm -r ~/.config/mem`

不会碰任何记忆数据。

---

## 限制

- 只做文本匹配，没有相关度排序。
- 规则能提高 AI 主动查记忆的概率，不能保证它每次都查。
- 只支持 macOS 和 Linux。
