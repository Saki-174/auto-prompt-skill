# Auto Prompt Skill · v1.0.1

**目标 Agent＋口语化需求 → 可复制的提示词。** 本版本已通过用户的 ChatGPT 本地 Work 验收。

在 ChatGPT 中使用本技能，为 Codex、ChatGPT、视频生成模型等目标 Agent 整理开发、学习、研究、写作、视频等需求。**运行宿主**执行这个技能；**目标 Agent**接收它生成的提示词，两者可以不同。

[English](README.en.md) · [安装/升级/回滚](docs/install.md) · [ChatGPT 验收清单](docs/chatgpt-acceptance.md) · [发布说明](docs/release-v1.0.1.md)

## 新电脑的一个安装入口

1. 安装并登录支持本地技能的 ChatGPT 桌面客户端，使用连接这台电脑的本地执行环境。宿主安装、登录、授权与最终启用由用户完成。
2. 从 [v1.0.1 Release](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.0.1) 下载并解压整合包 **auto-prompt-skill-1.0.1-bundle.zip**，双击 **Install-Windows.cmd**。
3. 安装器先检查项目专属 Python，再检查兼容的已有解释器。缺少或不兼容时，从 Python 官方下载固定版本 3.13.12 的 Windows x64 嵌入式运行时，验证固定 SHA-256，解压到本项目专属目录；不会更新全局 Python、PATH 或注册表。只有标准库，无 pip/npm/Ollama/Docker 依赖。
4. 按安装器输出，在 ChatGPT 桌面客户端的 Plugins 里选择个人本地来源（通常为 Auto Prompt Local），安装或刷新 Auto Prompt Skill。重启/新建本地聊天后，确认实际加载 v1.0.1。

安装器完成文件安装、项目运行时登记和个人 marketplace 条目更新；**文件安装成功不等于客户端已启用**。如果账号或客户端没有该入口，按实际宿主提供的方式启用，不能把 ZIP 附件视为安装成功。v1.0.1 自动运行时准备限定 Windows x64；其他平台保留 Python 手动安装路径，不宣称已完成所有宿主适配。

首次缺少 Python 需联网下载约 10.4 MB。有兼容解释器或经校验的官方 ZIP 时可离线安装，详见 [依赖方案](docs/v1.0.1-design.md)。

## 日常使用

在 ChatGPT 中选择 Auto Prompt 技能。仅调用技能会出现分步引导；也可以直接给出完整需求：

~~~text
目标 Agent：ChatGPT
想法：我想学习概率，基础一般，希望先用生活例子解释，再给两道自测题。
额外要求：中文，不假设我懂微积分。
~~~

~~~text
目标 Agent：视频生成模型
想法：给咖啡店做一段温暖的宣传短片，重点是雨天室内的舒适感。
先帮我澄清需要的信息，再整理提示词。
~~~

~~~text
目标 Agent：Codex
想法：根据我提供的报错修复解析逻辑，只允许改 parser.py，不增加依赖。
~~~

已有信息会被复用；只追问影响目标、范围、交付或验收的关键歧义。可以说“改成……”“暂不确定”“由你建议”“先出草案”。有结构化提问工具时使用提示框；没有时使用文字提问。具体入口受当前 ChatGPT 环境控制。

## 模式变化与兼容

| 输入 | v1.0.1 行为 |
| --- | --- |
| 日常自然语言，未指定模式 | **灵活模式默认**：当前 ChatGPT 理解并改写 |
| 明确要求严格模式 | 执行固定模板脚本，原样返回 |
| 完整旧 JSON 没有 strictMode | 保留旧协议，按 true |
| JSON strictMode=false | 当前模型灵活改写 |
| 直接运行 render_prompt.py | 继续严格模式、旧参数及原默认值 |

灵活输出因模型和上下文可能变化。严格模式仅保证**固定版本与模板、相同 JSON 输入得到相同 UTF-8 输出**，不承担自动理解、翻译或任意领域优化。自然语言到 JSON 的抽取仍由模型完成。四套旧模板及原严格脚本未更改。

~~~json
{"targetAgent":"ChatGPT","rawPrompt":"根据我提供的会议记录整理决定和行动项。","requirements":"中文；不推测缺失的负责人和截止时间。","profile":"general","strictMode":true}
~~~

Windows 安装后可使用技能目录的 scripts/Run-Strict.ps1；已有 Python 的环境也可直接运行：

~~~sh
python skills/auto-prompt/scripts/render_prompt.py --input examples/chatgpt.json
~~~

默认只生成提示词，不执行其中的业务任务。目标 Agent 的能力、模型参数与授权不能靠名称推断。

## 升级、定制与恢复

旧版到新版使用同一个 Install-Windows.cmd。安装器按旧版文件摘要识别 v1.0.0，并保存可恢复事务备份；原有其他插件、目录名称和条目自定义字段保留。

- 独立的用户文件原样保留。
- SKILL.md、模板等程序文件被本地修改或与新文件冲突时，安装中止并列出路径，供用户明确合并；不自动拼接规则或覆盖定制。
- 重复安装相同内容不会重复登记。
- 中途写入失败自动恢复程序、marketplace 和运行时指针。
- 安装器打印 transaction ID，可用 Install-Windows.ps1 -Rollback <ID> 回滚；若之后有用户编辑则停止，防止覆盖。
- 客户端的插件缓存/启用由宿主管理，回滚来源后仍须刷新并新建聊天核验。

完整 [安装、升级、故障恢复和卸载步骤](docs/install.md)。用户偏好文件保留不等于自动执行其内容；需要在使用时明确提供或引用。

## 开发与验收

~~~sh
python -m unittest discover -s tests -v
python scripts/build_release.py
~~~

运行时集成测试入口：tests/windows_acceptance.ps1。测试与验收边界见 [验证说明](docs/validation.md)。自动测试不能证明 ChatGPT 的技能发现、提示框或真实多轮引导已成功，必须完成 [新对话验收](docs/chatgpt-acceptance.md)。

整合包由公开文件白名单构建；运行时、用户配置、备份和机器日志不进入发布包。正式下载附件及 SHA-256 清单见 [Release](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.0.1)。

## 来源与许可

项目主体 [ISC](LICENSE)。澄清机制局部改编自用户指定的 mattpocock/skills：当前 grill-me 入口调用 grilling；保留了决策依赖和分轮澄清，限制了问题数量，移除了上游技能工具和子代理依赖。固定提交、MIT 许可与改编范围见 [来源说明](skills/auto-prompt/references/grill-me-attribution.md)。

Python 运行时来自 [Python 官方固定版本](https://www.python.org/downloads/release/python-31312/)，保留原压缩包的 LICENSE.txt；整合包本身不捆绑解释器。宿主路径依据 [OpenAI 本地插件文档](https://developers.openai.com/plugins/build/plugins)，技能使用依据 [ChatGPT skills 文档](https://learn.chatgpt.com/docs/build-skills)。本地文件安装不自动同步到网页、移动端或云端环境。
