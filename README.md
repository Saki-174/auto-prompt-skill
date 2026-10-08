# Auto Prompt Skill · v1.1.0

> v1.1.0 安全性修复版：加强文件、安装事务、输入和运行时保护。变更与升级限制见[发布说明](docs/release-v1.1.0.md)。

在 ChatGPT 中，把“目标 Agent＋口语化需求”整理成可复制的提示词。适合希望把想法说清楚，再交给 Codex、ChatGPT、视频生成模型等工具处理的人；支持开发、学习、研究、写作和视频需求。

[桌面整合包](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-bundle.zip) · [网页插件包](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-plugin.zip) · [完整安装教程](docs/install.md) · [English](README.en.md)

## 能做什么

- **整理需求**：保留目标、上下文、约束、交付物和验证标准，不编造缺失事实。
- **分步澄清**：仅调用时提供引导；已有信息直接复用，只追问影响结果的关键问题。
- **修改结果**：支持追加、替换、撤销要求，以及切换新任务。
- **两种模式**：日常默认由当前模型灵活改写；明确选择严格模式时，由离线脚本固定渲染。

技能只生成提示词，不执行提示词里的任务。**运行宿主**是加载技能的 ChatGPT 网页或桌面环境；**目标 Agent**是接收生成结果的工具，两者可以不同。

## 安装：选择你的 ChatGPT 环境

| 使用环境 | 下载文件 | 安装入口 |
| --- | --- | --- |
| Windows 电脑浏览器中的 ChatGPT 网页版 | `auto-prompt-skill-1.1.0-plugin.zip` | 插件页右上角 `＋` → 上传插件 |
| Windows x64 的 ChatGPT 桌面客户端，本地 Work | `auto-prompt-skill-1.1.0-bundle.zip` | 解压 → `Install-Windows.cmd` → 客户端启用 |

下载项与 `SHA256SUMS.txt` 均在 [v1.1.0 发布页](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.0)的 **Assets** 中。详细步骤见[安装教程](docs/install.md)。

### 网页版：上传插件

