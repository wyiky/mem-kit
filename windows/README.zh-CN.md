# Windows 原生记忆互查

这里提供适用于 Windows 的 Claude Code ↔ Codex 记忆桥。仓库原有的 `mem` 继续用于 macOS/Linux。Windows 版每次直接读取两边的本机原文件，不复制、不遮盖、不修改记忆。

## 安装

要求：Windows、已加入 PATH 的 Python 3.8+。ripgrep 可选，安装后能加快大型会话日志的检索。

克隆本仓库后，在 PowerShell 中运行：

```powershell
$memBin = Join-Path $HOME 'bin'
New-Item -ItemType Directory -Force -Path $memBin | Out-Null
Copy-Item .\windows\mem.py (Join-Path $memBin 'mem.py')
Copy-Item .\windows\mem.cmd (Join-Path $memBin 'mem.cmd')
Copy-Item .\windows\mem (Join-Path $memBin 'mem')
```

如果 `$memBin` 尚不在用户 PATH 中，先把它加进去并重开终端。PowerShell 使用 `mem.cmd`，Git Bash 使用无扩展名的 `mem`。运行 `mem --version` 验证。

先选定要互查的工具，再预览并写入代理指令与 Claude 命令白名单：

```powershell
mem init --agents claude,codex
mem map
mem install
mem install --apply
```

也可以只选 `claude` 或 `codex`；以后重新运行 `mem init` 即可更改名单。未选中的工具不会被检索。

`install` 会创建或更新 `%USERPROFILE%\.codex\AGENTS.md`、`%USERPROFILE%\.claude\CLAUDE.md` 和 Claude 全局 `settings.json`。已有内容会保留；重复安装只替换 `mem-windows:begin/end` 标记内的指令。完成后重开正在使用的代理会话。如果某个 Claude 启动方式明确跳过用户级设置或指令，需要在该项目的本地说明与本地设置中另加同样的规则和命令许可。

## 使用

```powershell
mem map
mem search "回滚方案"
mem search "回滚方案" --agent codex
mem search "回滚方案" --files-only
mem search "回滚方案" --sessions-only
mem recent --days 7
mem show "C:\搜索结果中的路径\MEMORY.md" --section "标题"
```

搜索不区分大小写，按原文匹配；多个关键词是“命中任意一个”。默认每个来源最多显示 24 行、每个文件最多 2 行，可用 `--max-hits` 和 `--per-file` 调大。`--sessions-only` 只查本机保留的 Claude/Codex JSONL 原始会话；`--deep` 则把原始会话与已保存记忆一起查。

Claude Code 的项目自动记忆和 Codex 的 Markdown 记忆每次运行都会重新发现。要加入任意项目：

```powershell
mem add-project "D:\项目路径"
mem projects
mem search "项目关键词" --agent project --files-only
```

登记的项目会收录 `AGENTS.md`、`CLAUDE.md`、`CLAUDE.local.md`、`MEMORY.md`，以及 `memory`、`memories`、`.memory`、`rules` 目录下的 Markdown 文件。新建符合规则的文件，下次搜索就能看到。`mem remove-project "D:\项目路径"` 只移除登记，不删除文件。工具名单与项目登记都保存在安装目录的 `mem-config.json`。

## 边界

脚本本身不联网，但 AI 代理读取搜索结果后，相关文字会进入当前模型上下文。工具不会过滤已登记记忆或项目文件中的密码。未保存到本机或被原工具清理的会话无法找回。自动检索指令会提高代理主动查找的概率；没有主动调用时，可以明确要求它运行 `mem search`。

卸载时，删除安装目录中的 `mem.py`、`mem.cmd`、无扩展名的 `mem` 和 `mem-config.json`；再删除两份全局指令中的 `mem-windows:begin/end` 块，以及 Claude 设置中的两条 `Bash(mem...)` 白名单。原记忆文件不会被删除。
