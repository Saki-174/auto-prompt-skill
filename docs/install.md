# 安装与使用

## ChatGPT Work 与 Codex 桌面版

安装整合包后，选择个人本地插件目录安装。整合包只有 Skill 和模板脚本，**没有 MCP 连接**，因此不需要填写服务 URL 或认证信息。

Windows：双击 `Install-Windows.cmd`，或 PowerShell 运行：

```powershell
.\Install-Windows.ps1 -Mode plugin
```

macOS／Linux：

```sh
python3 scripts/install.py --mode plugin
```

安装位置：

- 插件文件：`~/.codex/plugins/local-auto-prompt-skill/`
- 目录登记：`~/.agents/plugins/marketplace.json`

这里的 `~` 是本机当前用户目录。安装器保持原有目录名称和其他插件，打印实际 `marketplaceName`。它只登记可安装项；重启客户端后在 Plugins 中安装，才能启用。首次安装时目录名为 `Auto Prompt Local`。

安装器需要 Python 3.9+。Windows 包装脚本能使用已存在的主机内置 Python，不下载解释器。无需 Python 的手动安装：复制包中的 `plugin.json`、`LICENSE`、`NOTICE` 和 `skills/` 到上述插件目录，将包中 `.agents/plugins/marketplace.json` 的插件条目合并到个人目录；把 `source.path` 改为 `./.codex/plugins/local-auto-prompt-skill`。个人目录若不存在，创建它；存在时保留其他内容。严格模式执行时仍需要主机可用的 Python。

## GitHub 目录方式

若本机 Codex 支持 `plugin marketplace` 和 `plugin add`，可直接从源码仓库安装：

```sh
codex plugin marketplace add Saki-174/auto-prompt-skill --ref main
codex plugin add auto-prompt-skill@auto-prompt-local
```

无需运行包内安装器。不要同时安装个人本地来源与 GitHub 来源的同名技能，以免选择器出现重复项。CLI 子命令以本机 `codex plugin --help` 为准；不支持时使用上述本地安装流程。

## 单独安装 Codex Skill

```sh
python scripts/install.py --mode skill
```

Windows 也可运行 `Install-Windows.ps1 -Mode skill`。只复制到 `~/.agents/skills/auto-prompt/`，不改插件目录或其他配置。手动方式：解压 `auto-prompt-1.0.0-skill.zip`，把 `auto-prompt` 文件夹放入 `.agents/skills/`。这是单技能安装，不要再安装同一插件版本。

## 远程／云端 Work

本地安装不会把文件自动部署到其他电脑或未连接的云端执行环境。另一台计算机需要在其自身用户目录安装；本地 Work 需要连接该电脑。云端使用时，需通过账号支持的插件导入方式安装该纯 Skill 包，或把 Skill 放入获准的云端工作环境。

工作区管理员有插件导入／提交入口时，可使用 `auto-prompt-skill-1.0.0-plugin.zip`。入口及角色权限由实际账号决定；本项目没有提交到 OpenAI 公共插件目录，也不保证所有账号存在任意 ZIP 的上传入口。

## 更新与恢复

同一内容重装不重复增加目录条目。替换已有技能或插件时保留 `.backup-<UTC时间>` 目录，修改个人 marketplace 前保留对应备份文件。安装器只接受目标名称一致的已有目录；遇到同名插件来自不同路径会报错并保留原配置。

恢复时关闭使用该插件的客户端，把安装器打印的备份复制回相应目录，保留当前版本直到确认恢复成功。插件缓存由客户端管理；恢复来源后重新加载或重装插件。不要恢复整个 `.codex/config.toml` 来回滚本项目。

卸载插件可在 Plugins 中选择 Auto Prompt Skill，或使用本机支持的 `codex plugin remove`；个人源目录条目需单独移除。只移除此项目的条目或技能目录，不删除整个 `.agents` 或 `.codex`。

官方路径依据：[本地技能](https://learn.chatgpt.com/docs/build-skills)、[本地插件目录](https://developers.openai.com/plugins/build/plugins)。