1. 下载 [plugin.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-plugin.zip)，按[教程核对校验值](docs/install.md#1-下载网页插件包)，保持 ZIP，不解压。
2. 在浏览器打开 ChatGPT，点击左侧“插件”，再点击搜索框右侧的 `＋`，选择“上传插件”，选中刚下载的 ZIP。
3. 看到“导入成功”后点击“查看插件”，在“个人 → 我创建的”找到 **Auto Prompt Skill**；若详情页仍有安装按钮，完成安装。
4. 新建聊天，输入 `@` 并选择 Auto Prompt 插件或其技能，发送 `请调用 Auto Prompt 技能`，按引导提供目标 Agent 和需求。

上传入口受账号和工作区设置影响。网页版是否依赖本机 Windows 安装器或 Python 尚未完成独立验证；严格脚本执行、跨任务隔离及结构化提示框也尚未验证，见[验证边界](docs/validation.md#网页版验证边界)。

### 桌面客户端：本地安装

1. 安装并登录支持本地 Work 和本地插件来源的 ChatGPT **Windows 桌面客户端**。
2. 下载 [bundle.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-bundle.zip)，按[教程核对校验值](docs/install.md#2-下载并核对文件)，解压并双击 `Install-Windows.cmd`。
3. 看到“严格脚本自检：通过”后，刷新或重启桌面客户端，在插件页切换到安装器打印的本地来源（新建来源通常为 **Auto Prompt Local**／`auto-prompt-local`），安装或刷新 **Auto Prompt Skill**。
4. 新建连接本机的 Work 聊天，选择技能并发送 `请调用 Auto Prompt 技能`。详细入口辨认、成功标志和找不到来源的处理见[桌面教程](docs/install.md#二windows-桌面客户端本地安装)。

安装器复用符合[维护策略](docs/security-maintenance.md#运行时维护)的 Python；找不到时下载并校验固定的 Python 3.13.16 Windows x64 运行时，放入项目专属目录。首次运行时下载约 10.9 MB；不修改全局 Python、PATH 或注册表，也不需要 pip、npm、Ollama、Docker 或常驻服务。

安装器自检确认文件和严格启动器可用，客户端启用仍需新聊天验证。本地来源与网页上传是独立安装路径，不会因本地安装而自动出现网页个人条目。账号和客户端必须提供相应入口；其他平台保留[手动兼容路径](docs/install.md#手动兼容路径)，不宣称全部平台已验收。

## 日常使用

可以只调用技能，跟随引导；也可以一次提供完整信息，在 ChatGPT 聊天框发送：

~~~text
请使用 Auto Prompt。
目标 Agent：ChatGPT
需求：我想学习概率，基础一般。先用生活例子解释，再给两道自测题。
约束：用中文，不假设我懂微积分。
~~~

其他任务也用相同方式描述，例如：给 Codex 修复 `parser.py`，只允许改这个文件、不加依赖；或给视频模型制作雨天咖啡店宣传片，先澄清影响交付的关键选择。

生成后可直接说 `追加……`、`把……替换为……`、`撤销刚才修改`。说 `换个任务` 开始新需求，`直接使用` 结束转换。首次灵活输出可附一句可选修改提示；严格输出、后续修订和“只给结果”时省略。

不确定时可以回答 `暂不确定`、`由你建议` 或 `先出草案`。建议与已确认要求分开；有可用结构化输入工具时使用提示框，否则用文字提问。具体工具取决于当前宿主。

## 灵活模式与严格模式

**灵活模式是自然语言对话的默认值**，由当前模型理解和改写，输出会随模型、上下文变化。**严格模式需明确选择**，固定脚本和模板下，相同 JSON 输入得到相同 UTF-8 输出；自然语言抽取成 JSON 的过程不在确定性保证内。

严格模式需要宿主实际执行包内脚本；本地路径已验证，网页版执行尚未验收。它保留原有四套中英文开发／通用模板，不自动理解、翻译任意需求。若明确要求与固定模板或旧语言规则冲突，技能先澄清；直接 CLI 不做语义澄清。未知目标 Agent 的专有格式、参数和授权不能靠名称推断。

兼容行为保持不变：完整旧 JSON 缺省 `strictMode` 仍按 `true`；`strictMode=false` 交由当前模型灵活改写；直接运行严格脚本的旧参数和默认值保留。字段和语言限制见[输入参考](skills/auto-prompt/references/input.md)。

## 升级、恢复与其他安装方式

桌面本地升级使用整合包和同一个安装入口，再刷新客户端插件。这条路径保留独立用户文件；程序文件被修改或与新版路径冲突时，安装器停止并列出问题，不自动覆盖或拼接规则，重复安装不会重复登记。网页个人导入的更新方式和未验证项另见[升级说明](docs/install.md#升级与自定义内容)。

升级到 **v1.1.0** 请重新下载安装包和校验清单；已有解释器不符合补丁策略时，安装器准备项目专属运行时，不升级共享依赖。详见[v1.1.0 发布说明](docs/release-v1.1.0.md)。

历史 **v1.0.2 有同版本修订，版本号不能单独判断是否更新。** 2026-10-05 修订了解释器复用和安装自检；2026-10-07 修订了恢复、并发运行时准备、打包检查和损坏配置错误。详见[发布说明](docs/release-v1.0.2.md)。

离线安装、指定解释器、目录迁移、事务回滚、卸载及手动兼容方式统一见[安装教程](docs/install.md)。其中离线能力指依赖准备与严格脚本；ChatGPT 对话仍由宿主服务提供。独立用户文件被保留不代表其规则会自动应用，使用时需明确提供或引用。

## 开发与验证

开发者在仓库根目录、已有兼容 Python 的终端中运行：

~~~sh
python -m unittest discover -s tests -v
python scripts/build_release.py
~~~

整合包按公开文件白名单构建，不包含运行时、用户配置、备份或机器日志。自动测试、Windows 集成入口及未验证范围见[验证说明](docs/validation.md)；对话引导、提示框和需求质量需另做[真实客户端验收](docs/chatgpt-acceptance.md)。

## 许可与来源

项目主体使用 [ISC 许可证](LICENSE)。需求澄清机制局部改编自 mattpocock/skills 的 grill-me／grilling，保留决策依赖和分轮澄清，限制问题数量，移除上游工具和子代理依赖；固定提交、MIT 许可和改编范围见[来源说明](skills/auto-prompt/references/grill-me-attribution.md)。

可选运行时来自 [Python 官方固定版本](https://www.python.org/downloads/release/python-31316/)，保留原包 `LICENSE.txt`；整合包本身不附带解释器。技能机制参见 [OpenAI skills 文档](https://learn.chatgpt.com/docs/build-skills)。旧服务的迁移范围及共用依赖边界见[迁移说明](docs/migration.md)。
