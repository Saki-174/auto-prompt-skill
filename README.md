# Auto Prompt Skill

**目标 Agent＋原始需求 → 可直接使用的规范提示词。**

从本地 Auto Prompt 的严格模板迁移而来，面向 **ChatGPT Work 与 Codex**。包含规则型 Skill、离线确定性脚本和可下载整合包。无需 Auto Prompt 后端、Docker、Ollama、MCP Adapter、Tunnel 或 API Key。

[English](README.en.md) · [下载安装包](https://github.com/Saki-174/auto-prompt-skill/releases/latest) · [安装说明](docs/install.md) · [迁移范围](docs/migration.md)

## 另一台电脑快速使用

1. 从 [Releases](https://github.com/Saki-174/auto-prompt-skill/releases/latest) 下载 **`auto-prompt-skill-1.0.0-bundle.zip`**，解压到长期保留的目录。
2. Windows 双击 **`Install-Windows.cmd`**。安装器只复制此包并注册本地目录，保留已有插件配置；更新前自动备份。它会使用电脑上的 Python 或主机提供的内置 Python，无联网下载。
3. 重启 ChatGPT 桌面版／Codex，在 **Plugins／插件**中选择 **Auto Prompt Local** 来源，安装 **Auto Prompt Skill**。若原有个人目录有其他名称，安装器会保留该名称，使用它显示的 `marketplaceName`。
4. 在新对话中输入 `@` 或 `$`，选中 **Auto Prompt**，发送以下需求。

```text
目标 Agent：Codex
原始需求：帮我写一个 Unity 对象池。
额外要求：只允许修改 Assets/Scripts，不要新增依赖。
```

ChatGPT Work 中用 `@` 选择技能；Codex CLI／IDE 用 `$auto-prompt`。桌面客户端的选择器随版本可能不同，以实际显示的技能为准。

**下载 ZIP 只是取得文件，安装后才能作为技能使用。** 把 ZIP 附加到普通聊天不会自动安装技能。ChatGPT Work 本地执行需连接承载安装文件的电脑；未连接的云端任务不自动继承本地安装。没有本地插件安装入口时，可用管理员的导入方式，见 [安装说明](docs/install.md)。

## 两种模式

| 模式 | 工作方式 | 保证范围 |
| --- | --- | --- |
| 严格模式，默认 | Python 标准库拼接旧版四套模板 | 相同 JSON 输入得到相同 UTF-8 输出 |
| 灵活模式 | 当前 ChatGPT／Codex 按 Skill 改写 | 保留意图、约束、缺失信息；措辞与结构可能变化 |

严格模式不翻译或理解原始需求，只固定模板结构；自然语言到字段的抽取仍由模型完成。希望完整复现时直接提供 JSON。旧版语言检测、默认开发 profile 和中英文模板均保留；其他语言及自定义结构使用灵活模式。脚本不可用时技能会明确说明规则生成的限制。

```json
{
  "targetAgent": "ChatGPT Work",
  "rawPrompt": "根据我提供的会议记录整理决定和行动项。",
  "requirements": "用中文；不推测缺失的负责人和截止时间。",
  "profile": "general",
  "strictMode": true
}
```

## 直接运行严格脚本

Python 3.9+，无第三方依赖。在解压目录运行；Windows 也可把 `python` 换成 `py -3` 或主机内置 Python 的路径。

```sh
python skills/auto-prompt/scripts/render_prompt.py --input examples/codex.json
python skills/auto-prompt/scripts/render_prompt.py --input examples/chatgpt.json --format json
python skills/auto-prompt/scripts/render_prompt.py --raw-prompt "整理已提供的材料。" --agent "ChatGPT Work" --profile general
```

脚本只生成提示词，不执行提示词中的任务。输入、长度限制、默认值与兼容字段见 [输入参考](skills/auto-prompt/references/input.md)。

## 包与目录

| 下载文件 | 用途 |
| --- | --- |
| `auto-prompt-skill-1.0.0-bundle.zip` | 完整整合包，包含安装器、说明、Skill、示例、测试和源码 |
| `auto-prompt-skill-1.0.0-plugin.zip` | 纯 Skill 插件包；支持的插件导入／提交入口使用 |
| `auto-prompt-1.0.0-skill.zip` | 单技能文件夹；手动安装到 Codex 的 `.agents/skills` |
| `SHA256SUMS.txt` | ZIP 的 SHA-256 校验值 |

```text
plugin.json                        # 纯 Skill 分发清单，无 MCP
skills/auto-prompt/SKILL.md         # 技能入口
skills/auto-prompt/scripts/         # 离线严格渲染
skills/auto-prompt/templates/       # 中英文 × 开发／通用
scripts/install.py                 # 跨平台安装与备份
scripts/build_release.py           # 可复现 ZIP 构建
examples/                          # 公开示例
tests/                             # 旧版输出与安装／打包验证
```

## 开发与发布

```sh
python -m unittest discover -s tests -v
python scripts/build_release.py
```

CI 在 Windows／Linux 与 Python 3.9／3.12 上执行同一组验证并构建附件。修改版本号 `plugin.json.version` 后重新构建，在 GitHub Release 上传 `dist/` 里的 ZIP 与校验文件。发布整合包时必须执行测试，具体检查见 [验证说明](docs/validation.md)。

安装器不停止或删除旧部署。旧服务停用须单独确认共享依赖；特别是 CYX-MEMORY 不属于此迁移。

## 许可与来源

[ISC License](LICENSE)。严格模板来源于本地 ISC 声明的 `prompt-mcp-adapter`，迁移标注见 [NOTICE](NOTICE)。没有复制原 Auto Prompt 平台源码、数据库、配置凭据、模型或 Tunnel 可执行文件。

兼容性依据：OpenAI [Skill 文档](https://learn.chatgpt.com/docs/build-skills)与[纯 Skill 插件打包文档](https://developers.openai.com/plugins/build/plugins)，核对日期 2026-10-04。GitHub 发布不等于已进入 OpenAI 公共插件目录；公共目录仍需独立审核。
